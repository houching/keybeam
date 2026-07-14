<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

// i18n localization dictionary (easy translation support)
const i18n = {
  en: {
    title: 'KeyBeam',
    subtitle: 'Wireless Barcode Keyboard Bridge',
    serverIp: 'Server IP / Host',
    wsPort: 'Port',
    connect: 'Connect',
    disconnect: 'Disconnect',
    statusConnected: 'Connected',
    statusDisconnected: 'Disconnected',
    statusConnecting: 'Connecting...',
    lastScanned: 'Last Scanned Barcode',
    noScans: 'No barcodes scanned yet.',
    history: 'Scan History',
    clearHistory: 'Clear',
    copy: 'Copy',
    copied: 'Copied!',
    cameraAccess: 'Camera Access',
    cameraActive: 'Camera is active',
    cameraStarting: 'Initializing camera...',
    cameraStopped: 'Camera is turned off.',
    cameraErr: 'Camera error or permission denied.',
    selectCamera: 'Select Camera',
    nativeDecoder: 'Native Decoder',
    fallbackDecoder: 'WASM Decoder',
    settings: 'Preferences',
    beepLabel: 'Beep on Scan',
    vibrateLabel: 'Vibrate on Scan',
    debounceLabel: 'Debounce Delay (ms)',
    doubleVerifyLabel: 'Anti-Ghost Scan (require 2 reads)',
    themeLabel: 'Interface Theme',
    themeLight: 'Arcade Light',
    themeDark: 'Cyber Dark',
    themeSystem: 'Match System',
    laserLabel: 'Laser Scan Line',
    zenNormal: 'Normal Mode',
    zenActive: 'Zen Mode',
  },
  kh: {
    title: 'KeyBeam',
    subtitle: 'ស្កេនបាកូដបញ្ជូនទៅកុំព្យូទ័រឥតខ្សែ',
    serverIp: 'អាសយដ្ឋាន IP ម៉ាស៊ីនបម្រើ',
    wsPort: 'ច្រក',
    connect: 'ភ្ជាប់',
    disconnect: 'ផ្ដាច់',
    statusConnected: 'បានភ្ជាប់',
    statusDisconnected: 'មិនទាន់ភ្ជាប់',
    statusConnecting: 'កំពុងភ្ជាប់...',
    lastScanned: 'បាកូដស្កេនចុងក្រោយ',
    noScans: 'មិនទាន់មានការស្កេននៅឡើយទេ។',
    history: 'ប្រវត្តិនៃការស្កេន',
    clearHistory: 'សម្អាត',
    copy: 'ចម្លង',
    copied: 'បានចម្លង!',
    cameraAccess: 'ការអនុញ្ញាតកាមេរ៉ា',
    cameraActive: 'កាមេរ៉ាកំពុងដំណើរការ',
    cameraStarting: 'កំពុងចាប់ផ្ដើមកាមេរ៉ា...',
    cameraStopped: 'កាមេរ៉ាត្រូវបានបិទ។',
    cameraErr: 'កំហុសកាមេរ៉ា ឬមិនអនុញ្ញាត។',
    selectCamera: 'ជ្រើសរើសកាមេរ៉ា',
    nativeDecoder: 'កម្មវិធីស្កេនផ្ទាល់ (Native)',
    fallbackDecoder: 'កម្មវិធីស្កេនបន្ថែម (WASM)',
    settings: 'ការកំណត់',
    beepLabel: 'បន្លឺសំឡេងពេលស្កេន',
    vibrateLabel: 'ញ័រទូរស័ព្ទពេលស្កេន',
    debounceLabel: 'រយៈពេលផ្អាកស្កេនស្ទួន (ms)',
    doubleVerifyLabel: 'ការពារស្កេនខុស (ត្រូវការស្កេន ២ដង)',
    themeLabel: 'រូបរាង / ប្រធានបទ',
    themeLight: 'ពន្លឺបែបហ្គេម',
    themeDark: 'ងងឹតបែបបច្ចេកវិទ្យា',
    themeSystem: 'តាមប្រព័ន្ធទូរស័ព្ទ',
    laserLabel: 'បង្ហាញខ្សែឡាស៊ែរស្កេន',
    zenNormal: 'របៀបធម្មតា',
    zenActive: 'របៀបស្ងប់ស្ងាត់ (Zen)',
  }
};

