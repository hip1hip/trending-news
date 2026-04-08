# Trend Digest MVP

FastAPI 기반 AI/테크 트렌드 다이제스트 백엔드입니다. Hacker News·GitHub(mock) 수집 → 정규화·점수화 → 목 요약 → PostgreSQL 저장 → Discord 웹훅 전송을 수행하며, APScheduler로 **월·수·금 08:00 (`SCHEDULER_TZ`, 기본 `Asia/Seoul`)** 에 자동 실행됩니다.

## 스택

- Python 3.11+ (Dockerfile는 3.11 고정)
- FastAPI, Uvicorn, SQLAlchemy 2.0(async) + asyncpg, Alembic, Pydantic v2, httpx, APScheduler

## 빠른 시작 (Docker)

1. 루트에 `.env` 파일을 만듭니다: `.env.example`을 복사한 뒤 **반드시** 채웁니다.

   - `POSTGRES_PASSWORD`: DB 비밀번호 (추측 불가능하게)
   - `DATABASE_URL`: 위 비밀번호와 동일하게 URL 안에 반영 (`postgresql+asyncpg://USER:PASSWORD@db:5432/DB`)
   - `DISCORD_WEBHOOK_URL`: Discord Incoming Webhook 전체 URL
   - `UPSTAGE_API_KEY`(선택): 설정 시 Upstage **solar-pro3** 로 한국어 요약·항목별 요약 생성. 없으면 목 요약만 사용합니다.

   공개 배포·보안 체크리스트는 [SECURITY.md](SECURITY.md)를 참고하세요.

2. 실행

   ```bash
   docker compose up -d --build
   ```

   **Windows 참고:** 셸이나 시스템에 `DATABASE_URL` 등이 이미 잡혀 있으면, 예전 방식의 `${DATABASE_URL}` 치환은 `.env`가 아니라 **호스트 값**이 들어가 `localhost`로 붙는 경우가 있습니다. 현재 `docker-compose.yml`은 `db`/`app`에 `env_file: .env`로 **파일 내용을 그대로** 넣도록 되어 있어 이런 충돌을 피합니다.

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

- `.env`, `*.pem` 은 **Git에 올리지 마세요** (`.gitignore` 처리).
- `docker-compose.yml`에는 DB 비밀번호를 직접 적지 않습니다. 모두 `.env`에서만 주입합니다.
- Discord 웹훅 URL이 유출되면 Discord에서 웹훅을 삭제 후 재발급하세요.

## 백업

Postgres 볼륨(`postgres_data`) 스냅샷은 운영 단계에서 별도 정책을 두면 됩니다. MVP 단계에서는 필수 아님.
