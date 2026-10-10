# CTRLNET

**CTRLNET** is a Watch Dogs / ctOS-inspired interactive cybersecurity network profiler and research platform.

## Overview
CTRLNET is designed to evaluate whether locally hosted Large Language Models (LLMs) can add useful reasoning capabilities to traditional deterministic vulnerability identification.

It compares:
1. **Deterministic CPE/CVE matching**
2. **Local LLM-based profiling using Ollama**
3. **Hybrid LLM + deterministic verification**

The system features a futuristic UI (Profiler) to visualize the network scanning and inference process in real-time.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, WebSockets
- **Database**: SQLite (via `aiosqlite`)
- **Scanning**: `python-nmap` (requires Nmap installed)
- **NVD/CVE**: `nvdlib`
- **LLM**: Ollama Python SDK (`llama3.1` default)
- **Frontend**: Vanilla HTML/JS, D3.js (Canvas-rendered network graph)

## Prerequisites
1. **Python 3.11+**
2. **Nmap**: Must be installed on your system.
   - Ubuntu/Debian: `sudo apt install nmap`
   - macOS: `brew install nmap`
   - Windows: Download from Nmap.org
3. **Ollama**: Must be running locally (default: http://localhost:11434).
   - Pull at least one model: `ollama pull llama3.1`
4. **NVD API Key** (Optional but highly recommended to avoid severe rate limits).

## Installation

```bash
# Clone the repository
# (Assuming you are in the project root)

# Install dependencies
pip install -r requirements.txt

# Create a .env file for configuration
echo "OLLAMA_MODEL=llama3.1:8b" > .env
echo "NVD_API_KEY=your_api_key_here" >> .env
```

## Usage

### 1. Launch the Server & Dashboard
```bash
python -m ctrlnet serve
```
Open `http://localhost:8000/dashboard/index.html` in your browser to access the Watch Dogs-inspired Profiler interface.

### 2. Run the Research Pipeline (Headless)
```bash
python -m ctrlnet research
```
This runs the predefined evaluation pipeline against the lab corpus located in `ctrlnet/corpus/targets/`.

## Ethical Use
**AUTHORIZED SECURITY RESEARCH ONLY**

CTRLNET is intended for reconnaissance, profiling, vulnerability identification, and research evaluation on isolated lab networks or explicitly authorized systems. Do not use this tool for unauthorized scanning.
