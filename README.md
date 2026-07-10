# InMoov2 i2 Head - AI Mock Interview Robot Pipeline

This project is the AI brain and hardware (MRL) connection pipeline for driving a social robot based on the InMoov2 i2 head. It has been specifically evolved into an **AI Mock Interview System** featuring a Web-based Control UI and a dynamic Persona Engineering system.

> **Scope:** This repository covers the core pipeline connecting the robot's intelligence (Python/Flask) to its body (MyRobotLab). The ROS2-based simulation is developed separately and is **not** included in this repository.

---

## 📌 Architecture Overview (Web UI + Hybrid Strategy)

The burden of hardware control is delegated to MyRobotLab (MRL), while the AI logic and User Interface are isolated in a separate Python (Flask) environment.

```text
┌──────────────────────────────────────┐        ┌──────────────────────────┐
│      AI Brain (Flask / Python)       │        │   Body (MRL / MyRobotLab)│
│                                      │  HTTP  │                          │
│  [Web UI] Setup & Chat Interface     │  API   │  expressEmotion(label)   │
│    → Persona YAML Injection          │───┼──────▶│    → InMoov2 i2 head      │
│    → LLM Logic (Emotion + Chat)      │ :8888  │       (Execute Gestures) │
└──────────────────────────────────────┘        └──────────────────────────┘
```

1. **Web UI (`web_app.py`)**: A Flask-based dashboard where users can select the target company and interviewer persona, and conduct the interview interactively.
2. **Persona System (`personas/`)**: YAML files containing deep psychological and technical criteria for top IT companies (Samsung, Naver, Kakao, Toss, Woowa Brothers) and interviewer styles (Strict, Generous, Neutral).
3. **MRL Bridge (`mrl_bridge.py`)**: Safely transmits the 'emotion' determined by the LLM from Python to the MRL server.
4. **MRL Body**: Receives `expressEmotion(label)` via the MRL Web API and moves the servo motors (facial expressions).

---

## 🛠 Key Files and Roles

| Path | Role |
|------|------|
| `ai_brain/web_app.py`        | **[NEW]** Main Flask Web Server & API backend |
| `ai_brain/templates/`        | **[NEW]** Single Page Application (SPA) HTML view |
| `ai_brain/static/`           | **[NEW]** Premium Dark Mode CSS & Vanilla JS Logic |
| `ai_brain/personas/`         | **[NEW]** System Prompt data (`companies.yaml`, `styles.yaml`) |
| `ai_brain/brain_core.py`     | Legacy pipeline script (STT ➡️ LLM ➡️ TTS) |
| `ai_brain/mrl_bridge.py`     | Bridge: calls MRL REST API to run `expressEmotion` |
| `ai_brain/requirements.txt`  | Python dependency list (now includes `Flask`) |
| `mrl_setup/emotions.py`      | Custom Jython script for MRL (emotion label → gesture) |
| `mrl_setup/README.md`        | **Full MRL setup guide (from scratch)** |

---

## ✅ Prerequisites

- **OS:** Ubuntu 22.04 (tested) · **Python:** 3.10+
- **Internet connection required** — STT/TTS and LLM APIs are online services.
- **A running MRL instance** exposing `expressEmotion` on port `8888`.

---

## ⚙️ Setup & Run (From Scratch)

### Step 1 — System packages (apt)
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev flac
```

### Step 2 — AI Brain (Python) environment
```bash
cd ai_brain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3 — MRL (Body)  ⭐ critical
The bridge needs a running MRL where `expressEmotion` is loaded and `i01` (+ head) is started.
*(If you do NOT have MRL yet → follow the full guide in [`mrl_setup/README.md`](mrl_setup/README.md))*

**Verify the bridge can reach MRL:**
```bash
cd ai_brain
python3 mrl_bridge.py 놀람
```

### Step 4 — Run the Web UI Dashboard
```bash
cd ai_brain
python3 web_app.py
```
Open a web browser and navigate to **`http://127.0.0.1:5000`**. You will see the premium dark-mode interface where you can set up the interview environment.

---

## 🚀 Implementation Details & Highlights

### 1. Advanced Persona Engineering (YAML)
Instead of hardcoding prompts, the system uses structured YAML data. By combining `companies.yaml` (Core values, Green/Red flags) and `styles.yaml` (Tone, Reaction style), the AI generates a highly realistic and tailored interview experience based on the CASA (Computers-Are-Social-Actors) paradigm.

### 2. Premium UI/UX
The front-end uses Glassmorphism and modern Dark Mode aesthetics. It features a chat-like transcript view, a timer, and explicit `[Done Speaking]` buttons to solve the common STT cutoff issue during long pauses.

### 3. MRL (Jython) Code-Injection Prevention
MRL's internal interpreter is Jython 2.7. `mrl_bridge.py` applies safety mechanisms (`json.dumps`) to escape special characters in LLM outputs, preventing arbitrary code execution.

---

## 📝 Future Improvements
1. **Real LLM Integration**: Replace the Mock APIs in `web_app.py` with actual OpenAI/Gemini SDK calls using the loaded YAML personas.
2. **STT Enhancement**: Migrate Google Web Speech → local Whisper for offline speed.
3. **Hardware**: Connect the physical i2 head servos to a real controller (PCA9685) and calibrate.
