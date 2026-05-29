# 크롤링 설계

## 목적

크롤링 파트의 목적은 경매 웹사이트 안에서 시세 그래프와 가격 참고 정보를 보여주는 것이다.
시세 그래프는 별도 서비스가 아니다.
판매 등록 화면과 경매 상세 화면에서 시작가와 입찰 판단을 돕는 보조 기능이다.

## 기본 방향

당근마켓, 중고나라, 번개장터, KREAM에서 물품 가격 데이터를 수집한다.
사이트마다 페이지 구조와 표현 방식이 다르므로, 수집한 데이터를 바로 쓰지 않는다.
먼저 원본 데이터를 저장하고, 그다음 공통 형식으로 정리한다.
웹사이트는 실시간으로 크롤링하지 않는다.
웹사이트는 SQLite에 저장된 데이터만 읽어서 시세 그래프를 보여준다.
CSV는 샘플 작성과 데이터 적재 준비에 사용한다.

크롤링은 `requests + BeautifulSoup`을 기본 방식으로 진행한다.
JavaScript로 화면이 늦게 만들어져 기본 방식으로 수집이 어려운 경우에만 Selenium을 보조로 사용한다.

전체 흐름은 아래와 같다.

1. 검색어 또는 카테고리를 정한다.
2. 사이트별 크롤러가 데이터를 수집한다.
3. 원본 데이터를 그대로 저장한다.
4. 공통 필드로 정규화한다.
5. 중복, 누락, 이상치를 확인한다.
6. SQLite에 저장한다.
7. 웹사이트의 시세 그래프와 가격 참고 정보에서 사용한다.

정규화는 서로 다른 형식의 데이터를 같은 기준으로 맞추는 작업이다.

## 확정된 크롤링 방식

- 기본 방식: `requests + BeautifulSoup`
- 보조 방식: Selenium
- Selenium 사용 조건: 공개 HTML에서 필요한 데이터가 보이지 않을 때
- 우선순위: 기본 방식으로 먼저 시도하고, 실패한 사이트만 Selenium으로 보완
- 웹사이트 화면에서는 크롤러를 직접 실행하지 않음
- 크롤링 실패 시 기존 저장 데이터를 유지함

Selenium은 브라우저를 자동으로 실행해 화면에 나타난 내용을 확인하는 도구다.
동적 페이지에는 유용하지만 실행이 느리고 설정이 늘어날 수 있다.

## 저장 데이터 사용 원칙

웹사이트는 저장된 데이터만 사용한다.
크롤링은 데이터를 갱신하는 별도 작업이다.

- 판매 등록 화면은 SQLite의 기존 데이터를 읽어 시세 그래프를 보여준다.
- 경매 상세 화면도 저장된 데이터를 기준으로 가격 참고 정보를 보여준다.
- 크롤링이 실패해도 웹사이트는 기존 데이터를 계속 보여준다.
- 최신 데이터가 없으면 `최근 수집 데이터 기준`이라고 표시한다.
- 데이터가 부족하면 `데이터 부족` 안내를 표시한다.
- 실시간 크롤링 버튼은 만들지 않는다.
- 자동 즉시 수집 기능은 만들지 않는다.

샘플 데이터 형식은 `context/sample-data-format.md`를 따른다.
초기 개발은 CSV로 샘플을 만들고, 웹사이트 조회는 SQLite를 기준으로 한다.

## 수집 대상 사이트

| 사이트 | 역할 | 수집 방향 |
| --- | --- | --- |
| 당근마켓 | 생활 밀착형 중고거래 가격 참고 | 지역, 물품명, 가격, 게시일 중심 |
| 중고나라 | 다양한 중고 물품 가격 참고 | 물품명, 가격, 거래 상태, 게시일 중심 |
| 번개장터 | 개인 간 중고거래 가격 참고 | 물품명, 가격, 상품 상태, 이미지 중심 |
| KREAM | 브랜드 상품과 의류 시세 참고 | 브랜드, 모델명, 거래 가격, 상품 상태 중심 |

