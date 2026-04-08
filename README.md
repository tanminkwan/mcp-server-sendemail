# Email MCP Server

**EmailApi를 통해 HTML 및 Markdown 이메일을 발송하는 MCP(Model Context Protocol) 서버**

stdio 전송 방식으로 동작하며, VS Code의 Claude 확장 등 MCP 클라이언트에서 이메일 발송 도구로 사용할 수 있습니다.

## 주요 기능

| MCP 도구 | 설명 |
|----------|------|
| `send_html_email` | HTML 또는 일반 텍스트 이메일 발송 |
| `send_markdown_email` | Markdown → HTML 자동 변환 후 발송 (Mermaid, 코드블록, 표 지원) |

## 빠른 시작

```bash
# 가상환경 생성 및 활성화
python3.14 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -e .

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력

# 실행 (stdio)
email-mcp
```

## 환경변수

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `API_BASE_URL` | EmailApi 서버 주소 | O | — |
| `API_BEARER_TOKEN` | JWT 인증 토큰 | O | — |
| `API_SSL_VERIFY` | SSL 인증서 검증 여부 | X | `false` |
| `API_TIMEOUT` | HTTP 요청 타임아웃(초) | X | `60` |

## VS Code 설정

프로젝트 루트에 `.vscode/mcp.json` 파일을 생성합니다.

### 방법 A: .env 파일 사용

프로젝트 루트에 `.env` 파일이 있으면 MCP 서버가 자동으로 로드합니다.

**Linux:**
```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/email-mcp"
    }
  }
}
```

**Windows:**
```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "C:\\projects\\email-mcp-server\\.venv\\Scripts\\email-mcp.exe"
    }
  }
}
```

### 방법 B: mcp.json에서 환경변수 직접 전달

`.env` 파일 없이 `mcp.json`의 `env` 필드로 직접 설정할 수 있습니다.

**Linux:**
```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/email-mcp",
      "env": {
        "API_BASE_URL": "https://app.mwm.local:20443",
        "API_BEARER_TOKEN": "your_jwt_token_here",
        "API_SSL_VERIFY": "false"
      }
    }
  }
}
```

**Windows:**
```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "C:\\projects\\email-mcp-server\\.venv\\Scripts\\email-mcp.exe",
      "env": {
        "API_BASE_URL": "https://app.mwm.local:20443",
        "API_BEARER_TOKEN": "your_jwt_token_here",
        "API_SSL_VERIFY": "false"
      }
    }
  }
}
```

> **참고**: `env`에 설정한 값이 `.env` 파일보다 우선합니다. 두 방법을 혼용할 수도 있습니다.

## MCP 도구 상세

### send_html_email

HTML 태그가 포함된 이메일 또는 일반 텍스트 이메일을 발송합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `receivers` | string | O | 수신인 이메일 주소 (콤마로 다수 지정) |
| `subject` | string | O | 메일 제목 |
| `content` | string | O | 메일 본문 (HTML 또는 일반 텍스트) |
| `sender_name` | string | X | 발신인 표시 이름 |

### send_markdown_email

Markdown 본문을 HTML로 자동 변환하여 발송합니다. 헤더, 목록, 표, 코드블록, Mermaid 다이어그램을 지원합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `receivers` | string | O | 수신인 이메일 주소 (콤마로 다수 지정) |
| `subject` | string | O | 메일 제목 |
| `content` | string | O | 메일 본문 (Markdown 형식) |
| `sender_name` | string | X | 발신인 표시 이름 |

## 프로젝트 구조

```
src/email_mcp/
├── config.py     ← 환경변수 기반 설정 관리
├── client.py     ← EmailApi HTTP 클라이언트 (httpx)
└── server.py     ← MCP 서버 생성, 도구 등록, stdio 엔트리포인트
```

## 테스트

```bash
pip install -e ".[dev]"
pytest
```

커버리지 85% 이상을 유지합니다.

## 오프라인 설치

인터넷이 차단된 환경에서의 설치 방법은 [설치 가이드](docs/installation-guide.md)를 참조하세요.

## 기술 스택

- Python 3.14
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) (FastMCP, stdio)
- [httpx](https://www.python-httpx.org/) (비동기 HTTP 클라이언트)
- [python-dotenv](https://github.com/theskumar/python-dotenv) (환경변수 관리)
