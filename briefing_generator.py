import google.generativeai as genai
import os
from dotenv import load_dotenv
from data_collector import collect_market_data

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def clean_data(data):
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, dict):
            cleaned[key] = {
                "close": float(value["close"]),
                "change_pct": float(value["change_pct"])
            }
        else:
            cleaned[key] = value
    return cleaned


def generate_briefing():
    data = collect_market_data()
    data = clean_data(data)

    prompt = f"""당신은 DB GAPS 글로벌 자산배분 투자대회 참가자를 위한 시장 분석 어시스턴트입니다.
아래 시장 데이터를 바탕으로 일일 시황 브리핑을 작성해주세요.

[수집된 시장 데이터]
{data}

[작성 형식]
■ TL;DR (3줄)
- 시장: S&P500/코스피 종가·등락
- 동인: 오늘 시장 움직인 핵심 키워드
- 변수: 다음 거래일 주목 포인트

■ 본문
1. 지수 (S&P500, 나스닥, 코스피, 코스닥)
2. 금리 (미국 10년물)
3. 환율 (USD/KRW, DXY, USD/JPY)
4. 변동성·원자재 (VIX, WTI, 금)
5. ETF 매핑 코멘트 (위험자산/안전자산 시사점 2~3줄)

[작성 규칙]
- 모바일 가독성 우선, 600~900자
- 한국어로 작성
- 데이터에 있는 수치만 사용, 추측 금지
- 마지막에 데이터 시점 명시
"""

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    print("시황 생성 중... (30초~1분 소요)\n")
    briefing = generate_briefing()
    print("=" * 40)
    print(briefing)
    print("=" * 40)
