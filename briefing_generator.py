import google.generativeai as genai
import os
from dotenv import load_dotenv
from data_collector import collect_market_data

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def clean_data(data):
    """numpy 숫자를 일반 숫자로 변환"""
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 팀 컨텍스트 (충북대장주 투자계획서 기준)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEAM_CONTEXT = """
[팀 컨텍스트 - 충북대장주]
- 투자철학: '강세장 후기의 거시 환경 전환기 대응 — 핵심-보완 자산 + 양극 집중(barbell)'
- 7개 구조적 성장 산업: 반도체, 로봇, 우주항공, 조선, 방산, 원전·SMR, AI 전력 인프라
- 매수 ETF: KODEX 200, TIGER 미국S&P500, ACE 글로벌반도체TOP4 Plus,
  KODEX 미국AI전력핵심인프라, KODEX 로봇액티브, SOL 조선TOP3플러스,
  TIGER K방산&우주, HANARO 원자력iSelect, KODEX 국고채3년, KIWOOM 국고채10년,
  ACE KRX 금현물, KODEX 머니마켓액티브
- 회사채 미편입 전략 (신용 스프레드 확대 위험)
- 7대 트리거: 한은금리 / 미국금리 / 국민연금 자산배분 / SPCX IPO / BOJ금리 / 엔달러 / 美HY스프레드
- 리스크 한도: VaR 99% -8%, MDD -15%
- 자산군 비중: 주식 40~60%, 채권 20~40%, 금 4~10%(기준 8%), 현금성 0~10%(기준 7%)
"""


def generate_briefing(mode="us"):
    """모드별 시황 생성 (mode: 'us' or 'kr')"""

    data = collect_market_data(mode)
    data = clean_data(data)

    if mode == "us":
        prompt = f"""당신은 DB GAPS 글로벌 자산배분 투자대회 참가자(충북대장주팀)를 위한
시장 분석 어시스턴트입니다. 미국장 마감 데이터를 바탕으로 미국장 마감 브리핑을 작성해주세요.
지금은 한국시간 오전 7시, 한국장 시작(9시) 2시간 전입니다.

{TEAM_CONTEXT}

[수집된 미국 시장 데이터]
{data}

[작성 형식 - 700~1100자]

🌅 미국장 마감 브리핑 ({{날짜}})

■ TL;DR (3줄)
- 시장: S&P500/나스닥 종가·등락 한 줄
- 동인: 어젯밤 시장 핵심 키워드 (예: 빅테크 강세, 금리 상승 부담 등)
- 한국 영향: 오늘 한국장 시작 시 핵심 시사점

■ 매크로 (간결하게)
1. 지수: S&P500, 나스닥, 다우, 러셀2000 등락
2. 변동성: VIX 수준 해석 (12↓평온 / 12~20정상 / 20~30경계 / 30↑공포)
3. 금리: 미 10년·2년물, 한미 금리차 (현재 -1.0~1.25%p 역전)
4. 환율: DXY, USD/KRW, USD/JPY (160엔 개입경계, 1,520원 외국인 유출경계)
5. 원자재: WTI(미·이란 사태 모니터링), 금, 구리

■ 팀 보유 ETF 선행 지표 분석
- SOXX → ACE 글로벌반도체TOP4 Plus / 반도체 투톱 (삼전·하닉) 시사점
- XLK / PAVE → KODEX 미국AI전력핵심인프라 시사점
- ITA → TIGER K방산&우주 글로벌 동향
- EWY → 외국인 한국 수급 게이지
- URA → HANARO 원자력iSelect 시사점

■ 오늘 한국장 운용 시사점 (3~4줄)
- 위험자산 비중 (현재 한도 70%): ↑ / 유지 / ↓
- 7대 트리거 중 오늘 활성화된 변수 (있다면)
- 한국장 매매 전략 한 줄 (예: 반도체 비중 유지, 방산 관망 등)

[작성 규칙]
- 한국어로 작성, 모바일 가독성 우선
- 데이터에 있는 수치만 사용, 추측 금지
- 추측은 ❓로 표시
- 마지막에 데이터 시점 명시
- 회사채 미편입·핵심-보완 구조 일관성 유지
"""
    else:  # kr 모드
        prompt = f"""당신은 DB GAPS 글로벌 자산배분 투자대회 참가자(충북대장주팀)를 위한
시장 분석 어시스턴트입니다. 한국장 마감 데이터를 바탕으로 한국장 마감 브리핑을 작성해주세요.
지금은 한국시간 오후 4시, 한국장 마감(15:30) 직후이며 미국장 시작(22:30)까지 6시간 남았습니다.

{TEAM_CONTEXT}

[수집된 한국 시장 데이터]
{data}

[작성 형식 - 800~1200자]

🇰🇷 한국장 마감 브리핑 ({{날짜}})

■ TL;DR (3줄)
- 시장: 코스피/코스닥 종가·등락
- 동인: 오늘 한국 시장 핵심 키워드
- 미국 변수: 오늘밤 미국장 핵심 주목 포인트

■ 한국 시장 요약
1. 지수: 코스피(7,844 고점·반도체 투톱 견인 컨텍스트), 코스닥
2. 반도체 투톱: 삼성전자, SK하이닉스 (코스피 영업이익 69% 비중)
3. 환율: USD/KRW (1,510원대·1,520원 외국인 유출경계), DXY, USD/JPY (160엔 개입경계)

■ 팀 보유 ETF 일일 성과 (★ 핵심)
- KODEX 200: 등락·코멘트
- ACE 글로벌반도체TOP4 Plus: 등락·코멘트 (반도체 슈퍼사이클)
- KODEX 미국AI전력핵심인프라: 등락·코멘트
- KODEX 로봇액티브: 등락·코멘트
- SOL 조선TOP3플러스: 등락·코멘트
- TIGER K방산&우주: 등락·코멘트
- HANARO 원자력iSelect: 등락·코멘트

→ 오늘 강세 ETF / 약세 ETF 한 줄 요약

■ 오늘밤 미국장 프리뷰
- S&P500·나스닥 선물 동향으로 본 위험심리
- 한국 보유 자산 영향 가능성
- 7대 트리거 점검 (오늘 활성화 변수 있다면)

■ 운용 시사점 (3~4줄)
- 양극 집중 전략 관점 점검 (반도체 투톱 의존도)
- 위험자산/안전자산 비중 점검 (한도 70% / 100%)
- 다음 매매 결정 시 고려할 1~2가지

[작성 규칙]
- 한국어로 작성, 모바일 가독성 우선
- 데이터에 있는 수치만 사용, 추측 금지
- 추측은 ❓로 표시
- 마지막에 데이터 시점 명시
- 회사채 미편입·핵심-보완 구조 일관성 유지
"""

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "us"
    print(f"{mode.upper()} 모드 시황 생성 중...\n")
    briefing = generate_briefing(mode)
    print("=" * 40)
    print(briefing)
    print("=" * 40)
