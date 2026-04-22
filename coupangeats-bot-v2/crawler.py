"""
쿠팡이츠 파트너센터 정산 크롤러
- Selenium을 이용해 로그인 후 정산 데이터를 가져옵니다.
"""

import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


PARTNER_URL = "https://partner.coupangeats.com"
LOGIN_URL = f"{PARTNER_URL}/login"
SETTLEMENT_URL = f"{PARTNER_URL}/settlement"  # 정산 페이지 URL (실제 경로 확인 필요)


def get_driver() -> webdriver.Chrome:
    """헤드리스 Chrome 드라이버를 생성합니다."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver


def login(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """쿠팡이츠 파트너센터에 로그인합니다."""
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15)

        # 아이디 입력
        id_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        id_input.clear()
        id_input.send_keys(username)

        # 비밀번호 입력
        pw_input = driver.find_element(By.NAME, "password")
        pw_input.clear()
        pw_input.send_keys(password)

        # 로그인 버튼 클릭
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()

        # 로그인 완료 대기 (로그인 후 이동되는 페이지 요소 감지)
        wait.until(EC.url_changes(LOGIN_URL))
        time.sleep(2)

        print(f"[INFO] 로그인 성공: {username}")
        return True

    except TimeoutException:
        print("[ERROR] 로그인 타임아웃 - 아이디/비밀번호 또는 페이지 구조를 확인하세요.")
        return False
    except Exception as e:
        print(f"[ERROR] 로그인 실패: {e}")
        return False


def get_settlement_data(driver: webdriver.Chrome) -> dict:
    """
    정산 페이지에서 정산 데이터를 크롤링합니다.

    Returns:
        dict: 정산 데이터 (날짜, 매출, 정산 예정금, 정산 완료금 등)
    """
    try:
        driver.get(SETTLEMENT_URL)
        wait = WebDriverWait(driver, 15)
        time.sleep(3)  # 페이지 렌더링 대기

        data = {
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period": "",
            "total_sales": "N/A",
            "settlement_pending": "N/A",
            "settlement_completed": "N/A",
            "deduction": "N/A",
            "net_settlement": "N/A",
        }

        # ─────────────────────────────────────────────────
        # ⚠️  아래 셀렉터는 실제 쿠팡이츠 파트너센터 HTML 구조에 맞게 수정 필요
        # 브라우저 개발자도구(F12)로 각 요소의 selector를 확인하세요.
        # ─────────────────────────────────────────────────

        # 예시: 이번 달 정산 기간
        try:
            period_el = driver.find_element(By.CSS_SELECTOR, ".settlement-period")
            data["period"] = period_el.text.strip()
        except NoSuchElementException:
            data["period"] = _get_current_period()

        # 예시: 총 매출액
        try:
            sales_el = driver.find_element(By.CSS_SELECTOR, ".total-sales-amount")
            data["total_sales"] = sales_el.text.strip()
        except NoSuchElementException:
            pass

        # 예시: 정산 예정금
        try:
            pending_el = driver.find_element(By.CSS_SELECTOR, ".settlement-pending-amount")
            data["settlement_pending"] = pending_el.text.strip()
        except NoSuchElementException:
            pass

        # 예시: 정산 완료금
        try:
            completed_el = driver.find_element(By.CSS_SELECTOR, ".settlement-completed-amount")
            data["settlement_completed"] = completed_el.text.strip()
        except NoSuchElementException:
            pass

        # 예시: 공제액 (수수료 등)
        try:
            deduction_el = driver.find_element(By.CSS_SELECTOR, ".deduction-amount")
            data["deduction"] = deduction_el.text.strip()
        except NoSuchElementException:
            pass

        # 예시: 실 정산금
        try:
            net_el = driver.find_element(By.CSS_SELECTOR, ".net-settlement-amount")
            data["net_settlement"] = net_el.text.strip()
        except NoSuchElementException:
            pass

        print(f"[INFO] 정산 데이터 수집 완료: {data}")
        return data

    except TimeoutException:
        print("[ERROR] 정산 페이지 로딩 타임아웃")
        return {}
    except Exception as e:
        print(f"[ERROR] 정산 데이터 수집 실패: {e}")
        return {}


def _get_current_period() -> str:
    """현재 정산 기간을 반환합니다 (이번 달 1일 ~ 오늘)."""
    today = datetime.now()
    start = today.replace(day=1).strftime("%Y.%m.%d")
    end = today.strftime("%Y.%m.%d")
    return f"{start} ~ {end}"


def run_crawl() -> dict:
    """
    전체 크롤링 프로세스를 실행합니다.

    Returns:
        dict: 정산 데이터
    """
    username = os.environ.get("COUPANGEATS_ID")
    password = os.environ.get("COUPANGEATS_PW")

    if not username or not password:
        raise ValueError("환경변수 COUPANGEATS_ID, COUPANGEATS_PW가 설정되지 않았습니다.")

    driver = get_driver()
    try:
        success = login(driver, username, password)
        if not success:
            raise RuntimeError("로그인에 실패했습니다.")

        data = get_settlement_data(driver)
        return data
    finally:
        driver.quit()
