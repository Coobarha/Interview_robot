# InMoov i2 Head 소셜 로봇 — 개발 진행 리포트

> 한이음 공모전 / InMoov2 i2 head 기반 소셜 로봇
> 협업: Claude + Antigravity (2 AI 에이전트 코드 분담), 동기화 문서 `PROJECT_SYNC.md`
> 최종 업데이트: 2026-07-08

---

## 0. 아키텍처 — Plan B (하이브리드)

하드웨어 제어 부담을 MRL에 넘기고, AI 로직은 독립 Python으로 분리하는 전략.

```
┌─────────────────────────────┐        ┌──────────────────────────┐
│  두뇌 (Python / ai_brain)    │        │   몸통 (MRL / MyRobotLab) │
│                             │  HTTP  │                          │
│  마이크 → STT               │  API   │  expressEmotion(label)   │
│    → LLM 판단(감정+대답)  ───┼───────▶│    → InMoov2 i2 head 서보 │
│    → TTS 음성출력           │ :8888  │       (표정 실행)         │
└─────────────────────────────┘        └──────────────────────────┘
        (mrl_bridge.py 가 이 화살표를 담당)
```

- **두뇌:** 순수 Python (STT → LLM → TTS + 감정 텍스트 도출)
- **브리지:** Python → MRL 웹 API 로 표정 명령 전달 (`mrl_bridge.py`)
- **몸통:** MRL 이 명령을 받아 서보 제어 (순수 하드웨어 드라이버 역할)

---

## 1. MRL (몸통 / 하드웨어 두뇌) 구축

### 1.1 설치 — 휴대용 JDK + 설치기 데드락 우회

MRL Nixie `1.1.1611` 설치. 시스템에 Java 가 없고 sudo 제약이 있어 **폴더 내장 휴대용 JDK17(Temurin)** 로 구성.

```
~/mrl/
├── myrobotlab-1.1.1611/     # MRL 본체
│   ├── java -> ../jdk-17.0.19+10   # 심볼릭 링크 (MRL 이 자동 인식)
│   └── bin/wget             # 조용한 wget 래퍼 (아래 버그 우회용)
├── jdk-17.0.19+10/          # 휴대용 JDK
└── start-mrl.sh             # PATH 자동설정 실행 스크립트
```

**겪은 버그 — 설치기 데드락:** MRL `--install` 은 `libraries/install.sh` 에
`wget ...ivy.jar` + `java -jar ivy... -retrieve` 를 써두고 실행하는데, **wget 진행률 출력을
읽지 않아 파이프 버퍼가 차면 hang**. 우회책:
1. `bin/wget` = `wget -q` 래퍼를 PATH 앞에 둠 (출력 억제)
2. ivy retrieve 를 **수동 실행**해 캐시를 채운 뒤 `--install` 을 돌려 `repo.json` 생성

결과: 713 jar(1.7GB), InMoov2 서비스(`resource/InMoov2/`) 정상 설치.

### 1.2 감정 → 표정 디스패처: `emotions.py` (핵심 커스텀 코드)

**위치:** `~/mrl/myrobotlab-1.1.1611/resource/InMoov2/gestures/emotions.py`

InMoov2 기본 파일 `faceExpressions.py` 에 이미 `happy()/sad()/anger()/surprise()...` 표정 함수가
구현돼 있음. 우리가 추가한 것은 **"감정 라벨 → 표정 함수" 디스패처**.

