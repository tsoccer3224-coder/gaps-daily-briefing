import sys
from briefing_generator import generate_briefing
from telegram_sender import send_telegram


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "us"
    mode_name = "미국장 마감" if mode == "us" else "한국장 마감"

    print("=" * 40)
    print(f"충북대장주 GAPS {mode_name} 브리핑 시작")
    print("=" * 40)

    print(f"\n[1/2] {mode_name} 시황 생성 중... (30초~1분 소요)")
    briefing = generate_briefing(mode)

    print("\n[생성된 시황]")
    print(briefing)

    print("\n[2/2] 텔레그램 전송 중...")
    send_telegram(briefing)

    print("\n완료!")


if __name__ == "__main__":
    main()
