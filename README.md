# kdt15-team4-project1

중고거래의 불안 요소와 기존 경매 사이트의 불편함을 보완하는 경매 기반 중고거래 웹 프로젝트입니다.

## 프로젝트 목표

이 프로젝트는 이베이, 코베이, 크림 등 기존 거래·경매 서비스의 장단점을 참고하여 더 안전하고 직관적인 경매 사이트를 제작하는 것을 목표로 합니다.

핵심 목표는 다음과 같습니다.

- 중고거래의 사기 위험을 줄입니다.
- 판매자와 구매자의 직접 금전 거래를 줄입니다.
- 가격 흥정 대신 입찰과 즉시구매 방식으로 거래합니다.
- 상품 시세 정보를 제공하여 합리적인 가격 판단을 돕습니다.
- 사이트 업체가 중간 검수와 정산 역할을 맡는 안전 거래 구조를 만듭니다.

## GitHub 정보

```txt
Repository: https://github.com/vvybh/kdt15-team4-project1.git
Branch: feature/web
```

## 기본 폴더 구조

```txt
kdt15-team4-project1/
├─ README.md
├─ AGENTS.md
├─ context/
│  └─ project-brief.md
├─ templates/
│  └─ HTML 파일 저장 위치
├─ static/
│  ├─ css/
│  ├─ js/
│  └─ images/
├─ app.py
├─ requirements.txt
└─ .gitignore
```

## templates 폴더 규칙

프로젝트에서 제작되는 모든 HTML 파일은 `templates/` 폴더 안에 저장합니다.

예상 HTML 파일 예시는 다음과 같습니다.

```txt
templates/
├─ base.html
├─ index.html
├─ login.html
├─ register.html
├─ product_list.html
├─ product_detail.html
├─ product_create.html
├─ market_price.html
├─ popular.html
└─ mypage.html
```

## 핵심 기능

- 로그인 / 회원가입
- 상품 등록
- 상품 목록 조회
- 상품 상세 조회
- 입찰
- 즉시구매
- 시세 조회
- 인기 상품 조회
- 마이페이지
- 경고 및 포인트 정책
- 판매자 배송, 구매자 결제, 업체 검수, 정산 흐름

## 우선 개발 범위

1차 개발에서는 화면 흐름과 핵심 경매 기능을 우선 구현합니다.

- 메인 화면
- 상품 등록
- 상품 목록
- 상품 상세
- 입찰
- 즉시구매
- 로그인 / 회원가입
- 마이페이지 기본 구조

시세 크롤링, 결제, 배송, 정산, 관리자 검수 기능은 이후 확장 기능으로 분리합니다.

## 참고 문서

- `AGENTS.md`: Codex 작업 지침
- `context/project-brief.md`: 프로젝트 요구사항과 서비스 흐름
