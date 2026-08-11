# starchive

영화·책을 한곳에서 찾고 기록하는 서비스

| | 주소 |
|---|---|
| 웹 | (배포 예정) |
| API | (배포 예정) |
| API 문서 | (배포 예정)`/docs` |

## 구성

```
backend/   FastAPI + SQLAlchemy + Neon(Postgres, pgvector)
web/       Next.js 16 + Tailwind 4
```

## 데이터

| 타입 | 출처 | 수집 기준 |
|---|---|---|
| MOVIE | TMDB | MovieLens 평점 수 상위 3,000편 |
| BOOK | 알라딘 | 국내도서 베스트셀러 |

`contents` 한 테이블에 타입 구분해서 저장. 타입별 고유 필드는 `content_metadata`(JSONB)로 분리

## 실행

두 서버 모두 각자 디렉터리 안에서 실행

**백엔드**

```bash
cd backend
uv sync --all-groups
uv run uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs` 에서 API 문서 확인

**프론트**

```bash
cd web
npm install
npm run dev
```

`http://localhost:3000`

## 환경변수

`backend/.env` — `backend/.env.example` 참고

| 키 | 용도 |
|---|---|
| `DATABASE_URL` | Neon pooler. API 서버용 |
| `DIRECT_URL` | Neon 직접 연결. 마이그레이션·대량 적재용 |
| `JWT_SECRET` | 인증 |
| `TMDB_API_KEY` | 영화 수집 |
| `ALADIN_TTB_KEY` | 책 수집 |
| `FRONTEND_ORIGIN` | CORS 허용 출처 |

`web/.env.local`

| 키 | 용도 |
|---|---|
| `NEXT_PUBLIC_API_URL` | 백엔드 주소 |

## 데이터 수집

```bash
cd backend
uv run python -m scripts.ingest_movies
uv run python -m scripts.ingest_books
```

id 충돌 시 갱신하므로 여러 번 실행해도 중복이 생기지 않음

## 테스트

```bash
cd backend
uv run pytest -q -m "not db and not external"
```

| 마커 | 필요한 것 |
|---|---|
| 없음 | — |
| `db` | Neon 연결 |
| `external` | TMDB·알라딘 API |

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /contents` | 목록. `q` `type` `genre` `sort` `order` `page` `size` |
| `GET /contents/genres` | 타입별 장르 목록 |
| `GET /contents/{id}` | 상세 |
| `GET /health` | 헬스체크 |

`sort` 는 `popular`(기본) / `rating` / `recent`, `order` 는 `desc`(기본) / `asc`

`external_popularity` 는 소스마다 의미가 다름 (TMDB 평가 수 / 알라딘 판매 지수).
같은 `type` 안에서만 비교 가능
