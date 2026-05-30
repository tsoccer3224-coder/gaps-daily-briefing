from briefing_generator import generate_briefing
from telegram_sender import send_telegram


def main():
    print("=" * 40)
    print("GAPS 일일 시황 자동 생성 시작")
    print("=" * 40)

    print("\n[1/2] 시황 생성 중... (30초~1분 소요)")
    briefing = generate_briefing()

    print("\n[생성된 시황]")
    print(briefing)

    print("\n[2/2] 텔레그램 전송 중...")
    send_telegram(briefing)

    print("\n완료!")


if __name__ == "__main__":
    main()