```python
from __future__ import unicode_literals   # 한글 매칭 안정화
# 주의: InMoov2 는 이 파일을 '유니코드 문자열'로 읽어 exec 하므로
#       '# -*- coding: utf-8 -*-' 선언을 넣으면 SyntaxError 남.

emotionMap = {
    "happy":"happy","joy":"happy","기쁨":"happy","행복":"happy", ...
    "sad":"sad","슬픔":"sad","우울":"sad", ...
    "angry":"anger","화남":"anger","분노":"anger", ...
    "surprise":"surprise","놀람":"surprise","충격":"surprise", ...
    "fear":"fear","두려움":"fear", "disgust":"disgust","혐오":"disgust",
    "neutral":"neutral","중립":"neutral", ...
}
emotionDefault = "neutral"

def toText(label):
    """byte-str/unicode/None 무엇이 오든 안전하게 unicode 로. (Jython2 는 str(u'한글') 이 터짐)"""
    if label is None: return u""
    if isinstance(label, bytes):
        try: return label.decode("utf-8")
        except Exception: return label.decode("utf-8", "ignore")
    return u"%s" % label

def resolveEmotion(label):
    key = toText(label).strip()
    if not key: return emotionDefault
    return emotionMap.get(key.lower(), emotionMap.get(key, emotionDefault))

def expressEmotion(label):
    """Phase 5 진입점: 감정 라벨 → 해당 표정 gesture 실행."""
    labelText = toText(label)
    fnName = resolveEmotion(labelText)
    fn = globals().get(fnName)          # gesture 는 하나의 전역 네임스페이스 공유
    if fn is None or not callable(fn): return None
    print(u"expressEmotion: '%s' -> %s()" % (labelText, fnName))
    fn()
    return fnName
```

**코드레벨 포인트 (Jython/파이썬2 함정 3가지):**
1. `# -*- coding: utf-8 -*-` **금지** — InMoov2 로더가 파일을 유니코드 문자열로 `exec` 하는데,
   유니코드 문자열 안에 인코딩 선언이 있으면 `SyntaxError: encoding declaration in Unicode string`.
2. `from __future__ import unicode_literals` **필수** — utf-8 파일의 `"기쁨"` 리터럴이 byte-str 이라
   unicode 입력과 매칭 실패. future import 로 모든 리터럴을 unicode 화.
3. `str(u'한글')` **금지** — Jython2 에서 ASCII 인코딩 에러. `toText()` 로 정규화.
4. gesture 파일들은 **하나의 전역 네임스페이스에서 exec** 됨(`InMoov2.py:112-121`) → `globals()[fnName]()`
   로 다른 파일의 표정 함수를 직접 호출 가능.

리로드: `i01.loadGestures()`. 현재 **224 gestures, 0 error** 로 로드됨.

### 1.3 가상 모드 검증

웹 API 로 조작 (`http://localhost:8888/api/service/...`):
```
setAllVirtual(true) → i01=InMoov2 start → i01.startPeer("head")
```
- 기본 config 는 head servo 들이 `autoStart:false` → `data/config/default/i01.head.yml` 에서 true 로 변경
- 서보 config 가 `controller:null` → 가상 아두이노 생성 후 `va.attach("i01.head.<servo>", pin)` 로 연결
- **검증:** `expressEmotion(u"놀람")` → 눈썹 180 / 턱 160 / 눈꺼풀 162, `expressEmotion(u"화남")` → 눈썹 0 / 볼 0

---

## 2. ROS2 시뮬레이션 패키지 `i2_head_sim`

> Plan B 에서 하드웨어는 MRL 담당이라, 이 시뮬은 **검증·시각화용 곁가지**.

### 2.1 패키지 구조
```
~/i2_head_ws/src/i2_head_sim/
├── urdf/i2_head.urdf.xacro          # 로봇 모델 + ros2_control + gazebo/mock 전환
├── config/controllers.yaml          # joint_state_broadcaster + head_position_controller
├── config/head.rviz                 # RViz 뷰 설정
├── launch/gazebo.launch.py          # Gazebo Classic (현재 플러그인 버그로 막힘)
├── launch/rviz_control.launch.py    # RViz + mock 하드웨어 (작동)
├── launch/display.launch.py         # RViz + 슬라이더 (빠른 확인)
├── scripts/expression_publisher.py  # 감정 → 관절 명령
└── meshes/                          # STL 넣는 곳 (README + 미완)
```

### 2.2 URDF — i2 head 13관절 (`i2_head.urdf.xacro`)

관절: `rothead, neck, jaw, eye_left/right_pan, eyebrow_left/right(prismatic),
cheek_left/right(prismatic), eyelid_left/right_upper, eyelid_left/right_lower`

