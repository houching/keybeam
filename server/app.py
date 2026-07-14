# /// script
# dependencies = [
#   "websockets==12.0",
#   "pyautogui==0.9.54",
#   "pynput==1.7.6",
#   "pystray==0.19.5",
#   "pillow==10.4.0",
# ]
# ///

import asyncio
import json
import logging
import sys
import os
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import webbrowser
from PIL import Image, ImageDraw
import pystray

# Setup logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BarcodeBridge")

# Try to load websockets
try:
    import websockets
except ImportError:
    logger.error("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Try loading pyautogui for keyboard emulation, fallback to pynput if pyautogui fails
keyboard_controller = None
use_pyautogui = True

try:
    import pyautogui
    # Disable pyautogui fail-safe delay for faster typing
    pyautogui.PAUSE = 0.005
    logger.info("Successfully loaded pyautogui.")
except Exception as e:
    logger.warning(f"Could not load pyautogui: {e}. Trying pynput fallback...")
    use_pyautogui = False

if not use_pyautogui:
    try:
        from pynput.keyboard import Controller, Key
        keyboard_controller = Controller()
        logger.info("Successfully loaded pynput fallback controller.")
    except Exception as e:
        logger.critical(f"Failed to load both pyautogui and pynput: {e}")
        logger.critical("Please install either dependency to enable typing emulation.")
        sys.exit(1)

def emulate_typing(text: str):
    """Types out the given text followed by an Enter keypress."""
    if use_pyautogui:
        try:
            # Type code with 0.01s interval between keys to mimic physical typing
            pyautogui.write(text, interval=0.01)
            pyautogui.press("enter")
            logger.info(f"Emulated typing: '{text}' + [Enter] via pyautogui")
        except Exception as e:
            logger.error(f"pyautogui typing error: {e}")
    elif keyboard_controller:
        try:
            keyboard_controller.type(text)
            keyboard_controller.press(Key.enter)
            keyboard_controller.release(Key.enter)
            logger.info(f"Emulated typing: '{text}' + [Enter] via pynput")
        except Exception as e:
            logger.error(f"pynput typing error: {e}")

async def handle_client(websocket, path=None):
    """Handles messages from a connected client."""
    client_ip, client_port = websocket.remote_address
    logger.info(f"Client connected: {client_ip}:{client_port}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                code = data.get("code")
                ts = data.get("ts")
                
                # Check for timestamp
                time_str = "N/A"
                if ts:
                    try:
                        time_str = datetime.fromtimestamp(ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    except Exception:
                        pass
                
                logger.info(f"Received scan: '{code}' (Scanned at: {time_str})")
                
                if code:
                    emulate_typing(code)
                else:
                    logger.warning("Received payload with empty code field.")
                    
            except json.JSONDecodeError:
                logger.warning(f"Malformed JSON message received: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_ip}:{client_port}")
    except Exception as e:
        logger.error(f"Unexpected connection error: {e}")

import socket

def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a TCP port is already bound on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def show_error_dialog(title: str, message: str):
    """Displays a native system popup error dialog."""
    try:
        from tkinter import messagebox, Tk
        root = Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror(title, message)
        root.destroy()
    except Exception as e:
        logger.error(f"Failed to display system dialog: {e}")

def start_static_file_server(directory: str, port: int = 5173):
    """Launches a simple HTTP server in a daemon thread to host the client Web App."""
    class CustomHTTPHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
            
        def log_message(self, format, *args):
            # Suppress normal HTTP access logs to keep terminal logs clean
            pass

    try:
        server = HTTPServer(('0.0.0.0', port), CustomHTTPHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Successfully started Web App server at http://localhost:{port}/")
    except Exception as e:
        logger.warning(f"Could not start static HTTP server: {e}")

async def main(ws_port: int = 3000, http_port: int = 5173):
    host = "0.0.0.0"
    
    # Locate client web assets (check local folder or PyInstaller temporary bundle paths)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        dist_dir = os.path.join(base_path, 'client_dist')
    else:
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../client/dist')

    has_client = os.path.exists(dist_dir)

    # Validate Port Conflicts before opening any server
    conflicts = []
    if is_port_in_use(ws_port, host):
        conflicts.append(f"Port {ws_port} (WebSocket server)")
    if has_client and is_port_in_use(http_port, host):
        conflicts.append(f"Port {http_port} (Web App client)")

    if conflicts:
        err_msg = (
            f"KeyBeam is already running or another program is occupying the required ports:\n\n"
            f"- {', '.join(conflicts)}\n\n"
            f"Please close the other instance or program and try running KeyBeam again."
        )
        logger.critical(err_msg)
        show_error_dialog("KeyBeam — Port Conflict", err_msg)
        os._exit(1)

    if has_client:
        logger.info(f"Found compiled client web assets at: {dist_dir}")
        start_static_file_server(dist_dir, port=http_port)
    else:
        logger.info("Compiled client web assets not found. WebSocket server will run standalone.")

    logger.info(f"Starting WebSocket server on ws://{host}:{ws_port}/ws...")
    async with websockets.serve(handle_client, host, ws_port):
        # Serve forever
        await asyncio.Future()

def create_tray_image():
    """Generates a 64x64 neon green circular scanner logo for the system tray."""
    try:
        # If there is a favicon.png or similar, we can try to load it
        # Otherwise, dynamically draw a high-contrast neon scanner logo
        image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        # circular neon scan line
        dc.ellipse([6, 6, 58, 58], outline=(0, 255, 127), width=5)
        # scan laser dot in the center
        dc.ellipse([26, 26, 38, 38], fill=(0, 255, 127))
        return image
    except Exception:
        # Fallback to a solid color 64x64 image
        return Image.new('RGB', (64, 64), color=(0, 255, 127))

def setup_tray(loop, http_port: int = 5173):
    """Initializes and starts the system tray icon on the main thread."""
    def open_browser(icon, item):
        webbrowser.open(f"http://localhost:{http_port}")

    def stop_all(icon, item):
        logger.info("Stopping KeyBeam server via Tray menu...")
        icon.stop()
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception:
            pass
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Open Web Client", open_browser),
        pystray.MenuItem("Exit", stop_all)
    )
    
    icon = pystray.Icon(
        "KeyBeam",
        create_tray_image(),
        "KeyBeam Barcode Bridge",
        menu
    )
    logger.info("System Tray Icon starting...")
    icon.run()

def load_config(config_path: str) -> dict:
    """Loads ports from config.cfg if present, otherwise returns defaults."""
    config = {"ws_port": 3000, "http_port": 5173}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().lower()
                        v = v.strip()
                        if k in ("ws_port", "http_port"):
                            config[k] = int(v)
            logger.info(f"Loaded config from {config_path}: ws={config['ws_port']}, http={config['http_port']}")
        except Exception as e:
            logger.warning(f"Error reading config: {e}")
    return config

def save_config(config_path: str, ws_port: int, http_port: int):
    """Saves ports to config.cfg."""
    try:
        with open(config_path, "w") as f:
            f.write(f"ws_port={ws_port}\n")
            f.write(f"http_port={http_port}\n")
        logger.info(f"Saved config to {config_path}")
    except Exception as e:
        logger.error(f"Error writing config: {e}")

def prompt_ports_gui(default_ws: int, default_http: int) -> dict:
    """Shows a Tkinter dialog on the main thread to configure ports."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        result = {"ws_port": default_ws, "http_port": default_http, "cancelled": False}
        
        root = tk.Tk()
        root.title("KeyBeam Configuration")
        root.geometry("320x180")
        root.resizable(False, False)
        
        # Center window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"+{x}+{y}")
        
        frame = tk.Frame(root, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="WebSocket Port:").grid(row=0, column=0, sticky="w", pady=5)
        ws_entry = tk.Entry(frame, width=15)
        ws_entry.insert(0, str(default_ws))
        ws_entry.grid(row=0, column=1, pady=5, padx=5)
        
        tk.Label(frame, text="Web App Port:").grid(row=1, column=0, sticky="w", pady=5)
        http_entry = tk.Entry(frame, width=15)
        http_entry.insert(0, str(default_http))
        http_entry.grid(row=1, column=1, pady=5, padx=5)
        
        def on_submit():
            try:
                ws_val = int(ws_entry.get().strip())
                http_val = int(http_entry.get().strip())
                if ws_val <= 0 or http_val <= 0 or ws_val > 65535 or http_val > 65535:
                    raise ValueError("Port must be between 1 and 65535.")
                result["ws_port"] = ws_val
                result["http_port"] = http_val
                root.destroy()
            except ValueError as ex:
                messagebox.showerror("Invalid Input", f"Please enter valid port numbers:\n{ex}")
                
        def on_cancel():
            result["cancelled"] = True
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_cancel)
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        submit_btn = tk.Button(btn_frame, text="Start Server", command=on_submit, width=12)
        submit_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        root.mainloop()
        return result
    except Exception as e:
        logger.error(f"Failed to show GUI dialog: {e}")
        return {"ws_port": default_ws, "http_port": default_http, "cancelled": False}

if __name__ == "__main__":
    import argparse

    # Parse arguments
    parser = argparse.ArgumentParser(description="KeyBeam Barcode Bridge Server")
    parser.add_argument("--ws-port", type=int, default=None, help="Port for the WebSocket server")
    parser.add_argument("--http-port", type=int, default=None, help="Port for the Web App HTTP server")
    parser.add_argument("--interactive", action="store_true", help="Prompt for custom ports interactively in CLI")
    args = parser.parse_args()

    # Determine config file path (in the same directory as script or packaged .exe)
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, "config.cfg")

    # Load configuration
    config = load_config(config_path)
    ws_port = config["ws_port"]
    http_port = config["http_port"]

    # CLI arguments override config
    if args.ws_port is not None:
        ws_port = args.ws_port
    if args.http_port is not None:
        http_port = args.http_port

    # If running interactively via CLI flag/stdin, ask in console; otherwise prompt with GUI on startup if no CLI args are given
    has_cli_ports = (args.ws_port is not None or args.http_port is not None)
    
    if not has_cli_ports:
        if args.interactive or (sys.stdin is not None and sys.stdin.isatty()):
            # CLI Interactive prompt
            try:
                if sys.stdout is not None:
                    sys.stdout.write("Would you like to configure custom ports? (y/N): ")
                    sys.stdout.flush()
                choice = input().strip().lower()
                if choice in ('y', 'yes'):
                    ws_input = input(f"Enter WebSocket Port [{ws_port}]: ").strip()
                    if ws_input:
                        ws_port = int(ws_input)
                    http_input = input(f"Enter Web App HTTP Port [{http_port}]: ").strip()
                    if http_input:
                        http_port = int(http_input)
                    save_config(config_path, ws_port, http_port)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Configuration cancelled by user.")
                sys.exit(0)
            except Exception as e:
                logger.warning(f"Error during interactive port configuration: {e}. Using defaults.")
        else:
            # GUI Interactive Prompt
            gui_result = prompt_ports_gui(ws_port, http_port)
            if gui_result["cancelled"]:
                logger.info("Configuration cancelled via GUI. Exiting.")
                sys.exit(0)
            ws_port = gui_result["ws_port"]
            http_port = gui_result["http_port"]
            save_config(config_path, ws_port, http_port)

    try:
        # Initialize event loop
        loop = asyncio.new_event_loop()
        
        # Start event loop in a background daemon thread
        async_thread = threading.Thread(
            target=lambda: loop.run_until_complete(main(ws_port, http_port)), 
            daemon=True
        )
        async_thread.start()
        
        # Start pystray system tray on the main thread (blocking)
        setup_tray(loop, http_port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user request.")
    except Exception as e:
        logger.critical(f"Server crashed: {e}")