const currentLang = ref('en'); // Default to English

const t = (key) => {
  return i18n[currentLang.value][key] || i18n['en'][key] || key;
};

// State Variables
const serverIp = ref('');
const serverWsPort = ref('3000');
const wsStatus = ref('disconnected'); // 'disconnected' | 'connecting' | 'connected'
const lastCode = ref('');
const historyList = ref([]);
const videoElement = ref(null);
const cameraDevices = ref([]);
const selectedDeviceId = ref('');
const cameraStatus = ref('stopped'); // 'stopped' | 'starting' | 'running' | 'error'
const decoderType = ref('detecting'); // 'detecting' | 'native' | 'wasm'

// Settings Options
const beepOnScan = ref(true);
const vibrateOnScan = ref(true);
const debounceDelay = ref(1500); // 1.5s debounce default
const requireDoubleVerification = ref(true); // verify code in 2 consecutive frames to prevent ghost/garbled scans
const theme = ref(localStorage.getItem('kb_theme') || 'dark'); // 'dark' | 'light' | 'system'
const showLaserLine = ref(localStorage.getItem('kb_show_laser') !== 'false'); // true by default
const isZenMode = ref(false);
const isPaused = ref(false);

// Watch theme to update body class and localStorage
watch(theme, (newTheme) => {
  localStorage.setItem('kb_theme', newTheme);
  document.body.className = `theme-${newTheme}`;
}, { immediate: true });

// Watch laser toggle for persistence
watch(showLaserLine, (val) => {
  localStorage.setItem('kb_show_laser', val ? 'true' : 'false');
});

// Scanned history tracking
const lastScanTime = ref(0);
const copiedIndex = ref(null);
const lastScanCandidate = ref('');
const scanCandidateCount = ref(0);

let ws = null;
let reconnectTimeout = null;
let stream = null;
let animationFrameId = null;
let barcodeDetector = null;
let zxingReaderModule = null; // Lazy-loaded module helper

// Load initial query params and local storage
onMounted(() => {
  // Fetch and inject SVG sprite dynamically to bypass browser/proxy rendering bugs
  fetch('/icons.svg')
    .then(r => r.text())
    .then(svgText => {
      const container = document.createElement('div');
      container.style.display = 'none';
      container.innerHTML = svgText;
      document.body.insertBefore(container, document.body.firstChild);
    })
    .catch(err => console.error('Failed to load icons sprite sheet:', err));

  // Try to read settings from localStorage
  const savedIp = localStorage.getItem('kb_server_ip');
  const savedWsPort = localStorage.getItem('kb_server_ws_port');
  const savedLang = localStorage.getItem('kb_lang');
  
  if (savedLang) currentLang.value = savedLang;
  
  // URL Param priority
  const urlParams = new URLSearchParams(window.location.search);
  const paramIp = urlParams.get('server');
  const paramWsPort = urlParams.get('ws_port');
  
  if (paramIp) {
    serverIp.value = paramIp;
  } else if (savedIp) {
    serverIp.value = savedIp;
  } else {
    // Dynamic host fallback depending on what address the client accessed
    serverIp.value = window.location.hostname || 'localhost';
  }

  if (paramWsPort) {
    serverWsPort.value = paramWsPort;
  } else if (savedWsPort) {
    serverWsPort.value = savedWsPort;
  } else {
    serverWsPort.value = '3000';
  }

  // Detect decoder support
  detectDecoderSupport();

  // Initialize camera scan list
  initCameraList().then(() => {
    startCamera();
  });
});

onUnmounted(() => {
  stopCamera();
  disconnectWS();
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
});

// Watch lang to persist
watch(currentLang, (newVal) => {
  localStorage.setItem('kb_lang', newVal);
});

