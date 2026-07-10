# MRL (MyRobotLab) 세팅 가이드 — 처음부터

AI 브릿지(`mrl_bridge.py`)가 동작하려면 MRL 이 실행 중이고 `expressEmotion(label)` 이 호출 가능한
상태여야 한다. 이 문서는 **MRL 이 아예 없는 상태**에서 그 상태까지 만드는 전체 절차다.

> 요약 흐름: JDK 설치 → MRL 다운로드/설치 → `emotions.py` 복사 → InMoov2(i01)+head 시작
> → (실물 없으면) 가상 아두이노 연결 → `expressEmotion` 검증

---

## 0. 사전 요구사항
- **Java JDK 17** (MRL Nixie 는 Java 11+ 필요, 17 권장)
- 인터넷 (MRL 최초 설치 시 라이브러리 다운로드)
- 디스크 여유 ~3GB

### JDK 17 설치
```bash
# (A) 시스템 설치 (sudo 가능할 때)
sudo apt install -y openjdk-17-jdk

# (B) sudo 불가 시 — 휴대용 JDK 를 폴더에 풀어서 사용
cd ~/mrl
wget -O jdk17.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse"
tar xzf jdk17.tar.gz          # -> jdk-17.x.x+xx/
```

---

## 1. MRL 다운로드 & 설치
```bash
mkdir -p ~/mrl && cd ~/mrl
wget https://myrobotlab-repo.s3.us-east-1.amazonaws.com/myrobotlab.zip
unzip myrobotlab.zip          # -> myrobotlab-1.1.XXXX/
cd myrobotlab-1.1.*

# 휴대용 JDK 를 쓰는 경우: MRL 이 자동 인식하도록 심볼릭 링크
ln -sfn ../jdk-17.*  java
```

### ⚠️ 설치 hang(데드락) 주의
MRL 최초 실행은 `--install` 로 라이브러리를 받는데, 내부 설치기가 `wget` 진행률 출력을 읽지 않아
**파이프 버퍼가 차면 멈추는** 알려진 버그가 있다. 우회책:

```bash
# (1) 조용한 wget 래퍼를 PATH 앞에 두기 (출력 억제 → 데드락 방지)
mkdir -p bin
printf '#!/usr/bin/env bash\nexec /usr/bin/wget -q "$@"\n' > bin/wget && chmod +x bin/wget
export PATH="$PWD/bin:$PWD/java/bin:$PATH"

# (2) 실행 (최초 1회는 설치 때문에 오래 걸림)
./myrobotlab.sh
```
> 그래도 멈추면: `libraries/repo.json` 이 안 생겼는지 확인 후, `./myrobotlab.sh --install` 를 다시 실행.
> 브라우저가 자동으로 안 뜨면 **http://localhost:8888** 로 접속.

설치가 끝나면 `libraries/repo.json` 이 생기고, 이후 실행은 설치 단계를 건너뛴다.

---

## 2. 커스텀 `emotions.py` 복사
감정 라벨(한/영) → 표정 gesture 매핑 스크립트를 MRL gestures 폴더에 넣는다.
```bash
# 이 저장소 루트에서
cp mrl_setup/emotions.py ~/mrl/myrobotlab-1.1.*/resource/InMoov2/gestures/
```
> 이미 MRL 이 실행 중이면 MRL 안에서 `i01.loadGestures()` 로 리로드. 정상 로드 시 `... Gestures loaded, 0 error`.

---

## 3. InMoov2(i01) + head 시작

### 방법 A — 웹 UI
1. http://localhost:8888 접속 → Intro 탭 → InMoov 로고 → InMoov2 시작
2. 머리(head)까지 시작되었는지 확인

### 방법 B — 웹 API (스크립트, 재현성 good)
```bash
API=http://localhost:8888/api/service
curl -s "$API/runtime/start/%22i01%22/%22InMoov2%22"     # i01 시작
curl -s "$API/i01/startPeer/%22head%22"                  # 머리 시작
```

> **주의:** 기본 config 는 표정 서보(눈썹·볼 등)가 `autoStart:false` 라 안 뜬다.
> 전부 켜려면 `data/config/default/i01.head.yml` 의 `autoStart: false` → `true` 로 바꾼 뒤 head 시작.
> (이 저장소 `mrl_setup/config_backup/` 에 우리가 켜둔 head 서보 + 가상아두이노(va) config 백업이 있음 — 4번 참고.)

---

## 4. (실물 하드웨어가 없을 때) 가상 아두이노 연결

기본 config 는 서보의 `controller/pin` 이 `null` 이라 명령을 보내도 안 움직인다.
가상 모드로 표정을 **화면상 검증**하려면 가상 아두이노(VirtualArduino)를 만들어 서보를 붙인다.

```bash
API=http://localhost:8888/api/service
curl -s "$API/runtime/setAllVirtual/true"                # 이후 시작 서비스는 가상으로
curl -s "$API/runtime/start/%22va%22/%22VirtualArduino%22"
# 표정 서보들을 va 에 attach (핀 번호는 임의)
for s in eyebrowLeft eyebrowRight cheekLeft cheekRight jaw \
         eyelidLeftUpper eyelidRightUpper upperLip forheadLeft forheadRight; do
  curl -s "$API/va/attach/%22i01.head.$s%22/2" >/dev/null
done
```
> **실물 i2 head 를 붙일 때는** va 대신 실제 컨트롤러(예: PCA9685/Arduino)를 시작하고 각 서보에
> `controller`/`pin` 을 배정한다 (= 하드웨어 캘리브레이션). `config_backup/` 의 YAML 을
> `data/config/default/` 로 복사하면 우리가 맞춰둔 head 서보 설정을 재사용할 수 있다.

---

## 5. 검증
```bash
# 표정 실행 (한글/영문 모두 OK)
curl -s -X POST http://localhost:8888/api/service/python/exec \
  -H "Content-Type: application/json" -d '["expressEmotion(u\"놀람\")"]'
# 턱 서보 위치 확인 (놀람이면 160 근처로 벌어짐)
curl -s "http://localhost:8888/api/service/i01.head.jaw/getCurrentInputPos"
```
또는 이 저장소의 브릿지로:
```bash
cd ai_brain && python3 mrl_bridge.py 놀람
```

정상이면 이제 `brain_core.py` 를 실행할 준비 완료.

---

## config_backup/ 이란?
`mrl_setup/config_backup/` = 우리가 세팅한 MRL head 서보 config + 가상아두이노(va) config 백업.
`data/config/default/` 에 복사하면 표정 서보 autoStart + va 연결 상태를 그대로 재현할 수 있다.
(실물 하드웨어를 붙이면 각 서보의 controller/pin 을 실제 값으로 바꿔야 함.)
