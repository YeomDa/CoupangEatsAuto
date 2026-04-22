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
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login(driver: webdriver.Chrome, username: str, password: str) -> bool:
    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15)

        id_input = wait.until(EC.presence_of_element_located((By.ID, "loginId")))
        id_input.clear()
        id_input.send_keys(username)
        print("[DEBUG] 아이디 입력 완료")

        pw_input = driver.find_element(By.ID, "password")
        pw_input.clear()
        pw_input.send_keys(password)
        print("[DEBUG] 비밀번호 입력 완료")

        driver.save_screenshot("/tmp/before_login.png")

        login_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "merchant-submit-btn")))
        login_btn.click()
        print("[DEBUG] 로그인 버튼 클릭 완료")

        time.sleep(5)
        driver.save_screenshot("/tmp/after_login.png")
        print(f"[DEBUG] 클릭 후 URL: {driver.current_url}")

        try:
            wait.until(EC.invisibility_of_element_located((By.ID, "loginId")))
            print("[INFO] 로그인 성공")
            return True
        except TimeoutException:
            print("[ERROR] 로그인 후에도 여전히 로그인 페이지")
            return False

    except TimeoutException:
        print("[ERROR] 로그인 타임아웃")
        driver.save_screenshot("/tmp/timeout.png")
        return False
    except Exception as e:
        print(f"[ERROR] 로그인 실패: {e}")
        return False


def withdraw_all(driver: webdriver.Chrome) -> dict:
    data = {
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "withdraw_available": "N/A",
        "settlement_pending": "N/A",
        "withdraw_result": "미실행",
    }

    try:
        driver.get(SETTLEMENT_URL)
        time.sleep(5)
        print(f"[DEBUG] 현재 URL: {driver.current_url}")
        driver.save_screenshot("/tmp/settlement.png")

        # 팝업 닫기 (있으면 닫고 없으면 그냥 진행)
        try:
            close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='Dialog__CloseButton']")
            ))
            close_btn.click()
            print("[DEBUG] 팝업 닫기 완료")
            time.sleep(1)
        except TimeoutException:
            print("[DEBUG] 팝업 없음 - 그냥 진행")

        driver.save_screenshot("/tmp/after_popup.png")

        # 출금 가능 금액 읽기
        try:
            withdraw_el = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".settlement-section-withdraw-value span")
            ))
            data["withdraw_available"] = withdraw_el.text.strip()
            print(f"[INFO] 출금 가능 금액: {data['withdraw_available']}")
        except TimeoutException:
            print("[WARN] 출금 가능 금액 요소를 찾지 못했습니다.")

        # 출금 가능 금액이 0원이면 스킵
        amount_text = data["withdraw_available"].replace(",", "").replace("원", "").strip()
        if not amount_text.isdigit() or int(amount_text) == 0:
            print("[INFO] 출금 가능 금액이 없어 출금을 건너뜁니다.")
            data["withdraw_result"] = "출금 금액 없음"
            return data

        # 출금하기 버튼 클릭
        withdraw_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".withdraw-confirm-ok")
        ))
        withdraw_btn.click()
        print("[DEBUG] 출금하기 버튼 클릭")
        time.sleep(3)
        driver.save_screenshot("/tmp/after_withdraw_btn.png")

        # iframe으로 전환
        iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".settlement__iframe-viewer iframe")
        ))
        driver.switch_to.frame(iframe)
        print("[DEBUG] iframe 전환 완료")
        time.sleep(1)

        # 전액 버튼 클릭
        total_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "totalBalance")))
        total_btn.click()
        print("[DEBUG] 전액 버튼 클릭")
        time.sleep(1)

        # 인출 버튼 클릭
        withdraw_confirm_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "withdrawButton")))
        withdraw_confirm_btn.click()
        print("[DEBUG] 인출 버튼 클릭")
        time.sleep(2)
        driver.save_screenshot("/tmp/after_withdraw_confirm.png")

        # 확인 버튼 클릭
        confirm_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "confirmButton")))
        confirm_btn.click()
        print("[DEBUG] 확인 버튼 클릭")
        time.sleep(2)

        driver.switch_to.default_content()
        driver.save_screenshot("/tmp/withdraw_done.png")

        data["withdraw_result"] = "출금 완료"
        print(f"[INFO] 출금 완료: {data['withdraw_available']}")
        return data

    except TimeoutException:
        print("[ERROR] 타임아웃 발생")
        driver.save_screenshot("/tmp/error.png")
        data["withdraw_result"] = "실패 (타임아웃)"
        return data
    except Exception as e:
        print(f"[ERROR] 출금 실패: {e}")
        driver.save_screenshot("/tmp/error.png")
        data["withdraw_result"] = f"실패: {e}"
        return data


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
        return withdraw_all(driver)
    finally:
        driver.quit()
