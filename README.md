# Trend Digest MVP

FastAPI 기반 AI/테크 트렌드 다이제스트 백엔드입니다. Hacker News·GitHub(mock) 수집 → 정규화·점수화 → 목 요약 → PostgreSQL 저장 → Discord 웹훅 전송을 수행하며, APScheduler로 **`SCHEDULER_TZ`(기본 `Asia/Seoul`) 기준 매일 10:00** 에 자동 실행됩니다.

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

   **`502 Bad Gateway` 일 때:** `docker compose ps` 로 `app` 이 `Up` 인지 확인합니다. `Restarting` 이면 `docker compose logs app` 으로 DB·`.env`(특히 `DATABASE_URL` 호스트 `db`)를 확인하세요. 그다음 `docker compose up -d --build` 또는 `docker compose restart app nginx` 로 다시 올립니다.

4. EC2 등 원격 서버

   아래 **[EC2 (Ubuntu) 배포](#ec2-ubuntu-배포)** 절차를 따릅니다.

## EC2 (Ubuntu) 배포

서버에 **Docker Engine**과 **Docker Compose 플러그인**만 있으면 됩니다(호스트에 Python/Postgres를 따로 설치할 필요 없음).

### 1) EC2 준비

- **AMI**: Ubuntu 22.04 LTS 등
- **보안 그룹 인바운드**
  - **22** / TCP — SSH (가능하면 **본인 공인 IP만** 허용)
  - **80** / TCP — HTTP(nginx). 운영 전에는 IP 제한이나 나중에 **443 HTTPS**를 권장합니다.
- **키 페어**: `.pem` 은 로컬에만 두고 `chmod 400 your-key.pem`

SSH 예시:

```bash
ssh -i /path/to/your-key.pem ubuntu@<EC2_공인_IP>
```

### 2) Docker 설치 (Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${VERSION_CODENAME:-$VERSION_ID}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
```

`usermod` 후에는 **로그아웃 후 다시 SSH** 해야 `docker` 명령을 `sudo` 없이 씁니다.

### 3) 코드 올리기

한 가지 방법만 쓰면 됩니다.

**A. Git**

```bash
cd ~
git clone https://github.com/<계정>/trending-news.git
cd trending-news
```

**B. 로컬에서 압축 후 scp**

```bash
# 로컬 PC에서 (.git 제외 등)
tar czvf trending-news.tar.gz trending-news
scp -i your-key.pem trending-news.tar.gz ubuntu@<EC2_IP>:~/
# 서버에서
ssh ubuntu@<EC2_IP>
tar xzvf trending-news.tar.gz && cd trending-news
```

### 4) `.env` 만들기

서버의 프로젝트 **루트**에 `.env` 를 두고, **Git에 커밋하지 않습니다.**

```bash
cp .env.example .env
nano .env   # 또는 vim
```

**Docker Compose 안에서** DB 호스트 이름은 반드시 **`db`** 여야 합니다.

```env
DATABASE_URL=postgresql+asyncpg://trending:<비밀번호>@db:5432/trending
POSTGRES_USER=trending
POSTGRES_PASSWORD=<위와_동일>
POSTGRES_DB=trending
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
UPSTAGE_API_KEY=...
SCHEDULER_TZ=Asia/Seoul
```

### 5) 기동

```bash
docker compose up -d --build
docker compose ps
docker compose logs app --tail 30
```

### 6) 동작 확인

브라우저 또는 다른 터미널에서:

```bash
curl -s http://<EC2_공인_IP>/health
```

`{"status":"ok","database":"ok"}` 형태면 정상입니다. 스케줄은 **서울 기준 매일 10:00** 에 한 번 돌아갑니다.

### 7) 코드/설정 반영·재시작

```bash
cd ~/trending-news
git pull   # Git 쓰는 경우
docker compose up -d --build
```

`.env` 만 바꾼 경우:

```bash
docker compose up -d
```

### 8) 자주 쓰는 명령

```bash
docker compose logs -f app
docker compose restart app nginx
docker compose down          # 컨테이너 중지(볼륨 유지)
docker compose down -v       # DB 볼륨까지 삭제 — 데이터 초기화
```

---

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