**xacro 인자로 하드웨어/메시 전환:**
```xml
<xacro:arg name="hw" default="gazebo"/>          <!-- gazebo | mock -->
<xacro:arg name="use_meshes" default="false"/>   <!-- true 면 STL 렌더 -->
<xacro:property name="hw_type" value="$(arg hw)"/>
<xacro:property name="use_meshes" value="$(arg use_meshes)"/>
```

**mesh/primitive 전환 매크로 (`viz`):**
```xml
<xacro:macro name="viz" params="mesh:='' mat:=skin ox:=0 oy:=0 oz:=0 ... *prim">
  <xacro:if value="${use_meshes and mesh != ''}">        <!-- STL -->
    <visual><origin xyz="${ox} ${oy} ${oz}"/>
      <geometry><mesh filename="package://i2_head_sim/meshes/${mesh}" scale="0.001 0.001 0.001"/></geometry>
    </visual>
  </xacro:if>
  <xacro:unless value="${use_meshes and mesh != ''}">     <!-- 프리미티브 -->
    <xacro:insert_block name="prim"/>
  </xacro:unless>
</xacro:macro>
```

**하드웨어 플러그인 조건부 (gazebo vs mock):**
```xml
<ros2_control name="HeadSystem" type="system">
  <hardware>
    <xacro:if value="${hw_type == 'gazebo'}"><plugin>gazebo_ros2_control/GazeboSystem</plugin></xacro:if>
    <xacro:if value="${hw_type == 'mock'}"><plugin>mock_components/GenericSystem</plugin></xacro:if>
  </hardware>
  ... 13개 joint 마다 position command/state interface ...
</ros2_control>
```

### 2.3 컨트롤러 (`controllers.yaml`)
```yaml
controller_manager:
  ros__parameters:
    update_rate: 100
    joint_state_broadcaster: {type: joint_state_broadcaster/JointStateBroadcaster}
    head_position_controller: {type: position_controllers/JointGroupPositionController}
head_position_controller:
  ros__parameters:
    joints: [rothead, neck, jaw, eye_left_pan, eye_right_pan,
             eyebrow_left, eyebrow_right, cheek_left, cheek_right,
             eyelid_left_upper, eyelid_right_upper, eyelid_left_lower, eyelid_right_lower]
```
→ 13관절을 한 그룹으로 위치제어 (= "서보 각도 명령"). `expression_publisher` 의 배열 순서와 일치해야 함.

### 2.4 감정 → 관절 노드 (`expression_publisher.py`)

MRL `emotions.py` 매핑을 ROS2 로 이식. `/head_position_controller/commands` 로 `Float64MultiArray` 발행.

```python
JOINT_ORDER = ["rothead","neck","jaw","eye_left_pan","eye_right_pan",
               "eyebrow_left","eyebrow_right","cheek_left","cheek_right",
               "eyelid_left_upper","eyelid_right_upper","eyelid_left_lower","eyelid_right_lower"]

PRESETS = {   # 라디안 / prismatic 은 미터, URDF limit 범위 안
  "surprise": _mk(eyebrow_left=0.02, eyebrow_right=0.02,
                  eyelid_left_upper=0.0, eyelid_right_upper=0.0, jaw=0.45),
  "anger":    _mk(eyebrow_left=-0.013, cheek_left=-0.008, eyelid_left_upper=0.28, jaw=0.05),
  ... happy/sad/fear/disgust/neutral ...
}
EMOTION_MAP = { "기쁨":"happy","화남":"anger","놀람":"surprise", ... }  # 한/영
```
실행: `ros2 run i2_head_sim expression_publisher 놀람` / `... demo`(순환).
**검증:** `놀람` 발행 시 `/joint_states` = `[..., jaw 0.45, ..., eyebrow 0.02, ...]` 정확히 반영.

### 2.5 겪은 버그 — gazebo_ros2_control 0.4.10 (Gazebo 막힘)

```
[ERROR] gazebo_ros2_control: parser error Couldn't parse parameter override rule:
        '--param robot_description:=<?xml ... '
```
**원인:** 플러그인이 controller_manager 에 robot_description(URDF XML)을 CLI `--param` 으로 넘기는데,
XML 은 유효한 YAML/param 값이 아니라 rcl 인자 파서가 거부 → controller_manager 초기화 실패 →
`list_controllers` 무응답. **플러그인 내부 버그라 launch 에서 우회 불가** (개행 제거로도 안 됨).

