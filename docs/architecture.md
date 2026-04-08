# 아키텍처 정의

## 개요

Email MCP Server는 **stdio 전송 방식**의 MCP(Model Context Protocol) 서버로,
리발소 EmailApi를 통해 HTML 및 Markdown 이메일을 발송한다.

## 모듈 구조

```
src/email_mcp/
├── __init__.py      # 패키지 docstring
├── config.py        # 환경변수 기반 설정 관리 (Settings)
├── client.py        # EmailApi HTTP 클라이언트 (EmailClient)
└── server.py        # MCP 서버 생성 및 도구 등록, 엔트리포인트 (main)
```

## 모듈 설명

### config.py — 설정 관리
- `Settings` 클래스: `.env` 파일에서 환경변수를 로드
- 필수 환경변수: `API_BASE_URL`, `API_BEARER_TOKEN`
- 선택 환경변수: `API_SSL_VERIFY` (기본값 `false`)
- API 엔드포인트 경로는 상수로 관리

### client.py — EmailApi 클라이언트
- `EmailClient` 클래스: `Settings`를 주입받아 httpx로 API 통신
- `send_html()`: HTML 이메일 발송 (`POST /api/v1/email/send`)
- `send_markdown()`: Markdown 이메일 발송 (`POST /api/v1/email/send_markdown`)
- 인증: Bearer Token (JWT)

### server.py — MCP 서버
- `create_server()`: FastMCP 인스턴스 생성 및 도구 등록
- `create_email_client()`: Settings → EmailClient 팩토리
- `main()`: stdio 전송 방식으로 서버 실행

## MCP 도구

| 도구명 | 설명 | 파라미터 |
|--------|------|----------|
| `send_html_email` | HTML 이메일 발송 | `receivers`, `subject`, `content`, `sender_name`(선택) |
| `send_markdown_email` | Markdown 이메일 발송 | `receivers`, `subject`, `content`, `sender_name`(선택) |

## 의존성 흐름

```
server.py → client.py → config.py
   (MCP)      (HTTP)     (ENV)
```

- `server.py`는 `client.py`에 의존 (이메일 발송 위임)
- `client.py`는 `config.py`에 의존 (설정값 주입)
- 의존성 역전: `EmailClient`는 `Settings` 인터페이스를 통해 설정을 받음
