# Heejae workspace

경매 사이트 외부 시세 검색용 크롤러 파일입니다.

- 당근마켓은 현재 환경에서 수집이 불안정해서 제외했습니다.
- 중고나라, 번개장터, KREAM 결과를 사용합니다.
- 원본 이미지가 비어 있으면 `image_fallback.py`가 상품명 기준으로 쓸만한 사진 URL을 자동으로 넣습니다.
- 웹 앱에서 `from market_scraper import IntegratedScraper` 형태로 바로 붙일 수 있게 `market_scraper.py`를 추가했습니다.

## 커밋 기록

- 업로드 브랜치: `heejae-work`
- 커밋 해시: `972254a`
- 커밋 일시: `2026-05-29 19:26:27 +0900`
- 커밋 메시지: `Add heejae market scraper with image fallback`
