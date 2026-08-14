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
    ├── e2e/           Playwright
    └── src/
        ├── app/           라우트
        ├── components/    UI
        └── lib/           타입, API 클라이언트
```

**DB** — Neon(Postgres)

**한 테이블** — 영화·책·웹툰을 `contents` 하나에 담고 `type` 으로 구분한다. 매체별
고유 필드는 `content_metadata`(JSONB). 사용자 기록이 FK 하나로 연결된다.

**같은 출처** — 브라우저는 `/api` 로만 요청하고 `next.config.ts` 의 rewrite 가 백엔드로
넘긴다. 인증 쿠키가 프론트 도메인에 저장돼야 서버 컴포넌트가 `cookies()` 로 읽는다.

<br>

## 시작

Python 3.11+ ([uv](https://docs.astral.sh/uv/)), Node 20+, Neon 계정이 필요하다.
명령은 각 디렉터리 안에서 실행한다.

**백엔드**

```bash
cd backend
cp .env.example .env      # 값 채우기
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**프론트**

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

`http://localhost:3000`

<br>

## 환경변수

**`backend/.env`**

| 키 | 용도 |
|---|---|
| `DATABASE_URL` | Neon **pooler** 주소. API 서버용 |
| `DIRECT_URL` | Neon 직접 연결. 마이그레이션·대량 적재용 |
| `JWT_SECRET` | 토큰 서명 |
| `COOKIE_SECURE` | 배포는 `true`. https 에서만 쿠키를 보낸다 |
| `TMDB_API_KEY` | 영화 수집 |
| `ALADIN_TTB_KEY` | 책 수집 |
| `FRONTEND_ORIGIN` | CORS 허용 출처 |

**`web/.env.local`**

| 키 | 용도 |
|---|---|
| `BACKEND_ORIGIN` | 백엔드 주소. `https://` 포함, 끝에 `/` 없이 |

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

전체 목록과 파라미터는 [`/docs`](https://starchive-psi.vercel.app/docs) 참고

- `GET /contents` 응답의 `total` 은 현재 페이지가 아니라 필터에 걸린 전체 개수다
- `sort=rating` 은 평가 수 100 미만을 제외한다. 표본이 적은 평점은 신뢰할 수 없다
- `external_popularity` 는 소스마다 의미가 다르다(TMDB 평가 수 / 알라딘 판매 지수).
  같은 `type` 안에서만 비교할 수 있다
- `unseen=1` 은 로그인했을 때만 동작한다. 비로그인이면 무시된다

<br>

## 테스트

**백엔드** — pytest. FastAPI 를 같은 프로세스에서 호출한다.

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

**프론트** — 타입·린트.

```bash
cd web
npm run typecheck
npm run lint
```

**E2E** — Playwright. 브라우저부터 DB 까지 관통하므로 백엔드가 떠 있어야 한다.

```bash
npx playwright install chromium    # 최초 1회

cd backend && uv run uvicorn app.main:app --reload    # 다른 터미널
cd web && npm run e2e
```

<br>

## 배포

Vercel 프로젝트 2개. 같은 저장소에 Root Directory 만 다르게 잡는다.

| 프로젝트 | Root Directory |
|---|---|
| API | `backend` |
| 웹 | `web` |

`backend/api/index.py` 가 Vercel 진입점

