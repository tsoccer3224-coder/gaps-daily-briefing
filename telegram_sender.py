import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()


def send_telegram(message, max_retries=3):
    """텔레그램으로 메시지 전송 (재시도 + 긴 메시지 분할)"""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 텔레그램 메시지 최대 길이는 4096자. 길면 잘라서 여러 번 전송
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]

    for idx, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
        }

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    print(f"텔레그램 전송 성공! ({idx+1}/{len(chunks)})")
                    break
                else:
                    print(f"전송 실패: {response.status_code} - {response.text}")
                    break
            except requests.exceptions.RequestException as e:
                print(f"전송 시도 {attempt}/{max_retries} 실패: {type(e).__name__}")
                if attempt < max_retries:
                    print("3초 후 재시도...")
                    time.sleep(3)
                else:
                    print("최대 재시도 횟수 초과. 전송 실패.")
                    return False

    return True


if __name__ == "__main__":
    send_telegram("테스트 메시지입니다. GAPS 자동화 시스템 정상 작동!")
