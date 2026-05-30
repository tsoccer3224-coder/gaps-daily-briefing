import yfinance as yf
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🌅 미국장 모드 (07:00 KST)
# - 미국 시장 매크로 + 팀 보유 ETF 선행 지표
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
US_TICKERS = {
    # 미국 지수
    "S&P500": "^GSPC",
    "나스닥": "^IXIC",
    "다우": "^DJI",
    "러셀2000": "^RUT",
    "VIX": "^VIX",

    # 미국 금리
    "미국10년물": "^TNX",
    "미국2년물": "^IRX",

    # 환율
    "DXY": "DX-Y.NYB",
    "USD/KRW": "KRW=X",
    "USD/JPY": "JPY=X",

    # 원자재
    "WTI": "CL=F",
    "금": "GC=F",
    "구리": "HG=F",

    # 팀 보유 ETF 선행 지표 (미국 ETF로 매크로 흐름 추적)
    "SOXX(반도체)": "SOXX",       # ACE 글로벌반도체TOP4 Plus 선행
    "XLK(빅테크)": "XLK",         # 미국 기술주 전반
    "PAVE(인프라)": "PAVE",       # KODEX 미국AI전력핵심인프라 선행
    "ITA(미국방산)": "ITA",       # TIGER K방산&우주 비교
    "EWY(한국)": "EWY",           # 외국인 한국 수급 게이지
    "URA(우라늄)": "URA",         # HANARO 원자력iSelect 선행
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🇰🇷 한국장 모드 (16:00 KST)
# - 한국 시장 + 팀 실제 보유 ETF 직접 추적
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KR_TICKERS = {
    # 한국 지수
    "코스피": "^KS11",
    "코스닥": "^KQ11",

    # 대형주 (반도체 투톱)
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",

    # 환율
    "USD/KRW": "KRW=X",
    "DXY": "DX-Y.NYB",
    "USD/JPY": "JPY=X",

    # 미국 선행 (선물)
    "S&P500_선물": "ES=F",
    "나스닥_선물": "NQ=F",

    # 원자재
    "WTI": "CL=F",
    "금": "GC=F",

    # ★ 팀이 실제 매수할 ETF 직접 추적 (계획서 기준)
    "KODEX 200": "069500.KS",                      # 국내 베타 핵심
    "ACE 글로벌반도체TOP4 Plus": "485540.KS",       # 반도체 슈퍼사이클
    "KODEX 미국AI전력핵심인프라": "487230.KS",      # AI 전력 인프라
    "KODEX 로봇액티브": "404990.KS",                # 휴머노이드
    "SOL 조선TOP3플러스": "466920.KS",              # K-조선
    "TIGER K방산&우주": "449450.KS",                # K-방산
    "HANARO 원자력iSelect": "434730.KS",            # 원전 SMR
}


def collect_market_data(mode="us"):
    """시장 데이터 수집 (mode: 'us' or 'kr')"""

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

    data["mode"] = mode
    data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    return data


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "us"
    result = collect_market_data(mode)
    print(f"\n=== {mode.upper()} 모드 시장 데이터 ===")
    for k, v in result.items():
        print(f"{k}: {v}")