사이트별 HTML 구조와 접근 방식은 구현 단계에서 확인 필요다.
정책상 수집 가능 여부도 제출 전 다시 확인한다.

## 수집 원칙

- 개인정보는 수집하지 않는다.
- 판매자 실명, 전화번호, 채팅 내용, 상세 주소는 저장하지 않는다.
- 가격 판단에 필요한 데이터만 수집한다.
- 원문 링크는 출처 확인용으로만 저장한다.
- 사이트별 정책을 위반할 수 있는 방식은 사용하지 않는다.
- 발표용으로는 샘플 데이터 또는 허용 범위 데이터도 사용할 수 있다.

## 공통 수집 항목

| 필드명 | 설명 | 예시 | 필수 여부 |
| --- | --- | --- | --- |
| source | 수집 사이트 | daangn, joongna, bunjang, kream | 필수 |
| collected_keyword | 수집에 사용한 검색어 | 나이키 후드티 | 권장 |
| source_item_id | 사이트 안에서 구분할 수 있는 글 또는 상품 ID | 12345 | 권장 |
| source_url | 원문 링크 | https://... | 권장 |
| title | 게시글 또는 상품 제목 | 나이키 후드티 | 필수 |
| normalized_title | 비교용으로 정리한 제목 | 나이키 후드티 | 권장 |
| product_name | 정리한 상품명 | 나이키 후드티 | 필수 |
| category | 카테고리 | 의류 | 필수 |
| source_category | 원본 사이트 카테고리 | 패션의류 > 남성의류 | 선택 |
| brand | 브랜드 | Nike | 선택 |
| model_name | 모델명 또는 상세 상품명 | 확인 필요 | 선택 |
| price | 가격 | 35000 | 필수 |
| currency | 통화 | KRW | 필수 |
| listed_at | 게시일 또는 등록일 | 2026-05-29 | 권장 |
| sold_at | 거래일 또는 판매 완료일 | 확인 필요 | 선택 |
| trade_status | 거래 상태 | 판매중, 예약중, 판매완료 | 권장 |
| source_status | 원본 사이트에서 읽은 거래 상태 | 판매중 | 선택 |
| item_condition | 상품 상태 | 새상품, 사용감 있음 | 권장 |
| components | 구성품 | 박스 포함, 충전기 포함 | 선택 |
| location | 지역 | 서울 강남구 | 선택 |
| shipping_fee | 배송비 | 3000 | 선택 |
| trade_method | 거래 방식 | 택배거래 | 선택 |
| image_url | 대표 이미지 주소 | https://... | 선택 |
| description | 설명 요약 | 착용 3회 | 선택 |
| crawled_at | 수집 시각 | 2026-05-29 12:00:00 | 필수 |

## 사이트별 우선 수집 항목

### 당근마켓

우선 수집 항목은 아래와 같다.

- 물품명
- 가격
- 지역
- 게시일
- 거래 상태
- 대표 이미지
- 원문 링크

주의할 점은 아래와 같다.

- 지역 정보는 가격 차이에 영향을 줄 수 있다.
- 개인 연락처나 채팅 관련 정보는 수집하지 않는다.
- 상세 주소는 저장하지 않는다.

### 중고나라

우선 수집 항목은 아래와 같다.

- 물품명
- 가격
- 게시일
- 거래 상태
- 카테고리
- 상품 상태
- 구성품
- 배송비
- 거래 방식
- 대표 이미지
- 원문 링크

주의할 점은 아래와 같다.

- 판매 완료 여부가 가격 판단에 중요하다.
- 같은 상품이라도 제목 표현이 다를 수 있다.
- 광고성 글이나 부품 판매 글은 이상치로 분리할 수 있다.
- 상품 설명에 연락처가 있으면 저장 전에 제거한다.
- 상세 지역은 저장하지 않는다.

