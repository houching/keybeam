# /// script
# dependencies = [
#   "websockets==12.0",
#   "pyautogui==0.9.54",
#   "pynput==1.7.6",
# ]
# ///

import asyncio
import json
import logging
import sys
from datetime import datetime

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

async def handle_client(websocket, path):
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

async def main():
    port = 3000
    host = "0.0.0.0"
    logger.info(f"Starting WebSocket server on ws://{host}:{port}/ws...")
    async with websockets.serve(handle_client, host, port):
        # Serve forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user request.")
    except Exception as e:
        logger.critical(f"Server crashed: {e}")
