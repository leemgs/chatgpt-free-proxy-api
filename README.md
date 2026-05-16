# ChatGPT Free Reverse Proxy (Raspberry Pi + Cloudflare Bypass)

무료 ChatGPT 웹을 Playwright로 자동화하여 OpenAI 호환 API로 제공하는 Proxy 서버입니다.

### 주요 기능
- 자동 로그인 (Email + Password)
- Streaming 응답 지원 (`stream=true`)
- 강력한 Cloudflare 우회 (Stealth 기법 적용)
- Raspberry Pi 최적화 (ARM64, 메모리 절약)
- OpenAI `/v1/chat/completions` 호환
- Swagger UI 제공 (`/docs`)

### 빠른 시작

```bash
cp .env.example .env
# .env 파일에 EMAIL과 PASSWORD 입력

docker compose up --build -d
