# Trend Digest MVP

FastAPI 기반 AI/테크 트렌드 다이제스트 백엔드입니다. Hacker News·GitHub(mock) 수집 → 정규화·점수화 → 목 요약 → PostgreSQL 저장 → Discord 웹훅 전송을 수행하며, APScheduler로 **월·수·금 08:00 (`SCHEDULER_TZ`, 기본 `Asia/Seoul`)** 에 자동 실행됩니다.

## 스택

- Python 3.11+ (Dockerfile는 3.11 고정)
- FastAPI, Uvicorn, SQLAlchemy 2.0(async) + asyncpg, Alembic, Pydantic v2, httpx, APScheduler

## 빠른 시작 (Docker)

1. 루트에 `.env` 파일을 만들고 아래를 채웁니다 (`.env.example` 참고).

   - `DISCORD_WEBHOOK_URL`: Discord Incoming Webhook **전체 URL** (저장소에 넣지 말 것)
   - `DATABASE_URL`: compose 기본값과 같으면 생략 가능하지만, 앱 컨테이너에는 compose가 주입합니다.

2. 실행

   ```bash
   docker compose up -d --build
   ```

3. 접속

   - API(nginx 경유): `http://localhost/health`
   - 앱은 네트워크 내부 `app:8000`만 노출하고, 외부는 **nginx 80** 포트만 엽니다.

4. EC2 등 서버 배포 시

   - 동일하게 저장소와 `.env`를 두고 `docker compose up -d` 실행
   - 호스트·컨테이너 `TZ=Asia/Seoul` (compose에 반영됨)
   - 보안 그룹에서 **22(SSH), 80(HTTP)** 를 열고, 운영 전에 관리망 제한·HTTPS(443) 적용을 권장합니다.

## 로컬 개발 (Postgres 별도)

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env   # DATABASE_URL, DISCORD_WEBHOOK_URL 수정
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스(DB `SELECT 1`) |
| POST | `/jobs/run-digest` | 다이제스트 수동 실행 (202, `job_run_id`) |
| GET | `/digests` | 최근 다이제스트 목록 |
| GET | `/digests/{id}` | 상세 |

수동 실행 예:

```bash
curl -X POST http://localhost/jobs/run-digest -H "Content-Type: application/json" -d "{\"routine_type\":\"tech_trend\"}"
```

`routine_type`: `global_ai` | `tech_trend` | `community_trend`

## 마이그레이션

컨테이너 기동 시 `alembic upgrade head`가 엔트리포인트에서 자동 실행됩니다. 로컬에서만 실행할 때는 `DATABASE_URL`이 Alembic용으로 `+psycopg2`로 치환됩니다(`alembic/env.py`).

## 비밀·키 관리

- `.pem` SSH 키와 Discord 웹훅 URL은 **Git에 커밋하지 마세요** (`.gitignore`에 `*.pem`, `.env` 포함).
- 웹훅 URL이 유출되면 Discord에서 웹훅을 삭제 후 재발급하세요.

## 백업

Postgres 볼륨(`postgres_data`) 스냅샷은 운영 단계에서 별도 정책을 두면 됩니다. MVP 단계에서는 필수 아님.
