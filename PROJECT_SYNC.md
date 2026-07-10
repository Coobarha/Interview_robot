# Project Sync (Antigravity ↔ Claude)

## 📌 목표 및 아키텍처 (Plan B: Hybrid)
- **전략:** 하드웨어 제어의 부담을 줄이고 AI 로직에 집중하기 위해 MRL과 Python을 분리 연동.
- **두뇌 (AI 로직):** 순수 Python 기반. (음성 인식 STT ➡️ LLM 판단 ➡️ 대답(TTS) 및 감정 텍스트 도출)
- **통신 (Bridge):** Python ↔ MRL API(또는 Websocket) 연동하여 명령 전달.
- **몸통 (하드웨어):** MRL(MyRobotLab)이 수신된 명령을 바탕으로 서보모터를 제어 (순수 하드웨어 드라이버 역할).

## ✅ 구현 현황 (Status)
1. **표정 관절 매핑 검증 (완료):**
   - ROS2 (`i2_head_ws`) 환경에서 7가지 표정 매핑 로직 확인 완료.
2. **STL 시각화 우회 (완료):**
   - 기본 도형(Primitive shapes)으로 RViz 렌더링 우회 완료.
3. **AI 두뇌 파이프라인 프로토타입 (진행 중):**
   - `ai_brain` 폴더 생성 및 `requirements.txt` 설정 완료.
   - `brain_core.py`를 통해 마이크 입력(STT) -> LLM(현재 Dummy 로직) -> 스피커 출력(TTS) 파이프라인 뼈대 구축 완료.
   - **[해결]** PyAudio/SpeechRecognition 초기화 시 발생하는 ALSA 경고(Unknown PCM)를 `ctypes`를 이용해 C-level 에러 핸들러를 덮어써 완벽하게 억제함.
   - **실제 음성 테스트 완료**: 구글 STT가 "안녕"을 성공적으로 인식하고, 더미 LLM이 'happy' 감정 라벨과 응답을 정상 도출함.
4. **Python→MRL 표정 브리지 (완료 · Claude, 2026-07-08):**
   - `ai_brain/mrl_bridge.py` 신규 작성. `MRLBridge.express_emotion(label)` 이 MRL 웹 API(`POST /api/service/python/exec`)로 `expressEmotion(u"...")` 호출.
   - Jython(파이썬2) 한글 유니코드 처리 + `json.dumps` 이스케이프로 코드 인젝션 방지. `is_alive()` 헬스체크 포함.
   - **실 MRL 검증 완료**: 놀람→jaw160/눈썹180, happy/sad/anger/surprise 모두 서보 반영 확인.
   - `brain_core.py` 를 이 브리지로 연결(버그였던 `setEmotion` → `express_emotion` 교체). STT/LLM/TTS 로직은 그대로 둠.
   - `requirements.txt` 에 누락돼 있던 `requests` 추가.
5. **GitHub 신규클론 세팅 검수 (완료 · Claude, 2026-07-10):**
   - `.gitignore` 신규 작성 — `build/ install/ log/ __pycache__ *.log *.mp3 *.stl stl/` 제외. (이미 커밋돼 있던 pycache 는 추적 해제)
   - `README.md` 세팅 섹션 전면 보강 — 시스템 패키지(`portaudio19-dev, flac, python3-venv`), venv, 인터넷 요구사항, 공통 이슈 표 추가.
   - `mrl_setup/README.md` 신규 — **MRL 처음부터 세팅 전체 가이드**(JDK→다운로드→설치 데드락 우회→emotions.py 복사→i01+head 시작→가상아두이노 연결→검증). README 가 참조만 하고 절차가 없던 최대 구멍 메움.
   - 검증: 신규클론 파일세트 47개(대용량 stl 31M/build/install/log 전부 제외 확인), requirements ↔ 실제 import 일치 확인.
   - [결정됨] `src/`(ROS2 시뮬)은 **저장소에서 제외**(`.gitignore`에 `src/` 추가). 이 repo 는 Python 두뇌+MRL 브리지 파이프라인만. 신규클론 파일세트 36개로 확정.

## 🚀 다음 단계 (Next Steps)
- **AI 두뇌 테스트 및 고도화:**
  - 사용자 환경에서 `brain_core.py`를 실행하여 마이크와 스피커가 잘 연동되는지 테스트.
  - 더미 로직을 실제 Local Whisper(STT)나 실제 AI API로 교체.
- **MRL 연동 및 통신 (표정 전송: 완료):**
  - ~~표정 전송 브리지~~ → `mrl_bridge.py` 로 완료. HTTP API 방식 채택(WebSocket 불필요).
  - (선택) 발화도 MRL 스피커로 하려면 `MRLBridge.speak()` + `send_to_mrl(..., speak_via_mrl=True)` 사용. 현재는 Plan B 대로 Python(gTTS)이 TTS 담당.
- **AI 두뇌 실체화 (다음 핵심):**
  - `brain_core.py` 의 더미 LLM(`mock_llm_logic`)을 실제 API(OpenAI/Gemini)로 교체하고, 응답에서 감정 라벨을 뽑아 그대로 `mrl.express_emotion()` 에 전달.
  - STT 를 Google Web Speech → Local Whisper 로 교체(오프라인/속도).

## ⚠️ 알려진 문제점 및 이슈 (Issues)
- 기존에 작성된 ROS2 URDF/Node의 관절값(라디안, 미터)은 실제 모터(Degree) 값과 다름. 하지만 하드웨어 구동을 MRL로 전임하기로(Plan B) 결정함에 따라 해당 이슈는 무시해도 됨. MRL 내장 표정(emotions) 기능을 활용할 것.
- **[해결] MRL 표정 함수명은 `setEmotion` 이 아니라 `expressEmotion` 임** (MRL `resource/InMoov2/gestures/emotions.py`). brain_core 에서 잘못 호출하던 것 수정됨.
- **[전제조건] 브리지는 MRL 이 `localhost:8888` 에서 실행 중이고 `i01`(InMoov2)+`i01.head`+gestures(emotions.py)가 로드된 상태여야 동작함.** 현재 개발 PC의 MRL 인스턴스는 이 상태로 떠 있음.
- **[참고] 표정은 순간적(움직였다 중립 복귀)** — 실 하드웨어에선 자연스럽지만, 값 검증 시 호출 직후 바로 샘플링해야 피크가 잡힘.

---
**💡 룰 (Collaboration Rules):**
1. 새로운 작업을 시작하기 전 이 파일을 읽고 현재 상태를 파악할 것.
2. 작업이 끝난 후 진행된 내용, 새로 발생한 문제점, 다음 스텝을 이 파일에 반드시 업데이트할 것.
