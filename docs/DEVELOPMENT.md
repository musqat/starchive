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
패키지를 쓰면 로컬 테스트는 통과하고 배포만 죽는다. 실제로 한 번 죽었다. 재시도 라이브러리가
`etl` 그룹에 있었는데 재랭킹이 쓰기 시작하면서 런타임 의존이 됐고, 테스트 133개는 전부 통과했다.

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

**E2E** — Playwright. 브라우저부터 DB 까지 관통해서 백엔드를 먼저 띄운다.

```bash
npx playwright install chromium    # 최초 1회

cd backend && uv run uvicorn app.main:app --reload    # 다른 터미널
cd web && npm run e2e
```

**CI** — PR 마다 `.github/workflows/ci.yml` 이 돈다.

```
backend   pytest (db·external 제외) · 배포 의존성
web       빌드 · typecheck · lint
```

`db` 표시가 붙은 것과 E2E 는 안 돈다. Postgres 를 띄우고 백엔드를 기동해야 해서
로컬에서 돌린다. 프론트는 빌드를 먼저 한다 — `LayoutProps` 같은 라우트 타입을
`next` 가 빌드 때 만들어, 건너뛰면 `tsc` 가 못 찾는다.

<br>

## 배포

Vercel 프로젝트 2개. 같은 저장소에 Root Directory 만 다르게 잡는다.

| 프로젝트 | Root Directory |
|---|---|
| API | `backend` |
| 웹 | `web` |

`backend/api/index.py` 가 Vercel 진입점

**마이그레이션** — Vercel 은 alembic 을 돌리지 않는다. 로컬에서 `DIRECT_URL` 로 프로덕션 DB 에
직접 올린다.

```bash
cd backend
uv run alembic revision --autogenerate -m "add_xxx"    # 생성된 파일을 읽고 손본다
uv run alembic upgrade head                             # 로컬 DB 에 먼저
uv run pytest -q
DIRECT_URL=<Supabase 5432> uv run alembic upgrade head  # 프로덕션. PR 머지 전에
DIRECT_URL=<Supabase 5432> uv run alembic current      # head 인지 확인
```

순서는 스키마 먼저, 코드 나중. 머지하면 Vercel 이 바로 배포하는데 그 시점에 컬럼이 없으면 500 이다.
스키마가 먼저 가면 옛 코드는 새 컬럼을 모른 채 그대로 돈다. 그래서 변경은 옛 코드가 견디는
형태로 낸다. nullable 컬럼, 기본값 있는 컬럼, 인덱스, enum 값 추가. 이름 바꾸기와 컬럼 삭제는
새 컬럼 추가 → 코드 전환 → 옛 컬럼 삭제로 PR 을 셋으로 나눈다.

**Cron** — `backend/vercel.json` 이 하루 한 번 `GET /recommendations/cron` 을 부른다.

**전송량** — Supabase 무료 한도는 저장 0.5 GB, 전송 5 GB. 저장만 보고 있다가 전송량을 넘겨
18일을 멈춘 적이 있다. 평가를 프로덕션 DB 에 대고 열 번 넘게 돌린 탓이다.

```
저장   0.12 / 0.5 GB
전송   6.48 / 5 GB    ← 여기서 막혔다
```

원인은 취향 중심을 만들 때 임베딩을 파이썬으로 끌어와 평균을 낸 것이었다. 유저당 1536차원
벡터 수십 개, 기록 많은 사람은 1,588개(9.3MB). Postgres 집계로 내려 결과 벡터 하나(6KB)만
받게 고쳤고, 지표는 그대로였다. 평가는 로컬 DB 에서 돌리고, 스크립트가 원격을 향하면 연결 전에
멈춘다.

**감시** — 그때 `/health` 는 200 이었다. 앱은 살아 있고 DB 만 죽었는데 그걸 볼 길이 없었다.
지금은 `/health` 가 DB 에 쿼리 하나를 보내고, 안 받으면 5초 안에 503 을 낸다. 외부에서 5분마다
프론트 홈을 호출하고, 정상 응답이 아니면 메일로 알린다. 홈은 서버에서 목록을 불러오므로
백엔드나 DB 가 죽으면 같이 실패한다.

**Supabase REST** — Supabase 는 public 스키마를 PostgREST(`/rest/v1`) 로도 연다. 앱은 안 쓰지만
anon 키만 있으면 users 를 포함한 모든 테이블이 REST 로 읽히고 써진다. 마이그레이션
`f2a9c4d17b03` 이 테이블마다 RLS 를 정책 없이 켠다. anon·authenticated 는 0행, 앱은 테이블
소유자라 그대로다. 대시보드 Settings → API 의 Data API 도 끈다. 둘 다 있어야 키가 새도 막힌다.