// WebSocket Connection Logic
const connectWS = () => {
  if (!serverIp.value) return;
  
  disconnectWS();
  wsStatus.value = 'connecting';
  localStorage.setItem('kb_server_ip', serverIp.value);
  localStorage.setItem('kb_server_ws_port', serverWsPort.value);

  // Parse websocket target dynamically based on current page protocol
  const isSecure = window.location.protocol === 'https:';
  const protocol = isSecure ? 'wss:' : 'ws:';
  const host = serverIp.value.trim();
  
  let targetUrl = '';
  if (host.startsWith('ws://') || host.startsWith('wss://')) {
    targetUrl = host;
  } else {
    // If accessing via domain proxy, connect directly on the hostname without port
    if (host === window.location.hostname || host === window.location.host) {
      targetUrl = `${protocol}//${host}/ws`;
    } else {
      const portToUse = serverWsPort.value ? serverWsPort.value.trim() : '3000';
      targetUrl = `${protocol}//${host}:${portToUse}/ws`;
    }
  }

  try {
    ws = new WebSocket(targetUrl);
    
    ws.onopen = () => {
      wsStatus.value = 'connected';
      console.log('WebSocket connected to', targetUrl);
    };

    ws.onclose = () => {
      wsStatus.value = 'disconnected';
      // Automatically attempt reconnection
      if (wsStatus.value !== 'disconnected') {
        reconnectTimeout = setTimeout(connectWS, 3000);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      wsStatus.value = 'disconnected';
    };
  } catch (error) {
    console.error('WebSocket setup error:', error);
    wsStatus.value = 'disconnected';
  }
};

const disconnectWS = () => {
  if (ws) {
    ws.close();
    ws = null;
  }
  wsStatus.value = 'disconnected';
  if (reconnectTimeout) clearTimeout(reconnectTimeout);
};

// Decoder Support Detection
const detectDecoderSupport = async () => {
  if ('BarcodeDetector' in window) {
    try {
      // Check if it supports at least common formats
      const formats = await BarcodeDetector.getSupportedFormats();
      if (formats && formats.length > 0) {
        barcodeDetector = new BarcodeDetector({ formats: ['code_128', 'ean_13', 'qr_code', 'code_39', 'upc_a'] });
        decoderType.value = 'native';
        console.log('Using native BarcodeDetector API');
        return;
      }
    } catch (e) {
      console.warn('BarcodeDetector initialization error:', e);
    }
  }

  // Fallback to ZXing WebAssembly
  decoderType.value = 'wasm';
  console.log('Loading zxing-wasm lazy-loaded decoder module...');
  try {
    // Dynamic import to keep initial bundle size smaller
    const zxing = await import('zxing-wasm');
    zxingReaderModule = zxing;
    console.log('zxing-wasm initialized successfully');
  } catch (err) {
    console.error('Failed to load WASM decoder:', err);
  }
};

// Camera Control Logic
const initCameraList = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter(device => device.kind === 'videoinput');
    cameraDevices.value = cameras;
    
    if (cameras.length > 0) {
      // Try to find environment/back camera by default
      const backCam = cameras.find(c => c.label.toLowerCase().includes('back') || c.label.toLowerCase().includes('environment'));
      selectedDeviceId.value = backCam ? backCam.deviceId : cameras[cameras.length - 1].deviceId;
    }
  } catch (e) {
    console.error('Error listing camera devices:', e);
  }
};

const startCamera = async () => {
  stopCamera();
  cameraStatus.value = 'starting';

  const constraints = {
    video: {
      deviceId: selectedDeviceId.value ? { exact: selectedDeviceId.value } : undefined,
      facingMode: selectedDeviceId.value ? undefined : 'environment',
      width: { ideal: 1280 },
      height: { ideal: 720 }
    }
  };

  try {
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    if (videoElement.value) {
      videoElement.value.srcObject = stream;
      cameraStatus.value = 'running';
      // Trigger requestAnimationFrame scan loop
      animationFrameId = requestAnimationFrame(scanFrameLoop);
    }
  } catch (err) {
    console.error('Error starting camera stream:', err);
    cameraStatus.value = 'error';
  }
};

const stopCamera = () => {
  isPaused.value = false;
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  cameraStatus.value = 'stopped';
};

