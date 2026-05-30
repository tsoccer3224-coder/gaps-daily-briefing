import google.generativeai as genai
import os
from dotenv import load_dotenv
from data_collector import collect_market_data

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 팀 컨텍스트 (시점 종속 정보 제거 — 구조적 원칙만)
# ※ 날짜·확률 등 휘발성 정보는 박지 않는다.
#    구체 수치는 매일 수집되는 실제 데이터로 판단.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEAM_CONTEXT = """
[팀 컨텍스트 - 충북대장주]
- 투자철학: '강세장 후기의 거시 전환기 대응 — 핵심-보완 자산 + 양극 집중(barbell)'
- 시장 구조 인식: 반도체 투톱(삼성전자·SK하이닉스)이 코스피를 견인하는 양극화 구조.
  패시브 추종이 아닌 구조적 성장 산업 압축 집중.
- 7개 구조적 성장 산업: 반도체, 로봇, 우주항공, 조선, 방산, 원전·SMR, AI 전력 인프라
- 핵심 ETF: KODEX 200, TIGER 미국S&P500 (지수 베타)
- 보완 ETF: ACE 글로벌반도체TOP4 Plus, KODEX 미국AI전력핵심인프라, KODEX 로봇액티브,
  SOL 조선TOP3플러스, TIGER K방산우주, HANARO 원자력iSelect (섹터 알파)
- 안전자산: KODEX 국고채3년, KIWOOM 국고채10년, ACE KRX 금현물, KODEX 머니마켓액티브
- 명시적 배제: 회사채 미편입(신용 스프레드 확대 위험), 금 외 원자재 직접 미편입
- 7대 트리거(상시 감시): 한은금리 / 미국금리 / 국민연금 자산배분 / 주요 IPO 수급 /
  BOJ금리 / 엔달러 환율 / 美 HY 스프레드 — 구체 수치·일정은 그날 데이터로 판단
