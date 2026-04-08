# 보안 안내 (공개 저장소)

이 문서는 저장소를 **공개(Public)** 로 두기 전에 확인할 항목을 정리합니다.

## 저장소에 포함되지 않아야 하는 것

- `.env` (gitignore 처리됨): `DISCORD_WEBHOOK_URL`, `DATABASE_URL`, DB 비밀번호
- SSH·TLS 개인키 (`*.pem` 등, gitignore 처리됨)
- Discord 웹훅 URL(토큰 포함) — 유출 시 누구나 해당 채널에 메시지를 보낼 수 있음

## 애플리케이션·배포 관점

| 항목 | 현재 MVP | 공개 인스턴스 배포 시 권장 |
|------|-----------|----------------------------|
| Postgres | compose에서 **호스트 포트 미개방**(내부 네트워크만) | 동일 유지. 클라우드에서 DB 포트를 인터넷에 열지 말 것 |
| DB 비밀번호 | `.env`의 `POSTGRES_PASSWORD` 사용 | 추측 불가능한 값으로 설정, 기본값/예시 문자열 그대로 운영 금지 |
| API 인증 | 없음 (`/jobs/run-digest` 등 누구나 호출 가능) | 리버스 프록시(Basic Auth, mTLS), VPN, 또는 내부망만 허용 |
| HTTPS | nginx 예시는 HTTP(80)만 | Let’s Encrypt 등으로 443 TLS 종료 |
| Rate limit | 없음 | nginx/cloudflare 등에서 제한 검토 |

## 코드베이스 점검 요약

- 트래킹된 파일에 하드코딩된 Discord 웹훅·API 키·AWS 키 패턴은 없어야 합니다.
- `docker-compose.yml`에는 DB 비밀번호를 직접 적지 않고, 환경 변수만 참조합니다.

문제 발견 시 이슈로 알려 주시거나 PR로 수정해 주세요.
