from __future__ import unicode_literals   # 이 파일의 문자열 리터럴을 모두 unicode 로 (한글 매칭 안정화)
# 주의: InMoov2 는 이 파일을 '유니코드 문자열'로 읽어 exec 하므로
#       '# -*- coding: utf-8 -*-' 선언을 넣으면 안 됨(SyntaxError). unicode_literals 로 한글 처리.
###///EMOTION DISPATCHER — GPT 감정 라벨 -> 표정 매핑 (Phase 5 bridge)///###
#
#  목적: GPT(또는 감정 분류기)가 내놓는 감정 단어를 받아서
#        faceExpressions.py 에 이미 정의된 표정 함수를 자동으로 실행한다.
#
#  사용 예:
#     expressEmotion("joy")     -> happy()  실행
#     expressEmotion("기쁨")     -> happy()  실행
#     expressEmotion("anger")   -> anger()  실행
#     expressEmotion("weird!!") -> 매핑 없으면 neutral()
#
#  모든 gesture 는 하나의 전역 네임스페이스를 공유하므로(InMoov2.py 참조)
#  여기서 happy()/sad()/anger()/surprise() 등을 이름으로 바로 호출할 수 있다.

# 감정 라벨(영문 소문자 / 한글) -> faceExpressions.py 의 표정 함수 이름
emotionMap = {
    # --- 기쁨 ---
    "happy": "happy", "happiness": "happy", "joy": "happy", "joyful": "happy",
    "glad": "happy", "excited": "happy", "excitement": "happy", "pleased": "happy",
    "기쁨": "happy", "기쁜": "happy", "행복": "happy", "행복함": "happy", "즐거움": "happy",
    # --- 미소(가벼운 기쁨) ---
    "smile": "smile", "content": "smile", "amused": "smile", "미소": "smile", "만족": "smile",
    # --- 슬픔 ---
    "sad": "sad", "sadness": "sad", "unhappy": "sad", "sorrow": "sad", "down": "sad",
    "disappointed": "sad", "슬픔": "sad", "슬픈": "sad", "우울": "sad", "실망": "sad",
    # --- 화남 ---
    "angry": "anger", "anger": "anger", "mad": "anger", "furious": "anger",
    "annoyed": "anger", "irritated": "anger", "화남": "anger", "화": "anger",
    "분노": "anger", "짜증": "anger",
    # --- 놀람 ---
    "surprise": "surprise", "surprised": "surprise", "shock": "surprise",
    "shocked": "surprise", "astonished": "surprise", "wow": "surprise",
    "놀람": "surprise", "놀란": "surprise", "충격": "surprise",
    # --- 두려움 ---
    "fear": "fear", "afraid": "fear", "scared": "fear", "anxious": "fear",
    "worried": "fear", "공포": "fear", "두려움": "fear", "무서움": "fear", "불안": "fear",
    # --- 혐오 ---
    "disgust": "disgust", "disgusted": "disgust", "gross": "disgust",
    "혐오": "disgust", "역겨움": "disgust",
    # --- 생각중 ---
    "thinking": "thinking", "thoughtful": "thinking", "curious": "thinking",
    "생각": "thinking", "고민": "thinking", "궁금": "thinking",
    # --- 중립/평온 ---
    "neutral": "neutral", "calm": "neutral", "ok": "neutral", "fine": "neutral",
    "중립": "neutral", "평온": "neutral", "보통": "neutral",
}

# 매핑에 없는 감정이 들어왔을 때 실행할 기본 표정
emotionDefault = "neutral"


def toText(label):
    """어떤 형태(byte-str/unicode/None)로 들어오든 안전하게 unicode 로 변환.
    Jython2 에서 str(u'한글') 은 터지므로 직접 처리한다."""
    if label is None:
        return u""
    if isinstance(label, bytes):
        try:
            return label.decode("utf-8")
        except Exception:
            return label.decode("utf-8", "ignore")
    try:
        return u"%s" % label
    except Exception:
        return u""


def resolveEmotion(label):
    """감정 라벨을 표정 함수 이름으로 변환. 못 찾으면 emotionDefault 반환."""
    key = toText(label).strip()
    if not key:
        return emotionDefault
    # 영문은 대소문자 무시, 한글은 lower() 영향 없음
    return emotionMap.get(key.lower(), emotionMap.get(key, emotionDefault))


def expressEmotion(label):
    """감정 라벨을 받아 해당 표정 gesture 를 실행한다. (Phase 5 진입점)"""
    labelText = toText(label)
    fnName = resolveEmotion(labelText)
    fn = globals().get(fnName)
    if fn is None or not callable(fn):
        print(u"expressEmotion: 표정 함수 '%s' 를 찾을 수 없음 (faceExpressions.py 로드 확인)" % fnName)
        return None
    print(u"expressEmotion: '%s' -> %s()" % (labelText, fnName))
    fn()
    return fnName