### 번개장터

우선 수집 항목은 아래와 같다.

- 물품명
- 가격
- 상품 상태
- 거래 상태
- 대표 이미지
- 설명 요약
- 원문 링크

주의할 점은 아래와 같다.

- 상품 상태가 가격에 큰 영향을 줄 수 있다.
- 같은 브랜드 상품은 모델명 정리가 필요하다.
- 설명에서 구성품 정보를 추출할 수 있다.

### KREAM

우선 수집 항목은 아래와 같다.

- 브랜드
- 상품명
- 모델명
- 거래 가격 또는 판매 가격
- 상품 상태
- 거래일 또는 가격 기준일
- 이미지
- 원문 링크

주의할 점은 아래와 같다.

- 의류와 브랜드 상품의 기준 가격으로 쓰기 좋다.
- 일반 중고거래 사이트와 가격 기준이 다를 수 있다.
- 새상품 또는 리셀 상품 가격이 섞일 수 있으므로 상태 구분이 필요하다.

## 저장 형식

저장은 두 단계로 나눈다.

1. 원본 저장: 사이트에서 가져온 값을 최대한 그대로 저장한다.
2. 정규화 저장: 웹사이트와 그래프에서 쓰기 좋게 공통 필드로 저장한다.

## SQLite 테이블 설계

### crawl_runs

크롤링 실행 기록을 저장한다.

| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER | 실행 ID |
| source | TEXT | 수집 사이트 |
| keyword | TEXT | 검색어 |
| category | TEXT | 카테고리 |
| started_at | TEXT | 시작 시각 |
| finished_at | TEXT | 종료 시각 |
| status | TEXT | success, failed |
| item_count | INTEGER | 수집 개수 |
| error_message | TEXT | 오류 내용 |

크롤링이 실패해도 기존 `market_items`와 `price_snapshots` 데이터는 삭제하지 않는다.

### raw_items

사이트별 원본 데이터를 저장한다.

| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER | 원본 데이터 ID |
| crawl_run_id | INTEGER | 실행 ID |
| source | TEXT | 수집 사이트 |
| collected_keyword | TEXT | 수집에 사용한 검색어 |
| source_item_id | TEXT | 사이트 글 또는 상품 ID |
| source_url | TEXT | 원문 링크 |
| raw_title | TEXT | 원본 제목 |
| raw_price | TEXT | 원본 가격 |
| raw_status | TEXT | 원본 거래 상태 |
| raw_location | TEXT | 원본 지역 |
| raw_date | TEXT | 원본 날짜 |
| raw_category | TEXT | 원본 카테고리 |
| raw_condition | TEXT | 원본 상품 상태 |
| raw_components | TEXT | 원본 구성품 |
| raw_shipping_fee | TEXT | 원본 배송비 |
| raw_trade_method | TEXT | 원본 거래 방식 |
| raw_image_url | TEXT | 원본 이미지 |
| raw_description | TEXT | 원본 설명 요약 |
| raw_payload | TEXT | 원본 JSON 문자열 |
| crawled_at | TEXT | 수집 시각 |

raw_payload는 원본 데이터를 JSON 문자열로 저장한 값이다.
나중에 파싱 기준이 바뀌어도 다시 정리할 수 있게 남긴다.

### market_items

정규화된 물품 데이터를 저장한다.

| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER | 정규화 데이터 ID |
| raw_item_id | INTEGER | 원본 데이터 ID |
| source | TEXT | 수집 사이트 |
| collected_keyword | TEXT | 수집에 사용한 검색어 |
| source_url | TEXT | 원문 링크 |
| title | TEXT | 제목 |
| normalized_title | TEXT | 비교용 제목 |
| product_name | TEXT | 정리한 상품명 |
| category | TEXT | 카테고리 |
| source_category | TEXT | 원본 사이트 카테고리 |
| brand | TEXT | 브랜드 |
| model_name | TEXT | 모델명 |
| product_key | TEXT | 같은 상품을 묶는 기준 |
| price | INTEGER | 가격 |
| currency | TEXT | 통화 |
| listed_at | TEXT | 게시일 |
| sold_at | TEXT | 거래일 |
| trade_status | TEXT | 거래 상태 |
| source_status | TEXT | 원본 거래 상태 |
| item_condition | TEXT | 상품 상태 |
| components | TEXT | 구성품 |
| location | TEXT | 지역 |
| shipping_fee | INTEGER | 배송비 |
| trade_method | TEXT | 거래 방식 |
| image_url | TEXT | 이미지 주소 |
| description | TEXT | 설명 요약 |
| crawled_at | TEXT | 수집 시각 |

### price_snapshots

시세 그래프용 가격 데이터를 저장한다.

| 컬럼명 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER | 가격 데이터 ID |
| market_item_id | INTEGER | 정규화 데이터 ID |
| product_key | TEXT | 같은 상품을 묶는 키 |
| price | INTEGER | 가격 |
| observed_at | TEXT | 가격 기준일 |
| source | TEXT | 수집 사이트 |
| trade_status | TEXT | 거래 상태 |
| item_condition | TEXT | 상품 상태 |

product_key는 같은 상품을 묶기 위한 값이다.
예를 들어 브랜드, 상품명, 모델명을 정리해서 만든다.

## CSV 저장 형식

초기 개발과 발표 준비를 위해 CSV를 사용한다.
사람이 직접 작성하는 샘플 데이터는 `data/sample/market_items.csv`로 둔다.
크롤링 후 정규화한 결과는 `data/processed/market_items.csv`로 둔다.

```csv
id,raw_item_id,source,collected_keyword,source_item_id,source_url,title,normalized_title,product_name,category,source_category,brand,model_name,product_key,item_condition,components,price,currency,trade_status,source_status,listed_at,sold_at,location,shipping_fee,trade_method,image_url,description,crawled_at
1,,joongna,나이키 후드티,227159992,https://web.joongna.com/product/227159992,나이키 후드티 95,나이키 후드티 95,후드티,의류,패션의류 > 남성의류 > 티셔츠,Nike,,의류:nike:후드티,중고,구성품 전체 포함,13000,KRW,판매중,판매중,,,,2000,택배거래,https://example.com/image.jpg,상태 좋아요,2026-05-29 12:00:00
```

CSV는 사람이 열어 보기 쉽다.
SQLite는 웹사이트에서 조회하기 쉽다.
따라서 개발 초기에는 CSV를 쓰고, 웹 연결 단계에서는 SQLite를 기준으로 한다.
자세한 컬럼 설명은 `context/sample-data-format.md`를 따른다.

## 폴더와 파일 구성

```txt
crawlers/
├─ base.py
├─ daangn.py
├─ joongna.py
├─ bunjang.py
└─ kream.py

services/
├─ crawler_service.py
├─ normalize_service.py
└─ price_service.py

data/
├─ sample/
│  └─ market_items.csv
├─ raw/
│  ├─ daangn/
│  ├─ joongna/
│  ├─ bunjang/
│  └─ kream/
├─ processed/
│  └─ market_items.csv
└─ app.db

scripts/
├─ run_crawlers.py
├─ crawl_joongna.py
├─ normalize_items.py
└─ load_market_items.py
```

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| crawlers/base.py | 사이트별 크롤러가 따라야 할 공통 구조 |
| crawlers/daangn.py | 당근마켓 데이터 수집 |
| crawlers/joongna.py | 중고나라 데이터 수집 |
| crawlers/bunjang.py | 번개장터 데이터 수집 |
| crawlers/kream.py | KREAM 데이터 수집 |
| services/crawler_service.py | 크롤러 실행 관리 |
| services/normalize_service.py | 원본 데이터를 공통 필드로 변환 |
| services/price_service.py | 시세 그래프와 가격 참고 정보 계산 |
| data/sample/market_items.csv | 사람이 직접 작성하는 샘플 데이터 |
| data/processed/market_items.csv | 정규화된 수집 결과 CSV |
| data/app.db | 웹사이트가 읽는 SQLite 데이터베이스 |
| scripts/run_crawlers.py | 수동 크롤링 실행 |
| scripts/crawl_joongna.py | 중고나라 공개 상품 수집 후 CSV와 SQLite 저장 |
| scripts/normalize_items.py | 원본 데이터 정리 |
| scripts/load_market_items.py | 정리된 데이터를 SQLite에 저장 |

