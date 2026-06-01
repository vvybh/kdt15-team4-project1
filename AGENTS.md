# AGENTS.md

## 역할

이 문서는 Codex가 이 프로젝트에서 작업할 때 따라야 하는 기준입니다.

프로젝트 설명은 `README.md`를 확인하고, 상세 요구사항은 `context/project-brief.md`를 확인합니다.

## 작업 시작 순서

작업을 시작할 때 아래 순서로 확인합니다.

1. `README.md`
2. `context/project-brief.md`
3. 현재 파일 목록
4. Git 상태
5. 수정 대상 파일

## 프로젝트 정보

```txt
Repository: https://github.com/vvybh/kdt15-team4-project1.git
Branch: feature/web
```

## 작업 원칙

- 사용자가 요청한 범위 안에서만 수정합니다.
- 기존 파일 구조와 작성 방식을 먼저 확인합니다.
- 관련 없는 리팩터링은 하지 않습니다.
- 사용자가 만든 변경 사항을 임의로 삭제하지 않습니다.
- 확정되지 않은 내용은 `확인 필요`라고 표시합니다.
- 근거 없는 수치나 기능을 임의로 추가하지 않습니다.

## HTML 파일 규칙

- 모든 HTML 파일은 `templates/` 폴더 안에 저장합니다.
- HTML 파일을 루트 폴더에 만들지 않습니다.
- 공통 레이아웃이 필요하면 `templates/base.html`을 먼저 만들고 재사용합니다.
- 페이지별 HTML은 역할이 드러나는 이름으로 작성합니다.

예시:

```txt
templates/index.html
templates/login.html
templates/register.html
templates/product_list.html
templates/product_detail.html
templates/product_create.html
templates/market_price.html
templates/popular.html
templates/mypage.html
```

## CSS / JS / 이미지 파일 규칙

정적 파일은 `static/` 폴더 아래에 저장합니다.

```txt
static/css/
static/js/
static/images/
```

## 기능 구현 기준

### 상품 등록
- 제품 사진, 제품명, 브랜드명을 입력받습니다.
- 경매시작가와 즉시구매가를 입력받습니다.
- 경매 마감 시간은 1일, 3일, 7일, 15일 중 선택하게 합니다.
- 즉시구매가는 경매시작가보다 높아야 합니다.

### 입찰
- 현재 입찰가보다 낮거나 같은 금액은 허용하지 않습니다.
- 입찰 성공 시 현재 입찰가와 입찰 수를 갱신합니다.
- 서버 시간을 기준으로 경매 종료 여부를 판단합니다.

### 즉시구매
- 즉시구매가 발생하면 경매는 종료됩니다.
- 구매자는 결제 대기 상태로 이동합니다.
- 판매자는 상품 배송 요청 상태로 이동합니다.

### 거래 상태
거래 상태는 화면마다 다르게 처리하지 말고 공통 기준으로 관리합니다.

권장 상태값:

```txt
BIDDING
SOLD
PAYMENT_WAITING
SELLER_SHIPPING
INSPECTION_WAITING
DELIVERING
COMPLETED
CANCELLED
```

## 시세 정보 구현 기준

- 시세 데이터는 참고용으로 표시합니다.
- 시세를 확정 가격처럼 표현하지 않습니다.
- 데이터가 부족하면 `시세 정보 부족` 상태를 표시합니다.
- 시세 게이지는 최저가, 평균가, 최고가, 현재 경매가를 비교할 수 있게 구성합니다.

## 경고 및 포인트 정책 구현 기준

- 판매자가 정해진 기간 안에 상품을 보내지 않으면 판매자에게 경고 1회를 부여합니다.
- 구매자가 정해진 기간 안에 금액을 송금하지 않으면 구매자에게 경고 1회를 부여합니다.
- 경고 3회가 되면 이용 제한 상태로 처리합니다.
- 귀책 없는 상대방에게 1,000포인트를 지급합니다.
- 포인트는 배송비 할인 용도로 사용합니다.

## 검증 기준

문서 또는 코드를 수정한 뒤 아래 항목을 확인합니다.

- 요청한 파일만 수정했는가?
- HTML 파일이 `templates/` 안에 있는가?
- 문서 내용이 중복되지 않는가?
- 프로젝트 요구사항과 충돌하지 않는가?
- Python 파일을 수정했다면 문법 검사를 했는가?
- GitHub에 푸시하기 전 `feature/web` 브랜치인지 확인했는가?

## Git 작업 기준

작업 전 확인:

```powershell
git status --short --branch
git remote -v
```

브랜치 확인:

```powershell
git branch
```

필요 시 브랜치 이동:

```powershell
git checkout feature/web
```

푸시는 사용자가 명확히 요청한 경우에만 진행합니다.

```powershell
git push origin feature/web
```
