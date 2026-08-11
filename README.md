# starchive

영화와 책을 한곳에서 찾고 기록하는 서비스

[웹](https://starchive-front.vercel.app) · [API](https://starchive-psi.vercel.app) · [API 문서](https://starchive-psi.vercel.app/docs)

<br>

## 데이터

영화는 TMDB, 책은 알라딘에서 모아 한 테이블에 담았다. 매체가 달라도 같은 방식으로
찾고, 거르고, 기록한다.

| | 수집 기준 | 건수 |
|---|---|---|
| 영화 | MovieLens 평점 수 상위 3,000편 → TMDB 상세 | 2,988 |
| 책 | 알라딘 국내도서 베스트셀러 | 1,075 |

<br>

## 구조

```
starchive/
├── backend/    FastAPI · SQLAlchemy · Alembic
│   ├── app/
│   │   ├── core/          설정, DB 엔진, 외부 API 클라이언트
│   │   ├── domains/       도메인별 모델·스키마·라우터
│   │   └── ingestion/     수집 정규화
│   └── scripts/           수집 실행 스크립트
└── web/        Next.js 16 · Tailwind 4
    └── src/
        ├── app/           라우트
        ├── components/    UI
        └── lib/           API 클라이언트
```

**DB** — Neon(Postgres). `pgvector` 확장을 켜뒀고 임베딩 컬럼이 비어 있는 상태다.

**한 테이블** — 영화·책·웹툰을 `contents` 하나에 담고 `type` 으로 구분한다. 매체별
고유 필드는 `content_metadata`(JSONB). 사용자 기록·리뷰가 FK 하나로 연결되고,
벡터 검색이 매체 구분 없이 한 쿼리로 돈다.

**서버 컴포넌트** — 데이터 조회는 Next 서버에서 일어난다. 브라우저는 API 주소를
모르고 CORS 를 타지 않는다.

<br>

## 시작

**요구 사항** — Python 3.11+ ([uv](https://docs.astral.sh/uv/)), Node 20+, Neon 계정

### 백엔드

```bash
cd backend
cp .env.example .env      # 값 채우기
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs`

### 프론트

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

`http://localhost:3000`

> 명령은 각 디렉터리 안에서 실행한다. `pyproject.toml` 과 `package.json` 이
> 하위에 있어 저장소 루트에서는 설정을 찾지 못한다.

<br>

## 환경변수

**`backend/.env`**

| 키 | 용도 |
|---|---|
| `DATABASE_URL` | Neon **pooler** 주소. API 서버용 |
| `DIRECT_URL` | Neon 직접 연결. 마이그레이션·대량 적재용 |
| `JWT_SECRET` | 토큰 서명 |
| `TMDB_API_KEY` | 영화 수집 |
| `ALADIN_TTB_KEY` | 책 수집 |
| `FRONTEND_ORIGIN` | CORS 허용 출처 |

**`web/.env.local`**

| 키 | 용도 |
|---|---|
| `NEXT_PUBLIC_API_URL` | 백엔드 주소. `https://` 포함, 끝에 `/` 없이 |

`NEXT_PUBLIC_` 값은 빌드 시점에 코드로 들어간다. 변경 후 재배포가 필요하다.

<br>

## 수집 스크립트

```bash
cd backend
uv run python -m scripts.ingest_movies    # 6~8분
uv run python -m scripts.ingest_books     # 3분
```

`id` 충돌 시 갱신한다(upsert). 삭제는 하지 않으므로 베스트셀러 목록이 바뀌면
누적된다.

<br>

## API

| | |
|---|---|
| `GET /contents` | 목록 |
| `GET /contents/genres` | 타입별 장르 목록. 실제 데이터에 있는 것만 빈도순 |
| `GET /contents/{id}` | 상세 |
| `GET /health` | 헬스체크 |

**`GET /contents` 파라미터**

| | |
|---|---|
| `q` | 제목 부분 일치 |
| `type` | `MOVIE` / `BOOK` / `WEBTOON` |
| `genre` | 장르 정확히 일치 |
| `sort` | `popular`(기본) / `rating` / `recent` |
| `order` | `desc`(기본) / `asc` |
| `page`, `size` | 1부터, 1~100 |

응답의 `total` 은 현재 페이지가 아니라 필터에 걸린 전체 개수다.

`sort=rating` 은 평가 수 100 미만을 제외한다. 표본이 적은 평점은 신뢰할 수 없다.

`external_popularity` 는 소스마다 의미가 다르다(TMDB 평가 수 / 알라딘 판매 지수).
같은 `type` 안에서만 비교할 수 있다.

<br>

## 테스트

```bash
cd backend
uv run pytest -q -m "not db and not external"    # 빠른 것만
uv run pytest -q                                  # 전체
```

| 마커 | 필요한 것 |
|---|---|
| — | 없음 |
| `db` | Neon 연결 |
| `external` | TMDB · 알라딘 API |

```bash
cd web
npx tsc --noEmit
npx eslint .
```

<br>

## 배포

Vercel 프로젝트 2개. 같은 저장소에 Root Directory 만 다르게 잡는다.

| 프로젝트 | Root Directory |
|---|---|
| API | `backend` |
| 웹 | `web` |

`backend/api/index.py` 가 Vercel 진입점이다. `app` 을 재노출하는 것이 역할이라
정적 분석에서는 미사용으로 잡힌다. ruff 는 `per-file-ignores` 로 예외 처리했다.

<br>

## 앞으로

- [ ] 사용자 · 인증 — 본 것 체크가 현재 localStorage 에만 저장된다
- [ ] 임베딩 기반 추천 — `embedding` 컬럼이 비어 있다
- [ ] 의미 장르 — TMDB 는 정서 장르, 알라딘은 서가 분류라 매체 간 장르가 겹치지 않는다
