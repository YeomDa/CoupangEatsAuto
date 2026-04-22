# 🍔 쿠팡이츠 정산 알림 봇

매일 오전 9시에 쿠팡이츠 파트너센터에서 정산 데이터를 자동으로 가져와 카카오톡으로 알려드립니다.

---

## 📁 프로젝트 구조

```
coupangeats-bot/
├── .github/
│   └── workflows/
│       └── settlement.yml   # GitHub Actions 스케줄 설정
├── controller.py            # 메인 진입점
├── crawler.py               # 쿠팡이츠 파트너센터 크롤러
├── notification.py          # 카카오톡 알림 모듈
├── requirements.txt
├── .env.sample
└── README.md
```

---

## 🚀 사용법

### 1. 레포지토리 Fork

이 레포지토리를 본인 GitHub 계정으로 `fork`합니다.

---

### 2. 카카오 토큰 발급

카카오 "나에게 보내기" 기능을 사용합니다 (무료, 개인 계정).

#### 2-1. 카카오 앱 생성

1. [https://developers.kakao.com](https://developers.kakao.com) 접속 → 로그인
2. **내 애플리케이션 → 애플리케이션 추가하기**
3. 앱 이름 입력 후 저장
4. **앱 키 → REST API 키** 복사 (이것이 `KAKAO_REST_API_KEY`)

#### 2-2. 카카오톡 메시지 권한 활성화

1. 앱 → **제품 설정 → 카카오 로그인** → 활성화 ON
2. **동의항목** → `카카오톡 메시지 전송` 체크

#### 2-3. 리프레시 토큰 발급 (최초 1회)

브라우저에서 아래 URL 접속 (YOUR_REST_API_KEY 교체):

```
https://kauth.kakao.com/oauth/authorize?client_id=YOUR_REST_API_KEY&redirect_uri=https://example.com&response_type=code
```

- 카카오 로그인 → 동의 후 리다이렉트된 URL에서 `code=` 값 복사

터미널에서 아래 명령 실행 (code, REST API KEY 교체):

```bash
curl -X POST https://kauth.kakao.com/oauth/token \
  -d 'grant_type=authorization_code' \
  -d 'client_id=YOUR_REST_API_KEY' \
  -d 'redirect_uri=https://example.com' \
  -d 'code=YOUR_CODE'
```

응답 JSON에서 `refresh_token` 값 복사 → 이것이 `KAKAO_REFRESH_TOKEN`

---

### 3. GitHub Secrets 등록

레포지토리 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 이름 | 값 |
|---|---|
| `COUPANGEATS_ID` | 쿠팡이츠 파트너센터 아이디 |
| `COUPANGEATS_PW` | 쿠팡이츠 파트너센터 비밀번호 |
| `KAKAO_REST_API_KEY` | 카카오 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 카카오 리프레시 토큰 |

---

### 4. crawler.py 셀렉터 수정 ⚠️

> **이 단계가 가장 중요합니다.**

쿠팡이츠 파트너센터의 실제 HTML 구조에 맞게 `crawler.py` 내 CSS 셀렉터를 수정해야 합니다.

1. 쿠팡이츠 파트너센터([https://partner.coupangeats.com](https://partner.coupangeats.com)) 접속
2. 정산 페이지로 이동
3. 브라우저 개발자도구 (F12) → 정산 금액 요소 우클릭 → **검사**
4. `crawler.py`의 해당 `CSS_SELECTOR` 값을 실제 값으로 교체

```python
# 예시: 실제 선택자로 교체하세요
sales_el = driver.find_element(By.CSS_SELECTOR, ".실제-클래스명")
```

---

### 5. 실행 시간 조정

`.github/workflows/settlement.yml`에서 cron 표현식을 수정합니다.

```yaml
# 매일 오전 9시 KST (= UTC 00:00)
- cron: "0 0 * * *"

# 매일 오전 8시 KST
- cron: "0 23 * * *"  # 전날 UTC 23시

# 평일(월~금) 오전 9시 KST
- cron: "0 0 * * 1-5"
```

---

## 💬 알림 예시

```
🍔 쿠팡이츠 정산 현황 (2025-04-17 09:00)
────────────────────
📅 정산 기간: 2025.04.01 ~ 2025.04.17
💰 총 매출액: 1,250,000원
⏳ 정산 예정금: 380,000원
✅ 정산 완료금: 820,000원
📉 공제액 (수수료 등): 125,000원
💵 실 정산금: 1,125,000원
────────────────────
파트너센터에서 자세히 확인하세요.
```

---

## ⚙️ 로컬 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 작성
cp .env.sample .env
# .env 파일에 실제 값 입력

# 실행
python controller.py
```

---

## ❗ 주의사항

- 카카오 리프레시 토큰은 **유효기간이 최대 60일**입니다. 만료 전 재발급이 필요합니다.
- 쿠팡이츠 파트너센터 UI가 변경되면 셀렉터 수정이 필요할 수 있습니다.
- GitHub Actions 무료 플랜은 월 2,000분의 실행 시간을 제공합니다 (본 봇은 매일 약 1~2분 사용).
