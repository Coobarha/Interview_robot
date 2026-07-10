import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- 메인 페이지 ---
@app.route("/")
def index():
    return render_template("index.html")

# --- MOCK API 엔드포인트 ---

@app.route("/api/start", methods=["POST"])
def start_interview():
    """면접 시작 시 초기화 및 설정 정보를 받는 엔드포인트 (Mock)"""
    data = request.json
    company = data.get("company", "알 수 없음")
    style = data.get("style", "알 수 없음")
    job = data.get("job", "알 수 없음")
    
    print(f"\n[Web UI] 면접 시작 요청 수신:")
    print(f"  - 기업: {company}")
    print(f"  - 성향: {style}")
    print(f"  - 직무: {job}")
    
    # 딜레이를 주어 실제 로딩하는 것처럼 연출
    time.sleep(1)
    
    return jsonify({
        "status": "success",
        "message": f"{company} {job} 면접을 시작합니다.",
        "first_question": "안녕하십니까. 먼저 간단한 자기소개 부탁드립니다."
    })

@app.route("/api/answer", methods=["POST"])
def process_answer():
    """사용자 답변 완료 시 호출되는 엔드포인트 (Mock)"""
    data = request.json
    user_text = data.get("text", "")
    
    print(f"\n[Web UI] 사용자 답변 수신: {user_text}")
    print(f"[Web UI] AI (Mock) 추론 중...")
    
    # 실제 환경에서는 이 부분에 LLM 처리 및 MRL 전송 코드가 들어갑니다.
    time.sleep(2)  # LLM이 생각하는 것처럼 2초 대기
    
    # 임의의 응답 생성 로직 (나중에 실제 LLM으로 교체)
    mock_responses = [
        {"emotion": "neutral", "response": "그렇군요. 그럼 다음 질문입니다. 본인의 가장 큰 장점은 무엇인가요?"},
        {"emotion": "surprise", "response": "오, 흥미로운 경험이네요. 그 과정에서 가장 큰 어려움은 뭐였나요?"},
        {"emotion": "disgust", "response": "그 방식은 효율적이지 않아 보이는데요. 다른 대안은 없었나요?"},
        {"emotion": "happy", "response": "아주 좋습니다. 저희 기업 인재상과 잘 맞으시는 것 같네요. 마지막으로 궁금한 점 있나요?"}
    ]
    
    import random
    result = random.choice(mock_responses)
    
    print(f"  -> 결과 감정: {result['emotion']}")
    print(f"  -> 결과 대답: {result['response']}")
    
    return jsonify({
        "status": "success",
        "emotion": result["emotion"],
        "response": result["response"]
    })

@app.route("/api/end", methods=["POST"])
def end_interview():
    """면접 종료 시 피드백 리포트를 생성하는 엔드포인트 (Mock)"""
    time.sleep(2)
    return jsonify({
        "status": "success",
        "feedback": "전반적으로 논리적인 답변이 돋보였습니다. 다만, 기술적인 깊이를 묻는 질문에서 다소 당황하는 기색이 보였습니다. 회사 인재상인 '주도성'을 강조한 점은 훌륭합니다."
    })

if __name__ == "__main__":
    print("========================================")
    print("AI 모의 면접 웹 서버 (Mock Mode) 시작")
    print("웹 브라우저에서 http://127.0.0.1:5000 으로 접속하세요.")
    print("========================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
