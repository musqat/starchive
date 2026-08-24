# 개발

로컬 실행·수집·테스트·배포. 서비스 설계는 [README](../README.md) 참고.

- [시작](#시작)
- [환경변수](#환경변수)
- [수집 스크립트](#수집-스크립트)
- [API](#api)
- [테스트](#테스트)
- [배포](#배포)

<br>

## 시작

Python 3.11+ ([uv](https://docs.astral.sh/uv/)), Node 20+, Docker 가 필요하다.
명령은 각 디렉터리 안에서 실행한다.

**백엔드**

```bash
cd backend
cp .env.example .env      # 값 채우기
docker compose up -d      # 로컬 Postgres + pgvector
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
| `DATABASE_URL` | **pooler** 트랜잭션 모드(6543). API 서버용 |
| `DIRECT_URL` | pooler 세션 모드(5432). 마이그레이션·대량 적재용 |
| `JWT_SECRET` | 토큰 서명 |
| `COOKIE_SECURE` | 배포는 `true`. https 에서만 쿠키를 보낸다 |
| `TMDB_API_KEY` | 영화 수집 |
| `ALADIN_TTB_KEY` | 책 수집 |
| `OPENAI_API_KEY` | 임베딩과 재랭킹 |
| `CRON_SECRET` | 배치 갱신 인증. Vercel 이 Bearer 로 자동 첨부한다 |
| `FRONTEND_ORIGIN` | CORS 허용 출처 |

`OPENAI_API_KEY` 가 없으면 500 이 아니라 점수순 폴백으로 떨어진다. 추천은 나오지만
이유 문장이 고정 문구가 되고 화면에서는 이유 줄이 사라진다.

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
uv run python -m scripts.ingest_recent    # 2018년 이후 영화
uv run python -m scripts.ingest_seed      # MovieLens 평점 → 시드 계정
uv run python -m scripts.embed --apply    # 임베딩 (영화는 분위기 문장 포함)
```

`id` 충돌 시 갱신한다(upsert). 삭제는 하지 않으므로 베스트셀러 목록이 바뀌면
누적된다. `embed` 는 임베딩이 없는 것만 처리해 여러 번 돌려도 된다.

**추천**

```bash
uv run python -m scripts.recommend --apply         # 배치 생성
uv run python -m scripts.evaluate                  # Recall/NDCG · 무료
uv run python -m scripts.evaluate_rerank           # 재랭킹 전후 · 사용자 수만큼 호출
```

평가는 기록을 트랜잭션 안에서 지우고 롤백한다.

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
| `db` | DB 연결. `docker compose up -d` 면 된다 |
| `external` | TMDB · 알라딘 API |

**배포 의존성** — Vercel 은 `[project].dependencies` 만 설치한다. `app/` 이 `dev`·`etl` 그룹의
패키지를 쓰면 로컬 테스트는 통과하고 배포만 죽는다.

```bash
cd backend
uv run --no-dev --no-group etl python -c "from app.main import app"
```

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

**Cron** — `backend/vercel.json` 이 하루 한 번 `GET /recommendations/cron` 을 부른다.
