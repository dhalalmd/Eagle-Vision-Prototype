# Smart Border CCTV — M00 Core + Camera Management

Software-only AI layer on top of CCTV / webcam / phone cameras for border surveillance. Built for Smart India Hackathon (SIH26187).

## Features (M00 Core + M08 Camera Dashboard)
- **Multi-Source Ingest**: Laptop webcams, RTSP / HTTP IP cameras, video files, and phone webcams.
- **Low Latency Streaming**: Sub-300ms latency stream over Wi-Fi, single-frame latest-frame buffer, zero backlog.
- **Dynamic Camera Management**: Add, edit, delete, and enable/disable cameras live without server restarts.
- **Phone Camera Web Capture**: Secure HTTPS + WebSocket binary stream from any mobile browser via QR code scan.
- **Cross-Platform**: CPU-only execution on Windows, Linux, and macOS.

---

## Quick Start Guide

### 1. Requirements
- Python 3.9+
- Node.js 18+ and npm
- Laptop & Phone connected to the same Wi-Fi network

### 2. Installation

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install Frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

### 3. Generate Self-Signed Certificates
Generate cross-platform HTTPS certs containing your laptop's LAN IP address:
```bash
python scripts/gen_cert.py
```

### 4. Run Development Application
Run the unified launcher (starts both FastAPI backend and Vite frontend):
```bash
python scripts/run_dev.py
```

- **Dashboard UI**: `http://localhost:5173`
- **Backend API (HTTP)**: `http://localhost:8000`
- **Backend API (HTTPS)**: `https://<YOUR_LAN_IP>:8443`
- **Phone Camera Capture Page**: `https://<YOUR_LAN_IP>:8443/phone?cam=cam_phone`

---

## Network & Firewall Ports
Ensure your firewall allows incoming connections on the following ports for phone camera streaming:
- **Port 8000**: Backend HTTP REST & WebSocket API
- **Port 8443**: Backend HTTPS & WSS (Required for phone browser camera permissions)

---

## Phone Camera Setup & Alternatives

### Primary Method: Mobile Browser Web Capture
1. Open the Dashboard (`http://localhost:5173`).
2. Navigate to **Cameras** -> Click **Add Camera Source** -> Select **Phone Camera**.
3. Scan the generated QR Code with your smartphone.
4. Accept the self-signed certificate warning in your phone browser once.
5. The phone camera video will immediately stream live to the dashboard grid.

### Alternative Method: "IP Webcam" Android App
If using third-party IP camera apps like "IP Webcam" on Android:
1. Open the app on your phone and start the server (e.g. `http://192.168.1.45:8080`).
2. On the Dashboard, click **Add Camera Source** -> Select **IP / RTSP Stream**.
3. Set the stream URL to `http://<PHONE_IP>:8080/video` (or your app's MJPEG endpoint).

---

## Running Unit Tests

Run all unit tests (no physical hardware required):
```bash
pytest tests/
```