const togglePause = () => {
  if (!videoElement.value) return;
  isPaused.value = !isPaused.value;
  if (isPaused.value) {
    videoElement.value.pause();
  } else {
    videoElement.value.play().catch(e => console.error('Error playing video:', e));
  }
};

// Audio feedback helper
const playBeep = () => {
  if (!beepOnScan.value) return;
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(1000, audioCtx.currentTime); // 1000Hz frequency
    gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
    
    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.1); // 100ms duration
  } catch (e) {
    console.warn('Audio play failed:', e);
  }
};

// Vibration helper
const triggerVibration = () => {
  if (vibrateOnScan.value && navigator.vibrate) {
    navigator.vibrate(80); // Vibrate for 80ms
  }
};

// Verify scans across consecutive frames to prevent misreads
const processScanCandidate = (codeValue) => {
  if (!requireDoubleVerification.value) {
    handleBarcodeFound(codeValue);
    return;
  }
  
  if (codeValue === lastScanCandidate.value) {
    scanCandidateCount.value++;
    if (scanCandidateCount.value >= 2) {
      handleBarcodeFound(codeValue);
    }
  } else {
    lastScanCandidate.value = codeValue;
    scanCandidateCount.value = 1;
  }
};

// Process scanned value
const handleBarcodeFound = (codeValue) => {
  const now = Date.now();
  
  // Debounce duplicate scans
  if (codeValue === lastCode.value && (now - lastScanTime.value) < debounceDelay.value) {
    return;
  }
  
  lastCode.value = codeValue;
  lastScanTime.value = now;
  
  // Feedback
  playBeep();
  triggerVibration();
  
  // Add to history
  historyList.value.unshift({
    code: codeValue,
    time: new Date().toLocaleTimeString()
  });
  if (historyList.value.length > 20) historyList.value.pop();

  // Send to server
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      code: codeValue,
      ts: now
    }));
  }
};

// Processing Loop
const scanFrameLoop = async () => {
  if (cameraStatus.value !== 'running' || !videoElement.value || isPaused.value) {
    animationFrameId = requestAnimationFrame(scanFrameLoop);
    return;
  }

  // Ensure video metadata and dimensions are loaded
  if (videoElement.value.readyState === videoElement.value.HAVE_ENOUGH_DATA) {
    try {
      let decodedValue = null;

      if (decoderType.value === 'native' && barcodeDetector) {
        const barcodes = await barcodeDetector.detect(videoElement.value);
        if (barcodes && barcodes.length > 0) {
          decodedValue = barcodes[0].rawValue;
        }
      } else if (decoderType.value === 'wasm' && zxingReaderModule) {
        // Render current video frame to an offscreen canvas
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.value.videoWidth;
        canvas.height = videoElement.value.videoHeight;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height);
          // Extract Image Data
          const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          
          // Use zxing-wasm to read barcodes from imageData
          const results = await zxingReaderModule.readBarcodesFromImageData(imgData);
          if (results && results.length > 0) {
            decodedValue = results[0].text;
          }
        }
      }

      if (decodedValue) {
        processScanCandidate(decodedValue);
      } else {
        // Reset validation counter if no code is detected in this frame
        scanCandidateCount.value = 0;
        lastScanCandidate.value = '';
      }
    } catch (err) {
      // Avoid spamming error console logs on every single frame loop
    }
  }

  animationFrameId = requestAnimationFrame(scanFrameLoop);
};

// Clipboard Action
const copyToClipboard = (text, index) => {
  navigator.clipboard.writeText(text).then(() => {
    copiedIndex.value = index;
    setTimeout(() => {
      copiedIndex.value = null;
    }, 2000);
  });
};

const clearHistory = () => {
  historyList.value = [];
  lastCode.value = '';
};
</script>

