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


PARTNER_URL = "https://store.coupangeats.com"
LOGIN_URL = f"{PARTNER_URL}/merchant/login"
SETTLEMENT_URL = f"{PARTNER_URL}/merchant/management/orders/955171"  # 정산 페이지 URL (실제 경로 확인 필요)


def get_driver() -> webdriver.Chrome:
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
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15)

        # 아이디 입력 (id="loginId")
        id_input = wait.until(EC.presence_of_element_located((By.ID, "loginId")))
        id_input.clear()
        id_input.send_keys(username)

        # 비밀번호 입력 (id 확인 필요 - 임시로 추정)
        pw_input = driver.find_element(By.ID, "loginPw")
        pw_input.clear()
        pw_input.send_keys(password)

        # 로그인 버튼 (class="merchant-submit-btn")
        login_btn = driver.find_element(By.CLASS_NAME, "merchant-submit-btn")
        login_btn.click()

        wait.until(EC.url_changes(LOGIN_URL))
        time.sleep(2)

        print(f"[INFO] 로그인 성공: {username}")
        return True

    except TimeoutException:
        print("[ERROR] 로그인 타임아웃")
        return False
    except Exception as e:
        print(f"[ERROR] 로그인 실패: {e}")
        return False
 
def get_settlement_data(driver: webdriver.Chrome) -> dict:
    try:
        driver.get(SETTLEMENT_URL)
        WebDriverWait(driver, 15)
        time.sleep(3)
 
        data = {
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period": _get_current_period(),
            "withdraw_available": "N/A",
        }
 
        # 출금 가능 금액
        # <div class="settlement-section-withdraw-value"><span>32,622원</span></div>
        try:
            withdraw_el = driver.find_element(
                By.CSS_SELECTOR, ".settlement-section-withdraw-value span"
            )
            data["withdraw_available"] = withdraw_el.text.strip()
            print(f"[INFO] 출금 가능 금액: {data['withdraw_available']}")
        except NoSuchElementException:
            print("[WARN] 출금 가능 금액 요소를 찾지 못했습니다.")
 
        # 정산 섹션 전체 텍스트 (디버그용 - 로그에서 확인)
        try:
            section = driver.find_element(
                By.CSS_SELECTOR, ".settlement-summary-withdraw-section"
            )
            print(f"[DEBUG] 정산 섹션 전체:\n{section.text.strip()}")
        except NoSuchElementException:
            pass
 
        return data
 
    except TimeoutException:
        print("[ERROR] 정산 페이지 로딩 타임아웃")
        return {}
    except Exception as e:
        print(f"[ERROR] 정산 데이터 수집 실패: {e}")
        return {}
 
 
def _get_current_period() -> str:
    today = datetime.now()
    start = today.replace(day=1).strftime("%Y.%m.%d")
    end = today.strftime("%Y.%m.%d")
    return f"{start} ~ {end}"
 
 
def run_crawl() -> dict:
    username = os.environ.get("COUPANGEATS_ID")
    password = os.environ.get("COUPANGEATS_PW")
 
    if not username or not password:
        raise ValueError("환경변수 COUPANGEATS_ID, COUPANGEATS_PW가 설정되지 않았습니다.")
 
    driver = get_driver()
    try:
        success = login(driver, username, password)
        if not success:
            raise RuntimeError("로그인에 실패했습니다.")
        return get_settlement_data(driver)
    finally:
        driver.quit()