**해결 — RViz + mock 하드웨어로 전환 (`rviz_control.launch.py`):**
```python
# controller_manager 에 robot_description 을 'param dict' 로 전달 → CLI 파싱 버그 없음
cm = Node(package='controller_manager', executable='ros2_control_node',
          parameters=[{'robot_description': robot_desc}, controllers_file])
```
→ `mock_components/GenericSystem` 사용. **joint_state_broadcaster + head_position_controller 둘 다 active**,
표정 순환 정상 작동 (물리엔진만 빠짐 — 얼굴엔 불필요).

### 2.6 겪은 버그 — xacro 불리언 자동변환

`${use_meshes == 'true'}` 가 항상 False → 메시가 안 나옴.
**원인:** xacro 가 `"true"` 문자열을 **파이썬 불리언 `True` 로 자동 변환** → `True == 'true'` 는 False.
**해결:** `${use_meshes and mesh != ''}` (불리언으로 직접 사용).

### 2.7 STL 분석 결과 (미완)

사용자가 inmoov.fr 에서 i2 head STL 33개(`~/i2_head_ws/stl/`) 다운로드.
바운딩박스 분석 결과 **프린트용으로 눕혀 흩어진 좌표**(조립 안 됨) → 그대로 로드 시 뒤죽박죽.
`use_meshes=true` 인프라는 완성, **실제 조립은 Blender/Fusion 에서 해야 함** (미완).

---

## 3. AI 두뇌 + 브리지 (`ai_brain/`)

```
ai_brain/
├── brain_core.py      # 파이프라인 (Antigravity 작성, STT→LLM→TTS)
├── mrl_bridge.py      # Python→MRL 표정 브리지 (Claude 작성)
└── requirements.txt
```

### 3.1 파이프라인 (`brain_core.py`)

```
마이크 → recognizer.listen → recognize_google(ko-KR)   # STT (온라인)
      → mock_llm_logic(text)  → {emotion, response}    # LLM (현재 더미!)
      → send_to_mrl(emotion, response)                 # 표정 (브리지)
      → gTTS + pygame 재생                              # TTS (온라인)
```
`mock_llm_logic` 은 키워드 매칭 더미 (예: "안녕"→happy). **실제 API 로 교체 필요.**

### 3.2 브리지 (`mrl_bridge.py` — 핵심)

```python
class MRLBridge:
    def __init__(self, host="localhost", port=8888, timeout=3.0):
        self.base = "http://%s:%d/api/service" % (host, port)

    def exec_python(self, code):
        # MRL REST: 메서드 인자를 JSON 배열 본문으로 → python.exec(code)
        return requests.post("%s/python/exec" % self.base, json=[code], timeout=self.timeout)

    def is_alive(self):
        try: return requests.get("%s/runtime/getVersion" % self.base,
                                 timeout=self.timeout).status_code == 200
        except requests.exceptions.RequestException: return False

    def express_emotion(self, emotion):
        label = (emotion or "neutral").strip()
        # ★ 두 가지 안전장치:
        #   u"..."  → Jython2 에서 한글 안 깨지게 유니코드 리터럴
        #   json.dumps → LLM 출력의 따옴표/역슬래시 이스케이프 (코드 인젝션 방지)
        code = "expressEmotion(u%s)" % json.dumps(label, ensure_ascii=True)
        try:
            self.exec_python(code); return True
        except requests.exceptions.RequestException as e:
            print("[MRL BRIDGE] 표정 전송 실패: %s" % e); return False
```

**코드레벨 포인트:**
- `json.dumps("기쁨")` → `"기쁨"`, 여기에 `u` 접두 → `u"기쁨"` (Jython2 가 유니코드로 해석).
  `u` 없이 넘기면 Jython2 는 `\uXXXX` 를 문자 그대로 취급해 한글 매칭 실패.
- 감정 문자열이 LLM 출력이므로 `json.dumps` 로 이스케이프 → `expressEmotion("); 악성코드"` 같은 인젝션 차단.
- **실 MRL 검증:** `놀람` → jaw 160 / 눈썹 180, happy/sad/anger/surprise 모두 서보 반영.

