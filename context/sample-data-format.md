# 샘플 데이터 형식

## 목적

이 문서는 프로젝트에서 사용할 샘플 데이터 형식을 정리한다.
샘플 데이터는 시세 그래프와 가격 계산을 먼저 구현하고 시연하기 위한 기준 데이터다.
웹사이트는 실시간 크롤링 결과가 아니라 저장된 샘플 또는 정리 데이터를 읽는다.

## 최종 결정

이번 프로젝트는 `CSV + SQLite` 조합을 사용한다.

- CSV: 팀원이 직접 보고 수정하는 샘플 데이터
- SQLite: 웹사이트가 실제로 조회하는 데이터
- JSON: 크롤링 원본을 남길 때만 선택적으로 사용
- 대표 상품 1개당 샘플 데이터는 5개만 준비

CSV는 엑셀처럼 열어 보기 쉽다.
SQLite는 Python과 Flask에서 읽기 쉽고, 조건 검색과 그래프 데이터 조회에 적합하다.

## 파일 위치

```txt
data/
├─ sample/
│  └─ market_items.csv
├─ raw/
│  ├─ daangn_sample.json
│  ├─ joongna_sample.json
│  ├─ bunjang_sample.json
│  └─ kream_sample.json
├─ processed/
│  └─ market_items.csv
└─ app.db
```

각 파일의 역할은 아래와 같다.

