"""
메인 컨트롤러
- GitHub Actions 로그로 정산 데이터를 출력합니다.
"""

from dotenv import load_dotenv
import crawler


def run():
    load_dotenv(override=True)
    print("[START] 쿠팡이츠 정산 봇 시작")

    data = crawler.run_crawl()

    if not data:
        print("[ERROR] 정산 데이터를 가져오지 못했습니다.")
        return

    print("\n========== 쿠팡이츠 정산 현황 ==========")
    print(f"조회 시각     : {data.get('crawled_at', 'N/A')}")
    print(f"정산 기간     : {data.get('period', 'N/A')}")
    print(f"총 매출액     : {data.get('total_sales', 'N/A')}")
    print(f"정산 예정금   : {data.get('settlement_pending', 'N/A')}")
    print(f"정산 완료금   : {data.get('settlement_completed', 'N/A')}")
    print(f"공제액        : {data.get('deduction', 'N/A')}")
    print(f"실 정산금     : {data.get('net_settlement', 'N/A')}")
    print("========================================\n")

    print("[DONE] 완료")


if __name__ == "__main__":
    run()
