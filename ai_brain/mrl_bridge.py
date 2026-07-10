#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL Bridge (Plan B) — Python 두뇌 -> MRL(MyRobotLab) 하드웨어 연동

역할: AI 두뇌가 도출한 '감정 텍스트'를 MRL 로 보내 InMoov2 i2 head 의 표정을 실행.
MRL 쪽 진입점: resource/InMoov2/gestures/emotions.py 의 expressEmotion(label)
  - 한글/영문 감정 라벨 모두 매핑 (기쁨/happy/화남/anger/놀람/surprise ...), 모르는 라벨은 neutral

주의(중요):
  - MRL 은 Jython(파이썬2) 라서 한글을 유니코드 리터럴 u"..." 로 넘겨야 안 깨짐.
  - 감정 문자열은 LLM 출력이므로 json.dumps 로 이스케이프해 코드 인젝션을 막는다.
"""

import json
import sys
import requests


class MRLBridge:
    def __init__(self, host="localhost", port=8888, timeout=3.0):
        self.base = "http://%s:%d/api/service" % (host, port)
        self.timeout = timeout

    # --- 저수준: MRL python 서비스에서 임의 파이썬 코드 실행 ---
    def exec_python(self, code):
        url = "%s/python/exec" % self.base
        # MRL REST: 메서드 인자를 JSON 배열 본문으로 전달 -> exec(code)
        r = requests.post(url, json=[code], timeout=self.timeout)
        r.raise_for_status()
        return r

    # --- MRL 살아있는지 ---
    def is_alive(self):
        try:
            r = requests.get("%s/runtime/getVersion" % self.base, timeout=self.timeout)
            return r.status_code == 200
        except requests.exceptions.RequestException:
            return False

    # --- 감정 -> 표정 실행 ---
    def express_emotion(self, emotion):
        """감정 라벨(한글/영문)을 MRL expressEmotion 으로 실행. 성공 여부(bool) 반환."""
        label = (emotion or "neutral").strip()
        # u"..." 유니코드 리터럴 + json 이스케이프 (한글 안깨짐 + 인젝션 방지)
        code = "expressEmotion(u%s)" % json.dumps(label, ensure_ascii=True)
        try:
            self.exec_python(code)
            return True
        except requests.exceptions.RequestException as e:
            print("[MRL BRIDGE] 표정 전송 실패: %s" % e)
            return False

    # --- (옵션) MRL 내장 스피커로 발화. Plan B 는 기본적으로 Python TTS 사용이라 off ---
    def speak(self, text):
        code = "i01.mouth.speak(u%s)" % json.dumps(text or "", ensure_ascii=True)
        try:
            self.exec_python(code)
            return True
        except requests.exceptions.RequestException:
            return False


# 기본 브리지 인스턴스 (brain_core 에서 그대로 import 해서 쓰기 편하게)
_bridge = MRLBridge()


def send_to_mrl(emotion, speech_text="", speak_via_mrl=False):
    """brain_core 호환 진입점. 감정을 MRL 로 전송(표정 실행). speech 는 로그용.
    speak_via_mrl=True 면 MRL 스피커로도 발화(기본 off — Python 이 TTS 담당)."""
    print("\n[MRL BRIDGE] MRL 로 전송 -> 표정: %s | 대사: %s" % (emotion, speech_text))
    if not _bridge.is_alive():
        print("[MRL BRIDGE] MRL(localhost:8888) 응답 없음. MRL 이 켜져 있는지 확인하세요.")
        return False
    ok = _bridge.express_emotion(emotion)
    if speak_via_mrl and speech_text:
        _bridge.speak(speech_text)
    print("[MRL BRIDGE] 전송 %s" % ("완료" if ok else "실패"))
    print("-" * 40)
    return ok


if __name__ == "__main__":
    # 테스트: python3 mrl_bridge.py 기쁨
    emo = sys.argv[1] if len(sys.argv) > 1 else "기쁨"
    b = MRLBridge()
    print("MRL alive:", b.is_alive())
    print("express_emotion(%r):" % emo, b.express_emotion(emo))
