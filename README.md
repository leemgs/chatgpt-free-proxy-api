# ChatGPT Free Reverse Proxy (Ubuntu X86_64 + Cloudflare Bypass)

![Project Overview](./img/overview.png)

무료 ChatGPT 웹을 Playwright로 자동화하여 OpenAI 호환 API로 제공하는 Proxy 서버입니다. (최신 `chatgpt.com` 도메인 및 UI 업데이트 대응 완료)


## 🌟 주요 기능
- **자동 로그인**: Email 및 Password를 통한 자동 로그인 지원 (Auth0 등 다양한 로그인 폼 대응)
- **최신 UI 완벽 호환**: 새로운 ChatGPT DOM 구조(#prompt-textarea 등) 완벽 대응
- **세션 자동 유지 (Keep-Alive)**: 30분 단위 백그라운드 새로고침 기능으로 Cloudflare 세션 만료 및 봇 차단 우회
- **자동 복구 (Auto-Recovery)**: 페이지 DOM을 찾을 수 없거나 세션이 해제된 경우 자동으로 페이지 새로고침 및 재로그인 시도
- **Streaming 응답 지원**: OpenAI API와 동일하게 `stream=true` 지원
- **시스템 호환성**: Ubuntu 24.04, 26.04 (X86_64) 환경 완벽 지원
- **OpenAI 호환 API**: `/v1/chat/completions` 완벽 호환 및 Swagger UI 제공 (`/docs`)

## 🚀 Getting Started (시작하기)

### 1. 설치 및 환경 설정

먼저 프로젝트 저장소로 이동한 후 환경 변수를 설정합니다.

```bash
# 환경 변수 템플릿 복사
cp .env.example .env
```

`.env` 파일을 열고 본인의 ChatGPT 이메일과 비밀번호를 입력하세요.
```env
EMAIL=your-email@example.com
PASSWORD=your-password
PORT=8005
HEADLESS=true
```

### 2. 실행

Docker Compose를 사용하여 간편하게 서버를 빌드하고 실행합니다.

```bash
# 백그라운드 모드로 Docker 빌드 및 컨테이너 실행
docker-compose up --build -d
```
> **참고**: Playwright Chromium과 내부 종속성을 함께 설치하므로 최초 빌드 시 약간의 시간이 소요될 수 있습니다.

### 3. API 추론 테스트 (cURL)

서버가 정상적으로 구동되었다면, `curl`을 사용하여 OpenAI API 표준 규격으로 메시지 전송 테스트를 진행해 볼 수 있습니다. 
*(초기 기동 시 Playwright 브라우저 렌더링 및 자동 로그인 과정으로 인해 첫 요청은 20~30초 가량 소요될 수 있습니다.)*

![API Test Results](./img/api-test.png)

**일반 요청 테스트:**
```bash
curl -X POST http://localhost:8005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "안녕하세요, 지금 당신이 동작 중인지 확인하는 테스트 메시지입니다!"}],
    "stream": false
  }'
```

**스트리밍(Streaming) 요청 테스트:**
```bash
curl -X POST http://localhost:8005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "1부터 10까지 천천히 세어주세요."}],
    "stream": true
  }'
```
