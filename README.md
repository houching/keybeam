# KeyBeam (Web Client ⇆ Windows Keyboard Emulator) ⚡️👾

![Build Status](https://github.com/houching/barcode-scanner/actions/workflows/build.yml/badge.svg)

A 2-part wireless network utility designed to turn your mobile phone's camera into a physical barcode scanner. It transmits barcode scans over the local network (LAN) to a lightweight server running on your Windows PC, which instantly types them at your cursor as hardware keyboard inputs.

---

## ✨ Features & Highlights

- **⌨️ Keyboard Emulation**: Uses Python (`pyautogui`/`pynput`) to automatically type scanned barcodes into any active program (Notepad, Excel, POS, web form) and triggers a virtual `[Enter]` keystroke.
- **📱 Premium Retro/Hacker Vibe**: Designed with a custom Cyberpunk Retro-Terminal pixel style using `VT323` and `Share Tech Mono` fonts. Includes sound feedback, haptic vibrations, and a green laser sweep animation.
- **🌗 Custom Theme Switcher**: Persistently toggle between **Cyber Dark**, **Arcade Light**, and **Match System** themes.
- **👁️ Zen Mode**: An icon-only toggle to hide headers, configurations, preferences, and history lists, leaving only the camera viewport and the neon scan readout active.
- **📦 Progressive Web App (PWA)**: Installable as a standalone app on iOS/Android with offline capability using a **Stale-While-Revalidate** Service Worker.
- **🛡️ Anti-Ghost Scan (Consecutive Frame Verification)**: Prevents garbled reads by requiring a barcode value to match identically across 2 consecutive camera frames. Toggable under settings.
- **⚡ Dual-Decoder Pipeline**: Automatically runs native browser `BarcodeDetector` when available for maximum speed/battery efficiency, falling back to WebAssembly `zxing-wasm` dynamically when unsupported.
- **🌐 Dual Language**: Built-in support for **English** and **Khmer (ខ្មែរ)**.
- **🔒 Secure Proxy Ready**: Automatically resolves secure WebSocket (`wss://`) protocol paths under secure origins (like `https://keybeam.yourdomain.com/`) to prevent Mixed Content blocking.

---

## 🚀 Server Setup (Windows Host)

The Python server runs on your Windows computer, listens for incoming barcode payloads, and types them into whatever window currently has focus.

1. Ensure you have `uv` installed on your Windows machine.
2. Open PowerShell/CMD and navigate to the `/server` folder:
   ```bash
   cd server
   ```
3. Run the server using `uv`:
   ```bash
   uv run app.py
   ```

#### 🔍 Finding your Windows LAN IP Address
1. Run `ipconfig` in PowerShell/CMD.
2. Look for the **IPv4 Address** under your active adapter (usually `Wireless LAN adapter Wi-Fi` or `Ethernet adapter`).
3. Keep this IP handy (e.g. `192.168.1.100`).

---

## 📱 Client Setup (Mobile Device)

The client is a mobile-friendly Vue 3 + Vite application.

1. Open PowerShell/CMD and navigate to the `/client` folder:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the network address shown (e.g. `http://192.168.1.100:5173/`).

#### 🔒 Resolving HTTPS & Mixed Content Blocks
Mobile browsers require a **secure context (HTTPS)** to access device cameras. If you access the client via an HTTPS reverse proxy (like `https://keybeam.yourdomain.com/`), the browser blocks insecure WebSockets (`ws://`).

Configure your HTTPS proxy to route `/ws` path requests straight to your local PC WebSocket port `3000`:

##### Nginx Configuration:
```nginx
location /ws {
    proxy_pass http://192.168.1.100:3000/ws;  # Replace with Windows PC IP
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
}
```

##### Caddy Configuration:
```caddy
keybeam.yourdomain.com {
    reverse_proxy /ws* 192.168.1.100:3000
    reverse_proxy * localhost:5173
}
```

##### 📲 Connecting Client to Server:
1. Open the secure address on your phone (e.g. `https://keybeam.yourdomain.com/`).
2. Accept camera permissions.
3. In the host input field, simply enter your proxy domain name (e.g. **`keybeam.yourdomain.com`**) or local IP, then click **Connect**.
4. The client will connect to `wss://keybeam.yourdomain.com/ws` securely and start scanning!

---

## 🛠️ Preference Settings & Controls
- **Beep on Scan**: Optional sound signal when barcode is decoded.
- **Vibrate on Scan**: Optional haptic feedback.
- **Laser Scan Line**: Toggle the visual animated scanning sweep line.
- **Debounce Delay**: Adjustable range slider (500ms - 5000ms) to throttle duplicate scans.
- **Anti-Ghost Scan**: Checkbox to require matching values across 2 consecutive frames.
- **History List**: Collapsable (collapsed by default) scan history list with clipboard copy support.

---

## 📦 Single Standalone Binary Compilation

You can compile both the Vue Web Client and the Python Server into a **single, standalone `.exe` binary** for easy distribution. When the compiled binary runs, it hosts the client web application (on port `5173`) and operates the WebSocket bridge (on port `3000`) simultaneously with **zero external dependencies**.

### Build Instructions:

1. **Build the Client Web Assets**:
   ```bash
   cd client
   npm run build
   ```
   *This compiles the Vue app into static assets inside `/client/dist`.*

2. **Compile to Standalone windowless `.exe`**:
   Compile the Python server using `uv run`, embedding the client web assets, attaching the custom icon, embedding version metadata, and compiling without a CMD prompt window (`--noconsole`):
   ```bash
   cd ../server
   # Generate icon.ico and version_info.txt assets
   uv run --with pillow generate_ico.py
   uv run create_version_info.py

   # Compile KeyBeam.exe
   uv run --with pyinstaller --with pystray --with pillow --with websockets --with pyautogui --with pynput python -m PyInstaller --onefile --noconsole --name KeyBeam --icon=icon.ico --version-file=version_info.txt --add-data "../client/dist;client_dist" app.py
   ```

3. **Run the Binary**:
   - The compiled standalone executable will be saved in `server/dist/KeyBeam.exe`.
   - Double-clicking `KeyBeam.exe` launches the complete **KeyBeam** ecosystem in the background (no console window will appear).
   - A neon green scanner icon will appear in your **Windows System Tray** (near the clock).
   - **Right-click the System Tray Icon** to:
     - **Open Web Client**: Launches `http://localhost:5173/` in your default browser.
     - **Exit**: Cleanly terminates the background HTTP and WebSocket servers.