### 3.3 통합 (brain_core ↔ bridge)

`brain_core.py` 의 버그 수정 (Antigravity 원본에 `setEmotion` 오호출 → 우리 실제 함수는 `expressEmotion`):
```python
# (변경 전)  emotion_url = f".../python/exec/setEmotion('{emotion}')"; requests.get(emotion_url)
# (변경 후)  mrl.express_emotion(emotion)    # mrl = MRLBridge()
```
STT/LLM/TTS 로직은 그대로 두고 **표정 전송 부분만** 브리지로 교체. `requirements.txt` 에 누락된 `requests` 추가.

---

## 4. 구현 현황 요약

| 계층 | 요소 | 상태 |
|------|------|------|
| 두뇌 | STT (Google Web Speech) | ✅ 구현 (온라인) |
| 두뇌 | LLM 판단 | ⚠️ **더미** (실제 API 미설치) |
| 두뇌 | TTS (gTTS) | ✅ 구현 (온라인) |
| 브리지 | Python→MRL 표정 (`mrl_bridge.py`) | ✅ **구현+실검증** |
| 몸통 | MRL 실행 + `expressEmotion` | ✅ 검증 (한/영 7종) |
| 몸통 | 실물 i2 head 서보 | ❌ 미연결 (가상) |
| 시뮬 | ROS2 RViz (`i2_head_sim`) | ✅ 작동 (프리미티브) |
| 시뮬 | Gazebo | ❌ 플러그인 버그로 막힘 |
| 시뮬 | 실제 STL 메시 | ❌ 미조립 |

**핵심 결론:** STT·TTS·브리지·MRL 표정은 모두 작동. **더미 LLM 만 실제 API 로 교체하면
"말 걸면 → 알아듣고 → 판단해 → 표정 짓고 → 대답" 전체 흐름 완성.**

---

## 5. 다음 단계

1. **LLM 실체화 (최우선):** `mock_llm_logic` → 실제 API(Claude/GPT/Gemini). 응답에서 감정 라벨 추출 → `mrl.express_emotion()`.
2. **STT 고도화:** Google Web Speech → 로컬 Whisper (오프라인/속도).
3. **하드웨어 연결:** 실물 i2 head 서보를 MRL 실제 컨트롤러(PCA9685)에 배선 + 캘리브레이션.
4. (선택) STL 조립(Blender) → 시뮬 시각적 완성도.

---

## 부록 A. 실행 방법

**MRL (몸통):**
```bash
~/mrl/start-mrl.sh          # → http://localhost:8888
```
**AI 두뇌:**
```bash
cd ~/i2_head_ws/ai_brain
pip install -r requirements.txt
python3 brain_core.py       # 마이크 대기 → 말하면 표정+대답
python3 mrl_bridge.py 기쁨   # 브리지 단독 테스트
```
**ROS2 시뮬:**
```bash
source /opt/ros/humble/setup.bash && source ~/i2_head_ws/install/setup.bash
ros2 launch i2_head_sim rviz_control.launch.py
ros2 run i2_head_sim expression_publisher demo
```

## 부록 B. 트러블슈팅 로그 (겪은 버그 요약)
| 버그 | 원인 | 해결 |
|------|------|------|
| MRL 설치 hang | 설치기가 wget 출력 안 읽어 파이프 데드락 | `wget -q` 래퍼 + 수동 ivy retrieve |
| emotions.py SyntaxError | 유니코드 exec 에 coding 선언 | 선언 제거 + `unicode_literals` |
| 한글 표정 매칭 실패 | Jython2 byte-str vs unicode | `toText()` + `u"..."` 리터럴 |
| Gazebo controller 무응답 | robot_description 을 CLI param 으로 넘겨 파싱 실패 | mock 하드웨어 + param dict 전달 |
| xacro 메시 안 나옴 | `"true"`→bool 자동변환 | `${use_meshes and ...}` |
| brain_core 표정 안 됨 | `setEmotion` 오호출 | `expressEmotion` (브리지) |