| 파일 | 역할 | 필수 여부 |
| --- | --- | --- |
| data/sample/market_items.csv | 사람이 직접 작성하거나 수정하는 샘플 데이터 | 필수 |
| data/processed/market_items.csv | 크롤링 후 정규화된 결과 CSV | 권장 |
| data/raw/*_sample.json | 사이트별 원본 데이터 예시 | 선택 |
| data/app.db | 웹사이트가 읽는 SQLite 데이터베이스 | 필수 |

초기 개발에서는 `data/sample/market_items.csv`를 먼저 만든다.
그다음 같은 내용을 `data/app.db`에 넣어 웹사이트에서 사용한다.

## CSV 기준 컬럼

`market_items.csv`는 상품 하나를 한 줄로 저장한다.
컬럼은 아래 순서를 기준으로 한다.

```csv
id,raw_item_id,source,collected_keyword,source_item_id,source_url,title,normalized_title,product_name,category,source_category,brand,model_name,product_key,item_condition,components,price,currency,trade_status,source_status,listed_at,sold_at,location,shipping_fee,trade_method,image_url,description,crawled_at
```

컬럼 의미는 아래와 같다.

| 컬럼 | 의미 | 예시 | 필수 여부 |
| --- | --- | --- | --- |
| id | 샘플 데이터 안의 고유 번호 | 1 | 필수 |
| raw_item_id | 원본 데이터 ID | 1 | 선택 |
| source | 데이터 출처 | daangn | 필수 |
| collected_keyword | 수집에 사용한 검색어 | 나이키 후드티 | 권장 |
| source_item_id | 원본 사이트의 글 또는 상품 ID | D-001 | 권장 |
| source_url | 원본 링크 | https://example.com/item/1 | 권장 |
| title | 원본 제목 | 나이키 후드티 판매합니다 | 필수 |
| normalized_title | 비교용으로 정리한 제목 | 나이키 후드티 판매합니다 | 권장 |
| product_name | 정리한 상품명 | 나이키 후드티 | 필수 |
| category | 카테고리 | 의류 | 필수 |
| source_category | 원본 사이트의 카테고리 | 패션의류 > 남성의류 | 선택 |
| brand | 브랜드 | Nike | 선택 |
| model_name | 모델명 | 확인 필요 | 선택 |
| product_key | 같은 상품을 묶는 기준값 | 의류:nike:후드티 | 필수 |
| item_condition | 상품 상태 | 사용감 적음 | 권장 |
| components | 구성품 | 단품 | 선택 |
| price | 가격 | 35000 | 필수 |
| currency | 통화 | KRW | 필수 |
| trade_status | 거래 상태 | 판매완료 | 권장 |
| source_status | 원본 사이트에서 읽은 거래 상태 | 판매중 | 선택 |
| listed_at | 게시일 | 2026-05-20 | 권장 |
| sold_at | 거래일 | 2026-05-25 | 선택 |
| location | 지역 | 서울 강남구 | 선택 |
| shipping_fee | 배송비 | 3000 | 선택 |
| trade_method | 거래 방식 | 택배거래, 직거래 | 선택 |
| image_url | 대표 이미지 주소 | https://example.com/image.jpg | 선택 |
| description | 설명 요약 | 착용 3회 | 선택 |
| crawled_at | 수집 시각 | 2026-05-29 12:00:00 | 필수 |

## CSV 예시

```csv
id,raw_item_id,source,collected_keyword,source_item_id,source_url,title,normalized_title,product_name,category,source_category,brand,model_name,product_key,item_condition,components,price,currency,trade_status,source_status,listed_at,sold_at,location,shipping_fee,trade_method,image_url,description,crawled_at
1,,joongna,나이키 후드티,227159992,https://web.joongna.com/product/227159992,나이키 후드티 95,나이키 후드티 95,후드티,의류,패션의류 > 남성의류 > 티셔츠,Nike,,의류:nike:후드티,중고,구성품 전체 포함,13000,KRW,판매중,판매중,,,,2000,택배거래,https://example.com/image.jpg,상태 좋아요,2026-05-29 12:00:00
```

## SQLite 기준

웹사이트는 최종적으로 `data/app.db`를 읽는다.
SQLite에는 아래 테이블을 둔다.

| 테이블 | 역할 |
| --- | --- |
| market_items | 정리된 상품 데이터 |
| price_snapshots | 시세 그래프용 가격 데이터 |
| raw_items | 크롤링 원본 데이터 |
| crawl_runs | 크롤링 실행 기록 |

초기 개발에서는 `market_items`와 `price_snapshots`만 있어도 시세 그래프를 만들 수 있다.
`raw_items`와 `crawl_runs`는 크롤링 파트를 붙일 때 사용한다.

## JSON 사용 기준

JSON은 필수가 아니다.
크롤링 원본을 남길 때만 사용한다.

사용 예시는 아래와 같다.

- 사이트별 원본 필드가 서로 다를 때
- 나중에 정규화 기준을 바꿀 가능성이 있을 때
- 발표에서 원본 수집 결과와 정리 결과를 비교해 보여줄 때

원본 JSON에는 개인정보를 넣지 않는다.
판매자 실명, 전화번호, 채팅 내용, 상세 주소는 저장하지 않는다.

## 작성 규칙

- 가격은 숫자만 넣는다.
- 통화는 `KRW`로 통일한다.
- 날짜는 `YYYY-MM-DD` 형식을 사용한다.
- 날짜와 시간이 함께 필요하면 `YYYY-MM-DD HH:MM:SS` 형식을 사용한다.
- 알 수 없는 값은 비워 두거나 `확인 필요`로 표시한다.
- `product_key`는 같은 상품 비교 기준에 맞춰 직접 입력한다.
- `source_category`는 원본 사이트의 카테고리다. 프로젝트 카테고리인 `category`와 다를 수 있다.
- `shipping_fee`는 숫자만 넣는다.
- 개인정보가 섞인 설명은 저장 전에 제거한다.
- 샘플 데이터는 최소 5개 이상 있어야 시세 범위를 계산할 수 있다.
- 이번 과제에서는 대표 상품 1개당 샘플 5개를 기본으로 준비한다.

## 사용 흐름

1. 팀원이 `data/sample/market_items.csv`를 작성한다.
2. 같은 상품끼리 `product_key`를 맞춘다.
3. 가격, 상태, 거래 상태를 확인한다.
4. CSV 데이터를 `data/app.db`에 넣는다.
5. 웹사이트는 `data/app.db`를 읽어서 시세 그래프를 보여준다.
6. 크롤러가 완성되면 `data/processed/market_items.csv`를 만들고 같은 방식으로 SQLite에 넣는다.

## 확인 필요

- `source_url`에 실제 원본 링크를 넣을지 예시 링크를 넣을지
- `image_url`에 실제 이미지 링크를 넣을지 로컬 샘플 이미지를 쓸지
