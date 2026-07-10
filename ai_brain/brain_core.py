#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Brain Core (Plan B)
마이크 입력 (STT) -> AI 판단 (LLM Mock) -> 음성 및 표정 출력 (TTS & MRL Bridge)
"""

import os
import sys
import time
import urllib.parse
from ctypes import *

# ALSA 에러 완전 차단을 위한 C 라이브러리 핸들러 덮어쓰기
# (import pyaudio/pygame 이전에 실행되어야 함)
def py_error_handler(filename, line, function, err, fmt):
    pass
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
try:
    asound = cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except OSError:
    pass

import speech_recognition as sr
import pygame
import requests
from gtts import gTTS
from mrl_bridge import send_to_mrl  # Python->MRL 표정 브리지 헬퍼 함수

# 임시 AI 모델 (나중에 실제 OpenAI나 Gemini API로 교체될 부분)
def mock_llm_logic(user_text):
    print("[AI Think] 텍스트를 분석 중입니다...")
    time.sleep(1) # 인공지능이 생각하는 것처럼 딜레이 부여
    
    user_text = user_text.lower()
    
    # 텍스트에 포함된 단어에 따라 더미 반응을 생성합니다
    if "안녕" in user_text:
        return {"emotion": "happy", "response": "안녕하세요! 만나서 정말 반가워요."}
    elif "슬퍼" in user_text or "우울" in user_text:
        return {"emotion": "sad", "response": "저런, 기운 내세요. 제가 위로해 드릴게요."}
    elif "화나" in user_text or "짜증" in user_text:
        return {"emotion": "anger", "response": "정말 화가 나시겠군요. 진정하세요."}
    elif "놀래" in user_text or "깜짝" in user_text:
        return {"emotion": "surprise", "response": "앗! 저도 깜짝 놀랐네요!"}
    else:
        return {"emotion": "neutral", "response": "그렇군요. 제가 어떻게 도와드릴까요?"}

def main():
    # 1. 초기화
    recognizer = sr.Recognizer()
    pygame.mixer.init()
    
    print("========================================")
    print("AI Brain 파이프라인 시작 (음성 대기 모드)")
    print("마이크에 대고 말씀해 주세요 (종료하려면 Ctrl+C)")
    print("========================================")

    # 마이크 객체 생성
    mic = sr.Microphone()

    while True:
        try:
            with mic as source:
                # 배경 소음에 맞게 마이크 조정
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("\n[STT] 듣고 있습니다...")
                
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("[STT] 음성 인식 중...")
            # Google Web Speech API 사용 (무료, 인터넷 연결 필요)
            user_text = recognizer.recognize_google(audio, language="ko-KR")
            print(f"> 사용자: {user_text}")
            
            # 2. AI 판단 (LLM)
            ai_result = mock_llm_logic(user_text)
            emotion = ai_result["emotion"]
            response_text = ai_result["response"]
            
            print(f"> AI 대답: {response_text} (감정: {emotion})")
            
            # 3. 하드웨어(MRL)로 전송
            send_to_mrl(emotion, response_text)
            
            # 4. 파이썬 쪽에서 음성 출력 (TTS) - MRL 입을 쓰지 않을 경우
            print("[TTS] 파이썬에서 음성 합성 중...")
            tts = gTTS(text=response_text, lang="ko")
            tts_file = "temp_response.mp3"
            tts.save(tts_file)
            
            pygame.mixer.music.load(tts_file)
            pygame.mixer.music.play()
            
            # 오디오 재생이 끝날 때까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # 임시 파일 삭제
            if os.path.exists(tts_file):
                os.remove(tts_file)
                
        except sr.WaitTimeoutError:
            # 입력이 없을 때 조용히 다시 루프 시작
            continue
        except sr.UnknownValueError:
            print("[STT Error] 무슨 말씀이신지 잘 알아듣지 못했어요.")
        except sr.RequestError as e:
            print(f"[STT Error] 구글 API 요청 에러: {e}")
        except KeyboardInterrupt:
            print("\n종료합니다.")
            break
        except Exception as e:
            print(f"[Error] 알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    main()
