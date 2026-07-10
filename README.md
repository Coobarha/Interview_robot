# InMoov2 i2 Head - AI Brain & MRL Connection Pipeline

This project is the AI brain and hardware (MRL) connection pipeline for driving a social robot based on the InMoov2 i2 head.

> **Note:** This guide and codebase focus on the core pipeline that connects the robot's intelligence (Python) to its body (MyRobotLab). The ROS2-based simulation parts are excluded from this specific guide.

## 📌 Architecture Overview (Hybrid Strategy)

This project employs a **hybrid strategy** where the burden of hardware control is delegated to MyRobotLab (MRL), while the AI logic is isolated in a separate Python environment.

```text
┌─────────────────────────────┐        ┌──────────────────────────┐
│  Brain (Python / ai_brain)  │        │   Body (MRL / MyRobotLab)│
│                             │  HTTP  │                          │
│  Mic → STT (Google)         │  API   │  expressEmotion(label)   │
│    → LLM Logic(Emotion+Chat)───┼───────▶│    → InMoov2 i2 head      │
│    → TTS Output (gTTS)      │ :8888  │       (Execute Gestures) │
└─────────────────────────────┘        └──────────────────────────┘
        (mrl_bridge.py handles this arrow)
```

1. **AI Brain (`brain_core.py`)**: Listens to user voice (STT), determines the appropriate response and emotion via an AI model (LLM), and outputs the response via speakers (TTS).
2. **MRL Bridge (`mrl_bridge.py`)**: Safely transmits the 'emotion' data derived from the Python environment to the MRL server.
3. **MRL Body**: Receives the `expressEmotion(label)` command via the MRL Web API, interprets it, and moves the actual servo motors (facial expressions).

---

## 🛠 Key Files and Roles

* `ai_brain/brain_core.py` : The main script controlling the entire pipeline (STT ➡️ LLM ➡️ TTS and sending expressions).
* `ai_brain/mrl_bridge.py` : The communication bridge that calls MRL's REST API to execute Python code within MRL.
* `ai_brain/requirements.txt` : The list of dependency packages required to run the Python environment.

---

## 🚀 Implementation Details & Troubleshooting

### 1. Suppressing ALSA (PyAudio) Error Logs
In `brain_core.py`, unnecessary ALSA error messages (like Unknown PCM) that occur during PyAudio and SpeechRecognition initialization are blocked at the C-level using `ctypes`. This keeps the console output clean.

### 2. MRL (Jython) Korean Encoding & Code Injection Prevention
MRL's internal Python environment (Jython 2.7) is highly sensitive to handling Korean characters (and other non-ASCII characters). `mrl_bridge.py` applies two safety mechanisms:
* Uses `json.dumps(label, ensure_ascii=True)` to escape special characters in the LLM output text, preventing code injection.
* Forces the use of Unicode literal formatting `u"..."` when passing data to MRL, ensuring that Korean emotion labels (e.g., "기쁨", "놀람") are not corrupted and are correctly recognized in the Jython environment.

### 3. Modularization with Mock LLM
Currently, the `mock_llm_logic` function in `brain_core.py` acts as a dummy AI logic based on keyword matching. It is modularized to return a dictionary structure (`{"emotion": "...", "response": "..."}`), making it easy to replace with an actual LLM API (like OpenAI, Anthropic Claude, or Local LLM like Ollama) in the future.

---

## ⚙️ How to Run

### 1. Install Dependencies
Install the required libraries for the Python environment. (You may need system packages like `portaudio19-dev` for PyAudio).
```bash
cd ai_brain
pip install -r requirements.txt
```

### 2. Run MRL (MyRobotLab)
Run your pre-installed MRL environment. (The InMoov2 service and HTTP service port `8888` must be open).
> **Note:** Gestures corresponding to emotion labels must be mapped in MRL's internal `emotions.py`.

### 3. Run the AI Pipeline
While MRL is running, start the AI brain with the command below:
```bash
cd ai_brain
python3 brain_core.py
```
* When you speak into the microphone (e.g., "Hello", "I am surprised"), the recognized text is displayed in the terminal, the expression command is sent to MRL, and shortly after, the response is output through the speaker.
* To test only the MRL bridge independently, you can run `python3 mrl_bridge.py happy`.

---

## 📝 Future Improvements
1. **LLM Integration**: Replace `mock_llm_logic` with a real LLM API (Gemini, GPT-4, etc.) to build a true conversational AI.
2. **STT Enhancement**: Migrate from the internet-dependent Google Web Speech API to a local Whisper model to improve response speed and support offline environments.
