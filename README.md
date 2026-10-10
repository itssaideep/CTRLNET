# CTRLNET: Autonomous Network Profiler 🌐

> *"You are no longer in control. ctOS is."*

**CTRLNET** is a Watch Dogs / ctOS-inspired autonomous network profiling and vulnerability research platform. It leverages an ESP8266 hardware implant to silently scout local networks, paired with a powerful Python backend that uses local LLMs (via Ollama) and deterministic NVD matching to identify zero-day risks and known CVEs.

---

## 🏗️ Architecture

The system operates across three distinct layers:

### 1. The Autonomous Scout (Hardware)
An ESP8266 microcontroller acting as a rogue implant. 
- Constantly sweeps the local `/24` subnet using ICMP pings.
- The moment a device is found, it dispatches the target IP to the Central Command server.
- Built using **PlatformIO** (`CTRLNET_Remote`).

### 2. Central Command Server (Backend)
A FastAPI + Uvicorn server running on a high-performance machine.
- Receives dispatch signals from the Scout.
- Launches deep `Nmap` footprinting asynchronously to extract OS, open ports, and raw service banners.
- Uses **Ollama (LLaMA 3.1:8b / Qwen)** to process the raw banners into deterministic Common Platform Enumeration (CPE) strings.
- Cross-references the inferred CPE with the National Vulnerability Database (NVD API v2.0) to find known exploits.
- Stores everything persistently in a SQLite database (`ctrlnet.db`).

### 3. ctOS Dashboard (Frontend)
A sleek, hacker-aesthetic Web GUI for visualizing network intelligence.
- Live-updating nodes and connections.
- Real-time vulnerability streaming.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Nmap (must be in system PATH)
- Ollama (running locally with `llama3.1:8b` pulled)
- PlatformIO (for flashing the ESP8266)

### 1. Start the Backend Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run the central command server
python -m ctrlnet serve
```
*The server will start on `http://0.0.0.0:8000`.*

### 2. Flash the Scout Implant
```bash
cd CTRLNET_Remote
# Edit src/secrets.h to add your WiFi credentials
# Edit src/main.cpp to point to your Central Command laptop IP

# Compile and flash to the ESP8266
pio run --target upload
```

### 3. View the Intelligence
Navigate to `http://localhost:8000/dashboard/index.html` to view the live ctOS visualizer. 

To dump the raw SQLite database telemetry into your terminal:
```bash
python view_results.py
```

---

## 🔬 Research & Evaluation Pipeline
CTRLNET was originally built as a research platform to evaluate the efficacy of local LLMs in footprinting network banners. 

You can run the headless research pipeline against a simulated `mock_esp8266.py` or the provided ground-truth corpus to generate confidence matrices, abstention rates, and accuracy graphs using the `ctrlnet research` CLI.

> **Disclaimer:** CTRLNET is an educational security research tool. Do not deploy the autonomous scout on networks you do not own or do not have explicit permission to audit.