- 리스크 한도: VaR 99%(1일) -8%, MDD -15%, 금 4~10%(기준 8%)
- 자산군 비중: 주식 40~60%, 채권 20~40%, 금 4~10%, 현금성 0~10%
"""

# Markdown 안전 지침 (공통)
MD_SAFETY = """
[Markdown 작성 규칙 - 중요]
- 강조는 *별표 한 개*로 굵게, _밑줄_로 이탤릭
- ETF명·종목명·수치는 반드시 백틱(`)으로 감싼다: 예) `TIGER K방산우주` +1.2%
  (종목명의 특수문자가 Markdown과 충돌하는 것을 방지)
- 문단 사이는 빈 줄로 분리
- 표(table) 문법은 쓰지 않는다 (텔레그램 미지원). 불릿(•)으로 나열
"""


def _holiday_prompt(data, mode):
    """휴장일용 짧은 프롬프트"""
    mkt = "한국장" if mode == "kr" else "미국장"
    return f"""당신은 충북대장주팀 GAPS 시황 어시스턴트입니다.
오늘은 {mkt}이 휴장입니다 (데이터의 '요일'·'is_holiday' 참고).
직전 거래일 종가 기준으로 아주 간단한 요약만 작성하세요.

[데이터]
{data}

{MD_SAFETY}

[형식 - 250자 이내]
📴 *{mkt} 휴장* ({{데이터 timestamp의 날짜 MM/DD}}, {data.get('요일')}요일)

• 직전 거래일 종가: (대표 지수 1~2개만)
• 다음 거래일 주목: (있으면 한 줄, 없으면 생략)

📌 _데이터 시점: {data.get('timestamp', '')}_

[규칙] 날짜는 반드시 데이터의 timestamp에서 가져온다. 추측 금지.
"""


def generate_briefing(mode="us"):
    """모드별 시황 생성"""

    data = collect_market_data(mode)

    # 휴장이면 짧은 요약
    if data.get("is_holiday"):
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model.generate_content(_holiday_prompt(data, mode)).text

    # 회전율 점검 리마인더 (금요일 한국장만)
    turnover_note = ""
    if data.get("is_turnover_check"):
        turnover_note = """
🔄 *주간 회전율 점검* (금요일 리마인더)
• 이번 주 매매 회전율이 규정(월 10%↑, 5영업일 80%↑)을 충족하는지 점검 권고
• 미달 시 컷오프 위험 — 다음 주 리밸런싱 계획 확인
"""

    if mode == "us":
        prompt = f"""당신은 DB GAPS 투자대회 참가자(충북대장주팀)를 위한 시장 분석 어시스턴트입니다.
미국장 마감 데이터로 미국장 마감 브리핑을 작성하세요.
지금은 한국시간 오전, 한국장 시작 전입니다.

{TEAM_CONTEXT}

[수집된 데이터]
{data}

{MD_SAFETY}

[필수 형식 - 전체 1500자 이내]

🌅 *미국장 마감 브리핑* ({{데이터 timestamp의 날짜 MM/DD}}, {data.get('요일')}요일)
━━━━━━━━━━━━━

📌 *TL;DR*
• 시장: S&P500/나스닥 종가·등락 한 줄
• 동인: 어젯밤 핵심 키워드
• 한국 영향: 오늘 한국장 시작 시 시사점

📊 *매크로*
1. 지수: S&P500, 나스닥, 다우, 러셀2000
2. 변동성: VIX (평온<12 / 정상12~20 / 경계20~30 / 공포>30)
3. 금리: 미10년·2년물
4. 환율: DXY, USD/KRW, USD/JPY
5. 원자재: WTI, 금, 구리

📈 *팀 보유 ETF 선행 지표*
• SOXX → 반도체(ACE 글로벌반도체TOP4·삼전·하닉)
• XLK·PAVE → AI전력(KODEX 미국AI전력핵심인프라)
• ITA → 방산(TIGER K방산우주)
• EWY → 외국인 한국 수급 게이지
• URA → 원전(HANARO 원자력iSelect)

🚨 *7대 트리거 점검*
[데이터 '트리거경보' 그대로. 비어있으면 "🟢 모든 트리거 정상 범위"]

📅 *오늘의 매크로 이벤트*
[데이터 '경제캘린더' 사용. 시간·국가·이벤트. 비어있으면 "주요 발표 없음"]

🎯 *오늘 한국장 운용 시사점*
• 위험자산 비중(한도 70%): ↑/유지/↓ + 이유
• 주목 ETF: 강세/약세 후보
• 매매 전략 한 줄
{turnover_note}
📌 _데이터 시점: {data.get('timestamp', '')}_

[규칙]
- 날짜는 반드시 데이터 timestamp에서 가져온다 (추측 금지)
- 데이터에 있는 수치만 사용, 없으면 ❓
- 회사채 미편입·핵심보완 구조 일관성 유지
- 트리거경보 있으면 상단 TL;DR에도 언급
"""
    else:  # kr
        prompt = f"""당신은 DB GAPS 투자대회 참가자(충북대장주팀)를 위한 시장 분석 어시스턴트입니다.
한국장 마감 데이터로 한국장 마감 브리핑을 작성하세요.
지금은 한국시간 오후, 한국장 마감 직후이며 미국장 시작까지 시간이 남았습니다.

{TEAM_CONTEXT}

[수집된 데이터]
{data}

{MD_SAFETY}

[필수 형식 - 전체 1600자 이내]

🇰🇷 *한국장 마감 브리핑* ({{데이터 timestamp의 날짜 MM/DD}}, {data.get('요일')}요일)
━━━━━━━━━━━━━

📌 *TL;DR*
• 시장: 코스피/코스닥 종가·등락
• 동인: 오늘 한국 시장 핵심 키워드
• 미국 변수: 오늘밤 미국장 주목 포인트

📊 *한국 시장*
1. 지수: 코스피, 코스닥
2. 반도체 투톱: 삼성전자, SK하이닉스 (코스피 견인 구조)
3. 환율: USD/KRW, USD/JPY

🌍 *수급 동향*
[데이터 '한국수급' 사용. 외국인/기관/개인 + 한 줄 해석. 없으면 생략]

📈 *팀 보유 ETF 일일 성과*
• `KODEX 200`
• `ACE 글로벌반도체TOP4 Plus`
• `KODEX 미국AI전력핵심인프라`
• `KODEX 로봇액티브`
• `SOL 조선TOP3플러스`
• `TIGER K방산우주`
• `HANARO 원자력iSelect`
→ 오늘 *강세 TOP3* / *약세 TOP3*

🚨 *7대 트리거 점검*
[데이터 '트리거경보' 그대로. 비어있으면 "🟢 모든 트리거 정상 범위"]

📅 *오늘의 매크로 이벤트*
[데이터 '경제캘린더' 사용. 비어있으면 "주요 발표 없음"]

🌙 *오늘밤 미국장 프리뷰*
• S&P500·나스닥 선물 동향
• 한국 보유 자산 영향 가능성

🎯 *운용 시사점*
• 양극 집중도(반도체 투톱 의존) 점검
• 위험/안전자산 비중 점검
• 다음 매매 고려사항 1~2가지
{turnover_note}
📌 _데이터 시점: {data.get('timestamp', '')}_

[규칙]
- 날짜는 반드시 데이터 timestamp에서 가져온다 (추측 금지)
- 데이터에 있는 수치만 사용, 없으면 ❓
- 회사채 미편입·핵심보완 구조 일관성 유지
- 트리거경보 있으면 상단 TL;DR에도 언급
"""

    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(prompt).text


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "us"
    print(f"{mode.upper()} 모드 시황 생성 중...\n")
    print("=" * 40)
    print(generate_briefing(mode))
    print("=" * 40)