## 크롤러 공통 출력 형식

각 사이트 크롤러는 아래 형식의 리스트를 반환한다.

```python
[
    {
        "source": "daangn",
        "source_item_id": "12345",
        "source_url": "https://example.com/item/12345",
        "raw_title": "나이키 후드티 판매합니다",
        "raw_price": "35,000원",
        "raw_status": "판매중",
        "raw_location": "서울 강남구",
        "raw_date": "2026-05-20",
        "raw_payload": {
            "source_category": "패션의류 > 남성의류",
            "item_condition": "중고",
            "components": "구성품 전체 포함",
            "shipping_fee": "2,000원",
            "trade_method": "택배거래",
            "image_url": "https://example.com/image.jpg",
            "description": "착용 3회"
        }
    }
]
```

사이트별 필드가 달라도 크롤러 출력 형식은 최대한 맞춘다.
부족한 값은 빈 값으로 둔다.

## 데이터 정리 규칙

### 가격 정리

- 쉼표와 `원` 문자를 제거한다.
- 숫자로 바꿀 수 없는 가격은 제외하거나 확인 목록에 넣는다.
- `무료나눔`, `가격제안` 같은 값은 별도 상태로 분리한다.

### 날짜 정리

- 가능한 경우 `YYYY-MM-DD` 형식으로 바꾼다.
- `방금 전`, `1시간 전` 같은 상대 시간은 수집일 기준으로 변환한다.
- 변환이 어렵다면 원본 날짜를 raw_items에만 저장한다.

### 상품명 정리

- 불필요한 특수문자를 줄인다.
- 브랜드와 모델명이 있으면 분리한다.
- 같은 상품을 묶기 위한 product_key를 만든다.

### 거래 상태 정리

거래 상태는 아래 값으로 맞춘다.

- 판매중
- 예약중
- 판매완료
- 거래상태확인필요

## 시세 그래프에 사용할 데이터

시세 그래프는 `price_snapshots` 테이블을 기준으로 만든다.
자세한 계산 기준은 `context/pricing-design.md`를 따른다.

그래프 기준은 아래와 같다.

- x축: 날짜
- y축: 가격
- 점 또는 선: 사이트별 가격 데이터
- 보조 정보: 평균 가격, 중간 가격, 최저가, 최고가

판매 등록 화면에서는 같은 상품의 최근 가격 범위를 보여준다.
경매 상세 화면에서는 현재 입찰가가 시세 범위 안에 있는지 함께 보여준다.

## 확인 필요 항목

### 1. 대표 수집 카테고리

1. 권장안: 의류 2개, 생필품 2개로 시작
   - 발표용 그래프를 만들기 쉽다.
   - 카테고리 비교도 가능하다.
2. 간단안: 의류만 먼저 수집
   - 상품명과 상태 기준을 맞추기 쉽다.
   - 서비스 범위가 좁아 보일 수 있다.
3. 확장안: 의류, 생필품, 전자기기까지 수집
   - 서비스가 풍부해 보인다.
   - 크롤링과 정리 부담이 커진다.

### 2. 상품 묶음 기준

