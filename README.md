# InMoov2 i2 Head - AI Brain & MRL Connection Pipeline

This project is the AI brain and hardware (MRL) connection pipeline for driving a social robot based on the InMoov2 i2 head.

> **Scope:** This repository covers the core pipeline connecting the robot's intelligence (Python) to its body (MyRobotLab). The ROS2-based simulation is developed separately and is **not** included in this repository (see `PROGRESS_REPORT.md` for a write-up).

## 📌 Architecture Overview (Hybrid Strategy)

The burden of hardware control is delegated to MyRobotLab (MRL), while the AI logic is isolated in a separate Python environment.

```text
┌─────────────────────────────┐        ┌──────────────────────────┐
│  Brain (Python / ai_brain)  │        │   Body (MRL / MyRobotLab)│
│                             │  HTTP  │                          │
│  Mic → STT (Google)         │  API   │  expressEmotion(label)   │
│    → LLM Logic(Emotion+Chat)───┼──────▶│    → InMoov2 i2 head      │
│    → TTS Output (gTTS)      │ :8888  │       (Execute Gestures) │
└─────────────────────────────┘        └──────────────────────────┘
        (mrl_bridge.py handles this arrow)
```

1. **AI Brain (`brain_core.py`)**: Listens to user voice (STT), determines response + emotion via an AI model (LLM), and speaks the response (TTS).
2. **MRL Bridge (`mrl_bridge.py`)**: Safely transmits the 'emotion' from Python to the MRL server.
3. **MRL Body**: Receives `expressEmotion(label)` via the MRL Web API and moves the servo motors (facial expressions).

---

## 🛠 Key Files and Roles

| Path | Role |
|------|------|
| `ai_brain/brain_core.py`     | Main pipeline: STT ➡️ LLM ➡️ TTS + send expression |
| `ai_brain/mrl_bridge.py`     | Bridge: calls MRL REST API to run `expressEmotion` |
| `ai_brain/requirements.txt`  | Python dependency list |
| `mrl_setup/emotions.py`      | Custom Jython script for MRL (emotion label → gesture) |
| `mrl_setup/README.md`        | **Full MRL setup guide (from scratch)** |
| `mrl_setup/config_backup/`   | Backup of MRL head-servo + virtual-arduino config |

---

## ✅ Prerequisites

- **OS:** Ubuntu 22.04 (tested) · **Python:** 3.10+
- **Internet connection required** — STT (Google Web Speech) and TTS (gTTS) are online services.
- **A running MRL instance** exposing `expressEmotion` on port `8888` (see Step 3).

---

## ⚙️ Setup & Run (From Scratch)

### Step 1 — System packages (apt)
`pyaudio` must be compiled against PortAudio; `flac` is used by SpeechRecognition.
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev flac
```

### Step 2 — AI Brain (Python) environment
```bash
cd ai_brain
python3 -m venv .venv && source .venv/bin/activate   # (recommended, isolates deps)
pip install -r requirements.txt
```

### Step 3 — MRL (Body)  ⭐ critical, most commonly missed
The bridge needs a running MRL where `expressEmotion` is loaded and `i01` (+ head) is started.

**If you do NOT have MRL yet → follow the full guide:**
➡️ **[`mrl_setup/README.md`](mrl_setup/README.md)**
(JDK → download MRL → install (with hang workaround) → copy `emotions.py` → start `i01`+head → attach virtual arduino → verify)

**If MRL is already installed (quick version):**
```bash
# 1) copy the custom gesture script
cp mrl_setup/emotions.py /path/to/mrl/myrobotlab-*/resource/InMoov2/gestures/
# 2) start MRL, then start InMoov2 + head (Web UI Intro tab, or API):
#    curl "http://localhost:8888/api/service/runtime/start/%22i01%22/%22InMoov2%22"
#    curl "http://localhost:8888/api/service/i01/startPeer/%22head%22"
```

**Verify the bridge can reach MRL** (jaw servo should move on "surprise"):
```bash
cd ai_brain
python3 mrl_bridge.py 놀람      # or: python3 mrl_bridge.py surprise
```

### Step 4 — Run the pipeline
```bash
cd ai_brain
python3 brain_core.py
```
Speak into the mic (e.g. "안녕", "깜짝이야") → recognized text is shown → the emotion is sent to MRL
(face moves) → the response is spoken through the speaker.

> **Note:** MRL must be running and gestures fully loaded (`... Gestures loaded, 0 error`) **before** starting the pipeline.

---

## 🚀 Implementation Details & Troubleshooting

### 1. Suppressing ALSA (PyAudio) Error Logs
In `brain_core.py`, noisy ALSA errors during PyAudio/SpeechRecognition init are silenced at the C level via `ctypes`, keeping the console clean.

### 2. MRL (Jython) Korean Encoding & Code-Injection Prevention
MRL's internal interpreter is Jython 2.7 and is sensitive to non-ASCII handling. `mrl_bridge.py` applies two safety mechanisms:
* `json.dumps(label, ensure_ascii=True)` escapes special characters in LLM output → prevents code injection.
* Passes data as a Unicode literal `u"..."` so Korean labels (e.g. "기쁨", "놀람") are not corrupted in Jython.

### 3. Modularization with Mock LLM
`mock_llm_logic` in `brain_core.py` is a keyword-matching dummy returning `{"emotion": ..., "response": ...}`, so it can be swapped for a real LLM (OpenAI / Anthropic / Gemini / local Ollama) with minimal changes.

### Common setup issues
| Symptom | Fix |
|---------|-----|
| `pip install pyaudio` fails | `sudo apt install portaudio19-dev` first |
| STT never recognizes / RequestError | Check internet (Google Web Speech is online) |
| Bridge prints "MRL 응답 없음" | MRL not running / port 8888 not open / `i01` not started |
| Expression sent but robot doesn't move | Servos not attached to a controller — see `mrl_setup/README.md` §4 |

---

## 📝 Future Improvements
1. **LLM Integration**: Replace `mock_llm_logic` with a real LLM API (Gemini, GPT, Claude) for true conversation.
2. **STT Enhancement**: Migrate Google Web Speech → local Whisper for offline speed.
3. **Hardware**: Connect the physical i2 head servos to a real controller (PCA9685) and calibrate.
