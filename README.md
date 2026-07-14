# Khmer Barcode Bridge (Web Client ⇆ Windows Keyboard Emulator)

A 2-part utility designed to turn your mobile phone's camera into a physical barcode scanner for your Windows PC, transmitting barcodes over a local network (LAN) and emulating them as hardware keystrokes.

---

## 🚀 Quick Start Guide

### 1. Server Setup (Windows Host)

The Python server runs on your Windows computer, listens for incoming barcode payloads, and types them into whatever window currently has focus (e.g. Notepad, Excel, or your web POS).

1. Ensure Python 3.8+ is installed on your Windows machine.
2. Open PowerShell/CMD and navigate to the `/server` folder:
   ```bash
   cd server
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python app.py
   ```

#### 🔍 Finding your Windows LAN IP Address
Since the client phone needs to connect to the computer, you need to know the computer's LAN IP address:
1. Open PowerShell/CMD and run:
   ```powershell
   ipconfig
   ```
2. Look for the **IPv4 Address** under your active connection (usually under `Wireless LAN adapter Wi-Fi` or `Ethernet adapter`).
3. It will look like `192.168.x.x` or `10.0.x.x`. Keep this IP handy!

---

### 2. Client Setup (Mobile Device)

The client is a mobile-friendly Vue 3 + Vite application that accesses your camera, scans barcodes in real-time, and sends them to the server.

1. Open PowerShell/CMD and navigate to the `/client` folder:
   ```bash
   cd client
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server in host mode:
   ```bash
   npm run dev
   ```
4. The server will output a Local URL and a Network URL, e.g.:
   - Local: `https://localhost:5173/`
   - Network: `https://192.168.1.100:5173/`

#### 📱 Opening Client on your Phone
1. Connect your mobile phone to the **same Wi-Fi network** as your Windows PC.
2. Open your mobile browser (Chrome/Edge on Android, Safari on iOS) and navigate to the **Network URL** shown in the terminal (e.g. `https://192.168.1.100:5173/`).
   - *Note: Vite runs with HTTPS self-signed certificates so that the browser allows camera API access (`getUserMedia`). You might need to bypass the security warning in your mobile browser by tapping "Advanced" -> "Proceed anyway".*
3. Once loaded, allow camera permissions when prompted.
4. Input the Windows LAN IP in the server connection field and click **Connect**.
5. Once status turns **Connected**, aim your camera at a barcode. It will instantly type it into the focused window on your Windows PC!

---

## 🛠️ Key Configurations & Settings
- **Language**: Supports English and Khmer translation toggling.
- **Beep & Vibrate**: Configurable in the preferences section.
- **Debounce Delay**: Delay to prevent duplicate scans (default is 1500ms).
- **Decoder Fallback**: Utilizes `BarcodeDetector` Web API natively for hardware-level decoding, falling back to WebAssembly-based `zxing-wasm` if unsupported.
