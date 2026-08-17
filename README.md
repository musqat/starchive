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

줄거리가 있는 것은 `text-embedding-3-small` 로 임베딩해 `vector(1536)` 에 담는다.
제목·장르·작가를 줄거리 앞에 붙여 넣는다 — 알라딘 책소개는 홍보 문구가 섞여 있어
줄거리만 넣으면 내용이 묻힌다.

<br>

## 추천

영화와 책을 따로 낸다.

```
평점 4.0 이상인 기록  →  취향 중심 (임베딩 평균)
                          ↓
              내용 점수 0.3   줄거리가 취향 중심과 가까운 것
              이웃 점수 0.7   나와 겹치는 사람들이 좋아한 것
                          ↓
                      후보 30개
                          ↓
              gpt-4o-mini 재랭킹  →  10개 + 이유 한 문장
```

배치로 만들어 저장하고, 화면은 저장된 것만 읽는다. 하루 한 번 갱신하고 사용자가
직접 다시 만들 수도 있다(쿨다운 60분).

### 측정

시드 610명(MovieLens 평점 86,604건). 기록의 20% 를 가리고 상위 10에서 몇 개를
되찾는지 본다. 인기순을 같은 조건으로 나란히 재 비교 기준으로 쓴다.

**Recall@10** 가린 기록 중 상위 10에 든 비율 · **NDCG@10** 적중 순위가 앞설수록 커지는 값

| 내용:이웃 | Recall@10 | NDCG@10 |
|---|---|---|
| 0.7:0.3 | 0.021 | 0.046 |
| 0.5:0.5 | 0.112 | 0.171 |
| **0.3:0.7** | **0.130** | **0.240** |
| 0.0:1.0 | 0.131 | 0.243 |
| 인기순 | 0.097 | 0.190 |

처음 잡은 `0.7:0.3` 은 인기순에 4.6배 졌다. 두 점수의 범위가 달라서다 — 내용 점수는
바닥이 0.35, 이웃 점수는 0 까지 내려간다. 추천의 75.5% 가 이웃 점수 0 인 항목이었다.

`0.0:1.0` 이 근소하게 높지만 `0.3:0.7` 을 쓴다. 커버리지가 90편에서 97편으로 넓고,
내용 점수 경로가 살아 있어야 신작을 다룰 수 있다.

### 몇 편을 기록해야 하나

정답 20개를 고정하고 남기는 편수만 움직였다.

| 남긴 편수 | Recall@10 | 인기순 |
|---|---|---|
| 2 | 0.028 | 0.039 |
| 3 | 0.039 | 0.040 |
| **5** | **0.049** | 0.040 |
| 20 | 0.050 | 0.041 |
| 50 | 0.059 | 0.050 |

2편은 인기순보다 나쁘고 3편은 동점이다. **5편부터 앞선다.** 화면과 API 가 이 숫자로 막는다.

5편 이후가 평평하다. 취향 중심이 평균이라 기록이 쌓일수록 가운데로 모이는 것으로 보인다.

### 재랭킹이 하는 일

시드 50명, 같은 홀드아웃.

| | Recall@10 | NDCG@10 | 서로 다른 작품 | 상위 10편 점유 |
|---|---|---|---|---|
| 점수순 | 0.120 | 0.216 | 67 | 44.8% |
| 재랭킹 | 0.120 | 0.218 | 85 | 32.6% |

순서는 바뀌지 않았다. 50명 중 NDCG 가 오른 쪽이 19명, 내린 쪽이 15명이다.
대신 서로 다른 작품이 27% 늘고 쏠림이 12%p 줄었다. 자리의 45% 를 바꾸는데도 Recall 이
그대로라는 것은, 점수 11~30위와 1~10위의 품질 차이가 크지 않다는 뜻이다.

### 안 되는 것

- **매체를 넘지 못한다** — 영화 취향으로 책을 줄 세우면 위쪽이 전부 만화다.
  만화 소개가 TMDB 줄거리와 형식이 같기 때문이다
- **책 추천은 잴 수 없다** — 책에는 평점 데이터가 없다
- **같은 작품을 돌려쓴다** — 2,988편 중 90편 안팎만 추천에 등장한다
- **신작이 안 나온다** — 시드가 평가한 적 없어 이웃 점수가 0 이다

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
uv run python -m scripts.ingest_seed      # MovieLens 평점 → 시드 계정
uv run python -m scripts.embed --apply    # 줄거리 임베딩
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
| `db` | Neon 연결 |
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


