import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 시간 / 시장 상태 (KST 기준)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_kst_now():
    """GitHub Actions는 UTC로 동작 → KST(UTC+9) 변환"""
    return datetime.now(timezone.utc) + timedelta(hours=9)


def detect_market_status(mode):
    """요일 기반 휴장/회전율 점검일 판단 (KST 기준)"""
    kst = get_kst_now()
    wd = kst.weekday()  # 0=월 ... 6=일
    weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][wd]

    is_holiday = False
    # 한국장 마감 모드: 한국 토(5)·일(6) 휴장
    if mode == "kr" and wd in (5, 6):
        is_holiday = True
    # 미국장 마감 모드(KST 아침): KST 일(6)=미국 토, KST 월(0)=미국 일 → 미국 휴장
    if mode == "us" and wd in (6, 0):
        is_holiday = True

    # 회전율 점검일: 한국장 모드 + 금요일(4) → 주 1회 리마인더
    is_turnover_check = (mode == "kr" and wd == 4)

    return {
        "weekday_kr": weekday_kr,
        "is_holiday": is_holiday,
        "is_turnover_check": is_turnover_check,
        "kst_str": kst.strftime("%Y-%m-%d %H:%M KST")
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌅 미국장 모드 (07:00 KST)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
US_TICKERS = {
    "S&P500": "^GSPC",
    "나스닥": "^IXIC",
    "다우": "^DJI",
    "러셀2000": "^RUT",
    "VIX": "^VIX",
    "미국10년물": "^TNX",
    "미국2년물": "^IRX",
    "DXY": "DX-Y.NYB",
    "USD/KRW": "KRW=X",
    "USD/JPY": "JPY=X",
    "WTI": "CL=F",
    "금": "GC=F",
    "구리": "HG=F",
    "SOXX(반도체)": "SOXX",
    "XLK(빅테크)": "XLK",
    "PAVE(인프라)": "PAVE",
    "ITA(미국방산)": "ITA",
    "EWY(한국)": "EWY",
    "URA(우라늄)": "URA",
    "HYG(하이일드)": "HYG",
    "LQD(투자등급)": "LQD",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🇰🇷 한국장 모드 (16:00 KST)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KR_TICKERS = {
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "USD/KRW": "KRW=X",
    "DXY": "DX-Y.NYB",
    "USD/JPY": "JPY=X",
    "S&P500_선물": "ES=F",
    "나스닥_선물": "NQ=F",
    "WTI": "CL=F",
    "금": "GC=F",
    "KODEX 200": "069500.KS",
    "ACE 글로벌반도체TOP4 Plus": "485540.KS",
    "KODEX 미국AI전력핵심인프라": "487230.KS",
    "KODEX 로봇액티브": "404990.KS",
    "SOL 조선TOP3플러스": "466920.KS",
    "TIGER K방산우주": "449450.KS",
    "HANARO 원자력iSelect": "434730.KS",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚨 7대 트리거 임계치 (계획서 기준선)
#  ※ 이 값은 '전략적 기준선'이며 시점과 무관. 시장 상황 따라 조정 가능
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRIGGER_THRESHOLDS = {
    "VIX": {"warn": 20, "alert": 25, "label": "변동성 지수(VIX)"},
    "USD/JPY": {"warn": 158, "alert": 160, "label": "엔/달러(개입경계 160)"},
    "USD/KRW": {"warn": 1510, "alert": 1520, "label": "원/달러(외국인 유출 1520)"},
    "미국10년물": {"warn": 4.5, "alert": 4.8, "label": "미 10년물"},
    "WTI": {"warn": 90, "alert": 95, "label": "WTI 유가(인플레)"},
}


def fetch_economic_calendar():
    """investing.com 오늘의 주요 경제 지표 (중요도 ★★ 이상)"""
    try:
        url = "https://kr.investing.com/economic-calendar/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        events = []
        rows = soup.find_all('tr', class_='js-event-item')[:30]
        for row in rows:
            try:
                time_cell = row.find('td', class_='time')
                country_cell = row.find('td', class_='flagCur')
                impact_cell = row.find('td', class_='sentiment')
                event_cell = row.find('td', class_='event')
                if not (time_cell and event_cell):
                    continue
                importance = len(impact_cell.find_all('i', class_='grayFullBullishIcon')) if impact_cell else 0
                if importance < 2:
                    continue
                country_text = ""
                if country_cell and country_cell.find('span'):
                    country_text = country_cell.find('span').get('title', '')
                events.append({
                    "time": time_cell.text.strip(),
                    "country": country_text,
                    "event": event_cell.text.strip(),
                    "importance": importance
                })
                if len(events) >= 6:
                    break
            except Exception:
                continue
        return events
    except Exception as e:
        print(f"경제 캘린더 수집 실패: {e}")
        return []


def fetch_korea_supply_demand():
    """네이버 금융 투자자별 매매 동향"""
    try:
        url = "https://finance.naver.com/sise/investorDealTrendDay.naver"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = "euc-kr"
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {}
        tables = soup.find_all('table', class_='type_1')
        if tables:
            rows = tables[0].find_all('tr')[2:6]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    date = cells[0].text.strip()
                    if date:
                        result = {
                            "date": date,
                            "외국인": cells[1].text.strip(),
                            "기관": cells[2].text.strip(),
                            "개인": cells[3].text.strip()
                        }
                        break
        return result
    except Exception as e:
        print(f"한국 수급 수집 실패: {e}")
        return {}


def check_triggers(market_data):
    """7대 트리거 임계치 자동 점검"""
    alerts = []
    for indicator, th in TRIGGER_THRESHOLDS.items():
        if indicator in market_data and isinstance(market_data[indicator], dict):
            value = market_data[indicator].get("close")
            if value is None:
                continue
            if value >= th["alert"]:
                alerts.append(f"🚨 {th['label']}: {value} (경보 {th['alert']} 도달)")
            elif value >= th["warn"]:
                alerts.append(f"⚠️ {th['label']}: {value} (주의 {th['warn']} 근접)")

    # 한미 금리차 (한국 10년물 미수집 → 참고용 추정 제외, 미10년물만 표시)
    # HY-IG 스프레드 (7대 트리거 ⑦)
    if "HYG(하이일드)" in market_data and "LQD(투자등급)" in market_data:
        hyg = market_data["HYG(하이일드)"].get("change_pct", 0)
        lqd = market_data["LQD(투자등급)"].get("change_pct", 0)
        if (hyg - lqd) < -1.0:
            alerts.append(f"🚨 美 HY 스프레드 확대: HY-IG {round(hyg - lqd, 2)}%p (신용위험)")

    return alerts


def collect_market_data(mode="us"):
    """시장 데이터 수집 (mode: 'us' or 'kr')"""

    status = detect_market_status(mode)

    # 휴장이면 데이터 수집 최소화 (대표 지수만 직전 거래일 종가)
    tickers = US_TICKERS if mode == "us" else KR_TICKERS

    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                close = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = (close - prev) / prev * 100
                data[name] = {
                    "close": round(float(close), 2),
                    "change_pct": round(float(change_pct), 2)
                }
        except Exception as e:
            print(f"{name} 수집 실패: {e}")

    # 휴장이 아닐 때만 캘린더·수급·트리거 수집 (휴장일엔 의미 없음)
    if not status["is_holiday"]:
        print("경제 캘린더 수집 중...")
        data["경제캘린더"] = fetch_economic_calendar()
        if mode == "kr":
            print("한국 수급 수집 중...")
            data["한국수급"] = fetch_korea_supply_demand()
        print("7대 트리거 점검 중...")
        data["트리거경보"] = check_triggers(data)
    else:
        data["경제캘린더"] = []
        data["트리거경보"] = []

    data["mode"] = mode
    data["요일"] = status["weekday_kr"]
    data["is_holiday"] = status["is_holiday"]
    data["is_turnover_check"] = status["is_turnover_check"]
    data["timestamp"] = status["kst_str"]
    return data


if __name__ == "__main__":
    import sys, json
    mode = sys.argv[1] if len(sys.argv) > 1 else "us"
    result = collect_market_data(mode)
    print(f"\n=== {mode.upper()} 모드 데이터 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
