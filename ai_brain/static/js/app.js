document.addEventListener('DOMContentLoaded', () => {
    // Views
    const setupView = document.getElementById('setupView');
    const interviewView = document.getElementById('interviewView');
    const resultView = document.getElementById('resultView');
    
    // Status
    const systemStatus = document.getElementById('systemStatus');
    const sttStatus = document.getElementById('sttStatus');
    
    // Inputs & Buttons
    const companySelect = document.getElementById('companySelect');
    const styleSelect = document.getElementById('styleSelect');
    const jobInput = document.getElementById('jobInput');
    const mockSttInput = document.getElementById('mockSttInput');
    
    const startBtn = document.getElementById('startBtn');
    const doneSpeakingBtn = document.getElementById('doneSpeakingBtn');
    const endInterviewBtn = document.getElementById('endInterviewBtn');
    const restartBtn = document.getElementById('restartBtn');
    
    const chatBox = document.getElementById('chatBox');
    const interviewTimer = document.getElementById('interviewTimer');
    
    let timerInterval;
    let secondsElapsed = 0;
    
    // --- Utils ---
    function switchView(viewElement) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        viewElement.classList.add('active');
    }

    function updateStatus(text, type = 'normal') {
        systemStatus.textContent = text;
        if (type === 'thinking') {
            systemStatus.classList.add('thinking');
        } else {
            systemStatus.classList.remove('thinking');
        }
    }

    function formatTime(sec) {
        const m = Math.floor(sec / 60).toString().padStart(2, '0');
        const s = (sec % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    function addMessage(sender, text, emotion = null) {
        const div = document.createElement('div');
        div.classList.add('message');
        
        if (sender === 'AI') {
            div.classList.add('msg-robot');
            let senderHtml = `<span class="sender">🤖 AI 면접관`;
            if (emotion) senderHtml += ` [표정: ${emotion}]`;
            senderHtml += `</span>`;
            div.innerHTML = `${senderHtml}<div class="text">${text}</div>`;
        } else {
            div.classList.add('msg-user');
            div.innerHTML = `<span class="sender">👤 지원자</span><div class="text">${text}</div>`;
        }
        
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Events ---
    startBtn.addEventListener('click', async () => {
        const company = companySelect.options[companySelect.selectedIndex].text;
        const style = styleSelect.options[styleSelect.selectedIndex].text;
        const job = jobInput.value.trim() || "알 수 없음";

        startBtn.textContent = '설정 적용 중...';
        startBtn.disabled = true;

        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company, style, job })
            });
            const data = await res.json();
            
            // UI 변경
            switchView(interviewView);
            updateStatus('🟢 면접 진행 중');
            chatBox.innerHTML = '';
            
            // 타이머 시작
            secondsElapsed = 0;
            interviewTimer.textContent = '00:00';
            timerInterval = setInterval(() => {
                secondsElapsed++;
                interviewTimer.textContent = formatTime(secondsElapsed);
            }, 1000);
            
            // 첫 질문 표시
            addMessage('AI', data.first_question, 'neutral');
            sttStatus.textContent = '🎙️ 마이크가 활성화되었습니다. (답변을 입력하세요)';
            
        } catch (err) {
            alert('서버 연결 실패. Flask 서버가 켜져 있는지 확인하세요.');
        } finally {
            startBtn.textContent = '면접 시작하기';
            startBtn.disabled = false;
        }
    });

    doneSpeakingBtn.addEventListener('click', async () => {
        const userText = mockSttInput.value.trim() || "(침묵)";
        
        // 사용자 답변 화면에 표시
        addMessage('User', userText);
        mockSttInput.value = '';
        
        // 상태 변경 (AI 생각 중)
        updateStatus('🤔 AI 추론 중...', 'thinking');
        sttStatus.textContent = '⏳ AI가 답변을 분석하고 있습니다...';
        doneSpeakingBtn.disabled = true;
        
        try {
            const res = await fetch('/api/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: userText })
            });
            const data = await res.json();
            
            // AI 응답 화면에 표시
            addMessage('AI', data.response, data.emotion);
            
        } catch (err) {
            addMessage('AI', '[서버 에러] 응답을 받을 수 없습니다.', 'error');
        } finally {
            updateStatus('🟢 면접 진행 중');
            sttStatus.textContent = '🎙️ 마이크가 활성화되었습니다. (답변을 입력하세요)';
            doneSpeakingBtn.disabled = false;
        }
    });
    
    // Enter 키로 답변 전송
    mockSttInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !doneSpeakingBtn.disabled) {
            doneSpeakingBtn.click();
        }
    });

    endInterviewBtn.addEventListener('click', async () => {
        if (!confirm('면접을 종료하시겠습니까?')) return;
        
        clearInterval(timerInterval);
        updateStatus('📝 결과 리포트 생성 중...', 'thinking');
        
        try {
            const res = await fetch('/api/end', { method: 'POST' });
            const data = await res.json();
            
            switchView(resultView);
            updateStatus('⚪ 면접 종료');
            document.getElementById('reportBox').innerHTML = `<p>${data.feedback}</p>`;
            
        } catch (err) {
            alert('결과를 불러올 수 없습니다.');
        }
    });

    restartBtn.addEventListener('click', () => {
        switchView(setupView);
        updateStatus('🟢 대기 중');
    });
});
