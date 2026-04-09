# LLM / 에이전트 핸드오프 문서

이 파일은 **사람용 README 대신**, 세션/스레드가 끊긴 뒤 다른 LLM 에이전트가 저장소 상태와 운영 맥락을 복원하기 위한 기술 스냅샷이다.  
**민감값(키, PEM, 웹훅 URL 전체)은 여기에 적지 않는다.**

---

## 1. 제품 / 목적

- **이름:** Trend Digest (trending-news)
- **역할:** Hacker News + GitHub 트렌딩(mock) 수집 → 정규화·점수화 → 요약(Upstage 또는 mock) → PostgreSQL 저장 → Discord Incoming Webhook 전송.
- **스케줄:** `SCHEDULER_TZ` 기본 `Asia/Seoul`, **매일 현지 10:00** (`app/jobs/scheduler.py` `CronTrigger(hour=10, minute=0)`).
- **수동 트리거:** `POST /jobs/run-digest` JSON `{"routine_type":"tech_trend"}` (또는 `global_ai`, `community_trend`). 202 + `job_run_id`.

---

## 2. 스택 / 런타임

- Python **3.11** (Dockerfile 고정)
- FastAPI, Uvicorn, SQLAlchemy 2 async + **asyncpg**, Alembic, Pydantic v2, httpx, APScheduler
- 배포: **Docker Compose** — `db` (Postgres 16), `app`, `nginx` (호스트 80 → 앱)
- DB URL: 컨테이너 간 호스트명 **`db`** (`DATABASE_URL`에 `@db:5432`)

---

## 3. 디렉터리 / 핵심 파일

| 경로 | 설명 |
|------|------|
| `app/main.py` | FastAPI, lifespan에서 스케줄러 setup/start/shutdown |
| `app/core/config.py` | `DATABASE_URL`, `DISCORD_WEBHOOK_URL` 필수; `UPSTAGE_API_KEY` 선택(비우면 mock 요약) |
| `app/jobs/scheduler.py` | 매일 10:00 `run_scheduled_digest_pipeline` |
| `app/services/digest_pipeline.py` | 파이프라인 본체; `Semaphore(1)`로 수동·스케줄 동시 실행 1개; Discord는 DB 커밋 후 전송 |
| `app/summarization/upstage_summarizer.py` | Upstage OpenAI 호환 API |
| `app/delivery/discord_webhook.py` | 임베드 분할·dedup |
| `docker-compose.yml` | `db`/`app`에 `env_file: .env` (호스트 `DATABASE_URL` 덮어쓰기 이슈 완화) |
| `nginx/default.conf` | 리버스 프록시 `app:8000` |
| `.github/workflows/ci-cd.yml` | CI: `ubuntu-latest`; CD: **self-hosted**, 레이블 **`trending-ec2`** |
| `.env.example` | 필수/선택 변수 템플릿 (실비밀 없음) |

---

## 4. 환경 변수 (이름만; 값은 커밋 금지)

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL` — asyncpg, 비밀번호는 `POSTGRES_PASSWORD`와 일치, 호스트 **`db`**
- `DISCORD_WEBHOOK_URL` — **필수**, 비우면 기동 실패
- `SCHEDULER_TZ` — 기본 `Asia/Seoul`
- `UPSTAGE_API_KEY` — 선택; 있으면 Upstage, 없으면 mock
- `UPSTAGE_MODEL`, `UPSTAGE_BASE_URL` — 선택, 기본 solar-pro3 / Upstage 베이스 URL

`.env`는 `.gitignore`에 있음. **`*.pem`도 gitignore.**

---

## 5. AWS EC2 운영 (누적 결정사항)

- **OS:** Ubuntu, 사용자 `ubuntu`, 앱 경로 **`~/trending-news`**
- **Docker:** 호스트에 Engine; 과거 Ubuntu 패키지에 compose 플러그인 없을 수 있음 → 공식 바이너리로 Compose v2 CLI 플러그인 설치한 적 있음 (`/usr/local/lib/docker/cli-plugins/docker-compose`)
- **퍼블릭 IPv4는 인스턴스 Stop/Start 시 변경될 수 있음** — 문서 시점 예: 이전 `3.38.211.184` → 이후 **`3.34.53.137`** 로 변경됨. **고정 IP가 필요하면 Elastic IP 할당 권장.**
- **보안 그룹:** SSH 22는 **본인·사무실 공인 IP 등으로 제한**한 선택을 함. GitHub 호스트 러너에서 SSH 배포는 불가 → **self-hosted runner로 전환.**
- **같은 인스턴스에 n8n(5678) 등 다른 컨테이너가 있을 수 있음** — 80은 nginx가 사용.

---

## 6. CI/CD (GitHub Actions)

- 워크플로: `.github/workflows/ci-cd.yml`
- **트리거:** `push`/`pull_request` → `main`
- **`ci` job:** `ubuntu-latest` — checkout, pip, `compileall app`, `docker compose build`
- **`deploy` job:** 조건 `push` + `refs/heads/main` + `github.event.repository.fork == false`; `needs: ci`; **`runs-on: [self-hosted, trending-ec2]`**
- **배포 스크립트 (EC2 러너에서 실행):** `cd ~/trending-news` → `git fetch origin main` → `git reset --hard origin/main` → `docker compose up -d --build`
- **SSH 시크릿(`EC2_HOST` 등)은 현재 워크플로에서 미사용** (과거 appleboy SSH 방식 제거됨).
- 러너 등록: GitHub **Linux x64**, 디렉터리 예 `~/actions-runner`, **`--labels trending-ec2`** 필수 (설정 시 스킵하면 UI에서 레이블 추가). **`sudo ./svc.sh install` / `start`** 권장.
- 공개 저장소 + self-hosted: PR의 CI는 `ubuntu-latest`만 사용; deploy는 `main` 푸시만.

---

## 7. 로컬 / 검증 명령 (에이전트가 재현할 때)

```bash
pip install -r requirements.txt
python -m compileall -q app
docker compose build
docker compose up -d
curl -s http://localhost/health
```

EC2에서 (SSH 가능한 환경에서만):

```bash
cd ~/trending-news && docker compose ps
curl -s http://127.0.0.1/health
```

`.env` 수정 후: `docker compose up -d` 또는 `docker compose restart app`

---

## 8. 알려진 이슈 / 주의

- **Windows OpenSSH:** PEM 파일 권한이 넓으면 키 무시 → `icacls`로 현재 사용자만 읽기 권한.
- **PowerShell:** `curl`은 `Invoke-WebRequest` 별칭일 수 있음 → `curl.exe` 또는 JSON body 주의.
- **Discord:** `job_runs`가 `success`여도 웹훅 단계 실패 시 DB와 불일치 가능(코드상 커밋 후 웹훅). 실제 전송은 채널 확인.
- **GitHub Actions Node 20 deprecation 경고:** 러너/액션 업그레이드 이슈; 당장 실패 원인은 아님.

---

## 9. 원격 저장소

- GitHub: `https://github.com/hip1hip/trending-news` (공개 저장소로 진행됨)

---

## 10. 이 문서 갱신 시점

에이전트는 다음을 바꾼 뒤 **이 파일을 짧게 갱신**하는 것이 좋다.

- 스케줄 시각/타임존, 워크플로 트리거·레이블, 배포 경로, 필수 환경 변수, 아키텍처 결정

---

## 11. 사람용 문서

- `README.md` — 설치, EC2, CI/CD 사용자 안내
- `SECURITY.md` — 보안 체크리스트