<template>
  <div class="app-container">
    <!-- Header Interface with Language Selection -->
    <header class="glass-panel" style="padding: 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h1 style="font-size: 1.3rem; font-weight: 700; background: linear-gradient(135deg, #818cf8, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          {{ t('title') }}
        </h1>
        <p v-if="!isZenMode" style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px;">
          {{ t('subtitle') }}
        </p>
      </div>
      
      <div style="display: flex; gap: 8px;">
        <!-- Zen Mode Button -->
        <button class="btn-secondary" style="min-height: 36px; min-width: 36px; padding: 6px; font-size: 13px;" @click="isZenMode = !isZenMode" :title="isZenMode ? t('zenNormal') : t('zenActive')">
          <svg class="icon-svg"><use :xlink:href="isZenMode ? '#icon-eye' : '#icon-eye-off'"></use></svg>
        </button>

        <!-- Language Switcher Button -->
        <button class="btn-secondary" style="min-height: 36px; padding: 6px 12px; font-size: 13px;" @click="currentLang = currentLang === 'en' ? 'kh' : 'en'">
          <svg class="icon-svg" style="margin-right: 4px;"><use xlink:href="#icon-globe"></use></svg>
          {{ currentLang === 'en' ? 'ខ្មែរ' : 'English' }}
        </button>
      </div>
    </header>

    <!-- Connection Status & IP Configuration Card (One Row) -->
    <section v-if="!isZenMode" class="glass-panel" style="padding: 12px; margin-bottom: 16px;">
      <div style="display: flex; gap: 8px; align-items: center; width: 100%;">
        <span 
          :class="['pulse-indicator', wsStatus === 'connected' ? 'pulse-connected' : 'pulse-disconnected']"
          :title="wsStatus === 'connected' ? t('statusConnected') : (wsStatus === 'connecting' ? t('statusConnecting') : t('statusDisconnected'))"
          style="flex-shrink: 0;"
        ></span>
        
        <div style="flex-grow: 1; display: flex; gap: 6px;">
          <input 
            type="text" 
            v-model="serverIp" 
            placeholder="e.g. 192.168.1.100" 
            class="ios-safe-input" 
            style="flex: 2; height: 38px; padding: 6px 10px; font-size: 16px; min-width: 0;"
            :disabled="wsStatus === 'connected'" 
          />
          <input 
            type="number" 
            v-model="serverWsPort" 
            :placeholder="t('wsPort')" 
            class="ios-safe-input" 
            style="flex: 1; min-width: 70px; max-width: 90px; height: 38px; padding: 6px 10px; font-size: 16px;"
            :disabled="wsStatus === 'connected'" 
          />
        </div>
        
        <button 
          v-if="wsStatus !== 'connected'"
          class="btn-primary" 
          @click="connectWS" 
          style="flex-shrink: 0; height: 38px; min-height: 38px; min-width: 38px; padding: 6px 12px; font-size: 13px;"
        >
          <svg class="icon-svg" style="margin-right: 4px;"><use xlink:href="#icon-rocket"></use></svg> {{ t('connect') }}
        </button>
        <button 
          v-else
          class="btn-danger" 
          @click="disconnectWS" 
          style="flex-shrink: 0; height: 38px; min-height: 38px; min-width: 38px; padding: 6px 12px; font-size: 13px;"
        >
          <svg class="icon-svg" style="margin-right: 4px;"><use xlink:href="#icon-stop"></use></svg> {{ t('disconnect') }}
        </button>
      </div>
    </section>

    <!-- Camera Feed and Overlay -->
    <section class="glass-panel" style="padding: 12px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px;">
      <div class="video-scanner-wrapper">
        <video 
          ref="videoElement" 
          autoplay 
          playsinline 
          muted 
          class="scanner-video"
        ></video>
        
        <div class="scanner-overlay" v-if="cameraStatus === 'running'">
          <div class="scanner-box-guide"></div>
          <div class="laser-line" v-if="showLaserLine"></div>
        </div>

        <div 
          v-if="cameraStatus !== 'running'" 
          style="position: absolute; inset: 0; display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.6); color: var(--text-secondary); text-align: center; padding: 20px;"
        >
          <div>
            <div style="margin-bottom: 8px;">
              <svg class="icon-svg" style="width: 32px; height: 32px;"><use xlink:href="#icon-camera"></use></svg>
            </div>
            <div>{{ cameraStatus === 'starting' ? t('cameraStarting') : (cameraStatus === 'stopped' ? t('cameraStopped') : t('cameraErr')) }}</div>
          </div>
        </div>
      </div>

      <!-- Settings and Camera selectors -->
      <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap;">
        <div style="display: flex; gap: 8px; flex-grow: 1; flex-basis: 150px;">
          <select 
            v-model="selectedDeviceId" 
            @change="startCamera" 
            class="ios-safe-input" 
            style="flex-grow: 1; height: 38px; padding: 6px 12px; font-size: 14px;"
          >
            <option value="" disabled>{{ t('selectCamera') }}</option>
            <option v-for="cam in cameraDevices" :key="cam.deviceId" :value="cam.deviceId">
              {{ cam.label || `Camera ${cameraDevices.indexOf(cam) + 1}` }}
            </option>
          </select>
          
          <button 
            v-if="cameraStatus === 'running' || cameraStatus === 'starting'"
            class="btn-secondary" 
            style="height: 38px; min-height: 38px; min-width: 38px; padding: 6px;"
            @click="togglePause"
            title="Pause/Play"
          >
            <svg class="icon-svg"><use :xlink:href="isPaused ? '#icon-play' : '#icon-pause'"></use></svg>
          </button>

          <button 
            v-if="cameraStatus === 'running' || cameraStatus === 'starting'"
            class="btn-danger" 
            style="height: 38px; min-height: 38px; min-width: 38px; padding: 6px;"
            @click="stopCamera"
            :title="t('disconnect')"
          >
            <svg class="icon-svg"><use xlink:href="#icon-stop"></use></svg>
          </button>
          <button 
            v-else
            class="btn-primary" 
            style="height: 38px; min-height: 38px; min-width: 38px; padding: 6px;"
            @click="startCamera"
            :title="t('connect')"
          >
            <svg class="icon-svg"><use xlink:href="#icon-camera"></use></svg>
          </button>
        </div>

        
      </div>
    </section>

    <!-- Scan Results Card -->
    <section class="glass-panel" style="padding: 16px; margin-bottom: 16px;">
      <h2 style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 8px;">
        {{ t('lastScanned') }}
      </h2>
      
      <div v-if="lastCode" style="display: flex; justify-content: space-between; align-items: center; background: #07070a; padding: 12px; border: 2px solid var(--border-color); box-shadow: inset 2px 2px 0px 0px rgba(0,0,0,0.8);">
        <code style="font-family: var(--font-pixel); font-size: 2.2rem; font-weight: 700; color: var(--success); word-break: break-all; text-shadow: 0 0 10px var(--success-glow); line-height: 1;">
          {{ lastCode }}
        </code>
        <button 
          class="btn-secondary" 
          style="min-height: 36px; padding: 6px 12px; font-size: 13px;"
          @click="copyToClipboard(lastCode, 'last')"
        >
          <svg class="icon-svg"><use :xlink:href="copiedIndex === 'last' ? '#icon-check' : '#icon-copy'"></use></svg>
          {{ copiedIndex === 'last' ? t('copied') : t('copy') }}
        </button>
      </div>
      <div v-else style="color: var(--text-muted); font-size: 0.9rem; font-style: italic;">
        {{ t('noScans') }}
      </div>
    </section>

    <!-- Settings Panel -->
    <details v-if="!isZenMode" class="glass-panel" style="padding: 16px; margin-bottom: 16px;">
      <summary style="cursor: pointer; font-weight: 600; font-size: 0.9rem; color: var(--text-secondary); user-select: none;">
        <svg class="icon-svg" style="margin-right: 4px;"><use xlink:href="#icon-settings"></use></svg>
        {{ t('settings') }}
      </summary>
      
      <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 12px;">
        <label style="display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem;">
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <svg class="icon-svg"><use xlink:href="#icon-volume"></use></svg>
            {{ t('beepLabel') }}
          </span>
          <input type="checkbox" v-model="beepOnScan" style="width: 20px; height: 20px; cursor: pointer;" />
        </label>
        
        <label style="display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem;">
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <svg class="icon-svg"><use xlink:href="#icon-vibrate"></use></svg>
            {{ t('vibrateLabel') }}
          </span>
          <input type="checkbox" v-model="vibrateOnScan" style="width: 20px; height: 20px; cursor: pointer;" />
        </label>

        <label style="display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem;">
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <svg class="icon-svg"><use xlink:href="#icon-shield"></use></svg>
            {{ t('doubleVerifyLabel') }}
          </span>
          <input type="checkbox" v-model="requireDoubleVerification" style="width: 20px; height: 20px; cursor: pointer;" />
        </label>

        <label style="display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem;">
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <svg class="icon-svg"><use xlink:href="#icon-camera"></use></svg>
            {{ t('laserLabel') }}
          </span>
          <input type="checkbox" v-model="showLaserLine" style="width: 20px; height: 20px; cursor: pointer;" />
        </label>

        <label style="display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 0.9rem;">
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <svg class="icon-svg"><use xlink:href="#icon-settings"></use></svg>
            {{ t('themeLabel') }}
          </span>
          <select v-model="theme" class="ios-safe-input" style="width: auto; height: 36px; padding: 4px 10px; font-size: 13px; flex-shrink: 0;">
            <option value="light">{{ t('themeLight') }}</option>
            <option value="dark">{{ t('themeDark') }}</option>
            <option value="system">{{ t('themeSystem') }}</option>
          </select>
        </label>

        <label style="display: flex; flex-direction: column; gap: 6px; font-size: 0.9rem;">
          <div style="display: flex; justify-content: space-between;">
            <span style="display: inline-flex; align-items: center; gap: 6px;">
              <svg class="icon-svg"><use xlink:href="#icon-clock"></use></svg>
              {{ t('debounceLabel') }}
            </span>
            <span style="color: var(--primary);">{{ debounceDelay }}ms</span>
          </div>
          <input type="range" min="500" max="5000" step="250" v-model.number="debounceDelay" style="cursor: pointer;" />
        </label>
      </div>
    </details>

    <!-- Scan History List (Collapsable, collapsed by default) -->
    <details v-if="!isZenMode && historyList.length > 0" class="glass-panel" style="padding: 16px; margin-bottom: 16px;">
      <summary style="cursor: pointer; font-weight: 600; font-size: 0.9rem; color: var(--text-secondary); user-select: none; display: flex; justify-content: space-between; align-items: center;">
        <span style="display: inline-flex; align-items: center; gap: 6px;">
          <svg class="icon-svg"><use xlink:href="#icon-history"></use></svg>
          {{ t('history') }} ({{ historyList.length }})
        </span>
        <button 
          class="btn-secondary" 
          style="min-height: 28px; padding: 4px 8px; font-size: 11px; border-radius: 4px; z-index: 10;"
          @click.stop="clearHistory"
        >
          <svg class="icon-svg" style="width: 12px; height: 12px;"><use xlink:href="#icon-trash"></use></svg>
          {{ t('clearHistory') }}
        </button>
      </summary>

      <div style="overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-top: 12px; max-height: 200px; padding-right: 4px;">
        <div 
          v-for="(item, idx) in historyList" 
          :key="idx" 
          style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid rgba(255,255,255,0.03);"
        >
          <div style="display: flex; flex-direction: column; gap: 2px;">
            <code style="font-weight: 600; color: var(--text-primary); font-size: 0.95rem; word-break: break-all;">
              {{ item.code }}
            </code>
            <span style="font-size: 0.75rem; color: var(--text-muted);">
              {{ item.time }}
            </span>
          </div>
          
          <button 
            class="btn-secondary" 
            style="min-height: 32px; padding: 4px 8px; font-size: 11px; border-radius: 4px;"
            @click="copyToClipboard(item.code, idx)"
          >
            <svg class="icon-svg" style="width: 12px; height: 12px;"><use :xlink:href="copiedIndex === idx ? '#icon-check' : '#icon-copy'"></use></svg>
            {{ copiedIndex === idx ? t('copied') : t('copy') }}
          </button>
        </div>
      </div>
    </details>
  </div>
</template>

<style scoped>
details summary::-webkit-details-marker {
  display: none;
}
</style>