1. 권장안: 카테고리, 브랜드, 상품명, 상태를 기준으로 묶는다.
   - 가격 비교 기준이 비교적 자연스럽다.
   - 구현 난이도도 과제 수준에 맞다.
2. 간단안: 상품명 키워드만 기준으로 묶는다.
   - 구현이 쉽다.
   - 다른 상품이 섞일 수 있다.
3. 확장안: 모델명, 구성품, 사용 기간까지 반영한다.
   - 가격 정확도는 올라간다.
   - 데이터 정리가 어려워진다.

### 3. 크롤링 주기

1. 권장안: 발표용으로 수동 실행 후 저장
   - 과제 범위에 맞다.
   - 수집 결과를 안정적으로 관리할 수 있다.
2. 간단안: 미리 만든 CSV를 SQLite에 넣어서 사용
   - 가장 빠르게 웹사이트와 그래프를 만들 수 있다.
   - 크롤링 기능 시연은 약해진다.
3. 확장안: 수동 실행 스크립트에 여러 사이트 일괄 수집 기능을 둔다.
   - 여러 사이트 데이터를 한 번에 갱신할 수 있다.
   - 오류 처리와 로그 관리가 필요하다.

### 4. 사이트별 정책 처리

1. 권장안: 정책 확인 필요를 발표에 명시하고, 허용 범위 또는 샘플 데이터로 구현한다.
   - 안전하다.
   - 리스크 관리가 보인다.
2. 간단안: 정책 검토 없이 샘플 데이터만 사용한다.
   - 구현은 쉽다.
   - 데이터 수집 프로젝트 특징이 약해질 수 있다.
3. 확장안: 사이트별 이용약관과 robots.txt 확인 결과를 별도 문서로 정리한다.
   - 가장 명확하다.
   - 조사 시간이 필요하다.

## 우선 구현 순서

1. 공통 CSV 형식을 먼저 만든다.
2. 샘플 데이터를 작성한다.
3. SQLite 테이블을 만든다.
4. 샘플 데이터를 SQLite에 넣는다.
5. 판매 등록 화면과 경매 상세 화면에서 시세 그래프를 연결한다.
6. 사이트별 크롤러는 한 사이트씩 연결한다.
7. 최종 발표 전 정책 확인 내용을 정리한다.

웹사이트 기능 구현은 크롤러 완성보다 먼저 진행할 수 있다.
그 경우 샘플 CSV 또는 SQLite 데이터를 기준으로 화면을 만든다.

## 정책 확인 반영

사이트별 robots.txt와 약관 확인 결과는 `context/crawling-policy-check.md`에 정리했다.

현재 웹사이트 시연은 실제 사이트를 실시간으로 크롤링하지 않는다.
CSV와 SQLite에 저장된 데이터를 기준으로 시세 그래프를 보여준다.

실제 수집 스크립트를 실행해야 한다면 아래 기준을 지킨다.

- robots.txt에서 제한한 경로는 접근하지 않는다.
- 로그인, 채팅, 개인 계정 영역은 접근하지 않는다.
- 연락처, 계정명, 상세 위치 같은 개인정보는 저장하지 않는다.
- 요청 간격을 두고 소량만 수집한다.
- 사이트 정책이 불명확하면 `확인 필요`로 표시하고 샘플 데이터를 사용한다.

## 중고나라 수집 실행 방법

중고나라 공개 상품 수집은 수동 스크립트로 실행한다.

```powershell
.\.venv\Scripts\python.exe scripts\crawl_joongna.py --keyword "나이키 후드티" --category "의류" --brand "Nike" --product-name "후드티" --limit 8 --source-category-contains "패션의류"
```

실행 결과는 아래 두 곳에 저장된다.

- CSV: `data/processed/joongna_market_items.csv`
- SQLite: `data/app.db`

같은 `source`와 `product_key`의 기존 중고나라 데이터는 기본적으로 교체한다.
기존 데이터를 유지하고 추가하려면 `--keep-existing` 옵션을 붙인다.
