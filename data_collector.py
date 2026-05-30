import yfinance as yf
from datetime import datetime

def collect_market_data():
    """주요 시장 데이터 수집"""

    tickers = {
        "S&P500": "^GSPC",
        "나스닥": "^IXIC",
        "코스피": "^KS11",
        "코스닥": "^KQ11",
        "VIX": "^VIX",
        "WTI": "CL=F",
        "금": "GC=F",
        "USD/KRW": "KRW=X",
        "USD/JPY": "JPY=X",
        "DXY": "DX-Y.NYB",
        "미국10년물": "^TNX",
    }

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

    data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    return data


if __name__ == "__main__":
    result = collect_market_data()
    print("\n=== 시장 데이터 수집 결과 ===")
    for k, v in result.items():
        print(f"{k}: {v}")
