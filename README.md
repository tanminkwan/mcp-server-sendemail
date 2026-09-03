# MCP Server Collection

**Email 발송, 에러 로그 추출, 오류/조치 RAG 검색·등록 기능을 제공하는 독립적인 MCP(Model Context Protocol) 서버 모음**

각 서버는 완전히 독립된 패키지(`config`/`client`/`server` 3계층)로 구성되며, stdio 전송 방식으로 동작해
VS Code의 Claude 확장 등 MCP 클라이언트에서 도구로 사용할 수 있습니다.

## 서버 목록

| 서버 | 패키지 | 엔트리포인트 | 설명 | 상세 문서 |
|------|--------|-------------|------|-----------|
| Email MCP | `email_mcp` | `email-mcp` | EmailApi를 통해 HTML/Markdown 이메일 발송 | 본 문서 |
| Extract Error Log MCP | `extract_error_log_mcp` | `extract-error-log-mcp` | 서버 에러 로그 추출 요청 및 결과 조회 | [설계서](docs/extract_error_log_mcp_design.md) |
| Error RAG MCP | `error_rag_mcp` | `error-rag-mcp` | 오류/조치 사례를 RAG 서비스(llm-agent)에서 검색·등록 | [요구사항 정의서](docs/error_rag_mcp_requirements.md) |

## 주요 기능

| 서버 | MCP 도구 | 설명 |
|------|----------|------|
| Email MCP | `send_html_email` | HTML 또는 일반 텍스트 이메일 발송 |
| Email MCP | `send_markdown_email` | Markdown → HTML 자동 변환 후 발송 (Mermaid, 코드블록, 표 지원) |
| Extract Error Log MCP | `request_extract_log` | 서버 에러 로그 추출 요청 (command_id 반환) |
| Extract Error Log MCP | `get_extracted_log` | command_id로 추출된 로그(마크다운) 조회 |
| Error RAG MCP | `search_similar_error` | 오류 요약(벡터 검색)+키워드(텍스트 매칭)로 과거 유사 오류/조치 사례 검색 |
| Error RAG MCP | `register_error_resolution` | 오류 및 조치 결과를 표준 보고서 형식으로 RAG에 등록 |

## 빠른 시작

```bash
# 가상환경 생성 및 활성화
python3.11 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 의존성 설치 (dev 포함: pytest 등)
pip install -e ".[dev]"

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력

# 실행 (stdio) — 필요한 서버만 실행
email-mcp
extract-error-log-mcp
error-rag-mcp
```

## 환경변수

### Email MCP / Extract Error Log MCP (공유)

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `API_BASE_URL` | EmailApi/로그 추출 API 서버 주소 | O | — |
| `API_BEARER_TOKEN` | JWT 인증 토큰 | O | — |
| `API_SSL_VERIFY` | SSL 인증서 검증 여부 | X | `false` |
| `API_TIMEOUT` | HTTP 요청 타임아웃(초) | X | `60` |
| `EMAIL_RECIPIENT_MAPPING` | 수신자 이름-이메일 매핑 (JSON 또는 `이름:이메일` 콤마 구분, Email MCP 전용) | X | — |

> **수신자 이름 매핑 (`EMAIL_RECIPIENT_MAPPING`)**:
> - `EMAIL_RECIPIENT_MAPPING` 환경변수에 이름과 이메일 주소를 등록하면, 이메일 발송 시 `receivers`에 이메일 주소 대신 이름만 지정해도 서버가 자동으로 이메일 주소로 변환합니다.
> - **콤마 구분 형식**: `홍길동:hong@example.com, 김철수:kim@example.com`
> - **JSON 형식**: `{"홍길동": "hong@example.com", "김철수": "kim@example.com"}`

### Error RAG MCP (`error_rag_mcp`)

llm-agent RAG API 연동을 위한 별도 환경변수를 사용합니다 (위 변수들과 독립적).

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `RAG_API_BASE_URL` | llm-agent 서비스 기본 URL | O | — |
| `RAG_API_BEARER_TOKEN` | 인증 토큰 (현재 llm-agent는 미인증 접근 가능, 향후 대비) | X | — (헤더 생략) |
| `RAG_API_SSL_VERIFY` | SSL 인증서 검증 여부 | X | `false` |
| `RAG_API_TIMEOUT` | HTTP 요청 타임아웃(초) | X | `60` |
| `RAG_COLLECTION_NAME` | 고정 콜렉션 식별자 | O | — |
| `RAG_DOMAIN_ID` | 고정 도메인 ID (정수) | O | — |
| `RAG_VECTOR_SEARCH_LIMIT` | 벡터 검색 결과 개수 | X | `3` |
| `RAG_TEXT_MATCHING_LIMIT` | 텍스트 매칭 검색 결과 개수 | X | `2` |
| `RAG_SOURCE` | 등록 시 지식의 `source` 태그 | X | `error-resolution-report` |

## VS Code 설정

프로젝트 루트에 `.vscode/mcp.json` 파일을 생성합니다. 서버별로 `command`(엔트리포인트)만 다르고
패턴은 동일합니다.

### 방법 A: .env 파일 사용

프로젝트 루트에 `.env` 파일이 있으면 각 MCP 서버가 자동으로 로드합니다.

**Linux:**
```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/email-mcp"
    },
    "extract-error-log-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/extract-error-log-mcp"
    },
    "error-rag-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/error-rag-mcp"
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
      "command": "C:\\projects\\mcp-server\\.venv\\Scripts\\email-mcp.exe"
    },
    "extract-error-log-mcp": {
      "type": "stdio",
      "command": "C:\\projects\\mcp-server\\.venv\\Scripts\\extract-error-log-mcp.exe"
    },
    "error-rag-mcp": {
      "type": "stdio",
      "command": "C:\\projects\\mcp-server\\.venv\\Scripts\\error-rag-mcp.exe"
    }
  }
}
```

### 방법 B: mcp.json에서 환경변수 직접 전달

`.env` 파일 없이 `mcp.json`의 `env` 필드로 직접 설정할 수 있습니다. (예: `error-rag-mcp`)

```json
{
  "servers": {
    "error-rag-mcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/error-rag-mcp",
      "env": {
        "RAG_API_BASE_URL": "http://localhost:28000",
        "RAG_COLLECTION_NAME": "your_collection_name_here",
        "RAG_DOMAIN_ID": "0"
      }
    }
  }
}
```

> **참고**: `env`에 설정한 값이 `.env` 파일보다 우선합니다. 두 방법을 혼용할 수도 있습니다.

## MCP 도구 상세

### Email MCP

#### send_html_email

HTML 태그가 포함된 이메일 또는 일반 텍스트 이메일을 발송합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `receivers` | string | O | 수신자 이름 또는 이메일 주소 (등록된 이름인 경우 자동 변환, 콤마로 다수 지정) |
| `subject` | string | O | 메일 제목 |
| `content` | string | O | 메일 본문 (HTML 또는 일반 텍스트) |
| `sender_name` | string | X | 발신인 표시 이름 |

#### send_markdown_email

Markdown 본문을 HTML로 자동 변환하여 발송합니다. 헤더, 목록, 표, 코드블록, Mermaid 다이어그램을 지원합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `receivers` | string | O | 수신자 이름 또는 이메일 주소 (등록된 이름인 경우 자동 변환, 콤마로 다수 지정) |
| `subject` | string | O | 메일 제목 |
| `content` | string | O | 메일 본문 (Markdown 형식) |
| `sender_name` | string | X | 발신인 표시 이름 |

### Extract Error Log MCP

#### request_extract_log

서버의 에러 로그 추출을 요청하고 `command_id`를 반환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `date` | string | O | 로그 추출 대상 일자 (`yyyymmdd`) |
| `host_id` | string | O | 호스트 ID |
| `time_from` | string | O | 검색 시작 시간 (`hhmiss`) |
| `time_to` | string | O | 검색 종료 시간 (`hhmiss`, `time_from`보다 이후) |
| `was_instance_id` | string | O | WAS 인스턴스 ID (`_MS` 포함 필수) |

#### get_extracted_log

`command_id`로 추출된 로그(마크다운 문서)를 조회합니다. `request_extract_log` 호출 후 약 1분 대기 뒤 호출해야 합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `command_id` | string | O | `request_extract_log` 호출 결과로 받은 command_id |

### Error RAG MCP

#### search_similar_error

과거 동일/유사 오류 사례와 조치 방법을 RAG에서 검색합니다. 오류 요약(벡터 검색)과 오류 코드 등
핵심 키워드(텍스트 매칭 검색)를 병행 조회해 `id` 기준으로 중복 제거된 결과를 반환합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `error_summary` | string | O | 오류 내용 요약 (300자 이내). 벡터 검색 쿼리로 사용 |
| `error_keyword` | string | O | 오류 코드 등 핵심 식별 키워드. 텍스트 매칭 검색 쿼리로 사용 (명확한 키워드가 없으면 빈 문자열로 두면 텍스트 매칭 검색을 건너뛰고 벡터 검색만 수행) |

#### register_error_resolution

오류 및 조치 결과를 표준 보고서 형식으로 RAG에 등록합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `error_summary` | string | O | 오류 내용 요약 (300자 이내) |
| `error_keyword` | list[string] | O | 오류 코드 등 핵심 식별 키워드 목록 (최대 3개, 1개 이상) |
| `error_occurred_at` | string | O | 오류 발생일시 |
| `host_id` | string | O | 오류가 발생한 호스트 ID ('서버'/'시스템'이라고도 부름, `extract_error_log_mcp`의 `host_id`와 동일한 의미) |
| `was_instance_id` | string | O | 오류가 발생한 WAS 인스턴스 ID (보통 `_MS` 포함, `extract_error_log_mcp`의 `was_instance_id`와 동일한 의미) |
| `error_content` | string | O | 오류 내용 (상세) |
| `action_taken_at` | string | O | 조치일시 |
| `actor` | string | O | 조치자 |
| `action_content` | string | O | 조치 내용 |

> `content`(검색 대상)는 `error_summary`와 `error_keyword`를 서버가 결합해 생성하고,
> `extended_content`(보고서 본문)는 나머지 6개 필드로 표준 양식을 생성합니다(`host_id`와
> `was_instance_id`는 결합되어 "오류 발생 위치" 한 항목이 됩니다). 자세한 설계 근거는
> [요구사항 정의서](docs/error_rag_mcp_requirements.md)를 참조하세요.

## 프로젝트 구조

```
src/
├── email_mcp/
│   ├── config.py     ← 환경변수 기반 설정 관리
│   ├── client.py     ← EmailApi HTTP 클라이언트 (httpx)
│   └── server.py     ← MCP 서버 생성, 도구 등록, stdio 엔트리포인트
├── extract_error_log_mcp/
│   ├── config.py
│   ├── client.py
│   └── server.py
└── error_rag_mcp/
    ├── config.py     ← Settings, 도메인 상수(MAX_ERROR_SUMMARY_LENGTH 등)
    ├── client.py     ← llm-agent RAG API 클라이언트 (RagClient)
    └── server.py     ← search_similar_error / register_error_resolution 등록
```

## 테스트

```bash
pip install -e ".[dev]"
pytest
```

서버별로 독립된 `tests/` 하위 테스트를 가지며, 커버리지 85% 이상을 유지합니다.

## 오프라인 설치

인터넷이 차단된 환경에서의 설치 방법은 [설치 가이드](docs/installation-guide.md)를 참조하세요.

## 기술 스택

- Python 3.11+
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) (FastMCP, stdio)
- [httpx](https://www.python-httpx.org/) (비동기 HTTP 클라이언트)
- [python-dotenv](https://github.com/theskumar/python-dotenv) (환경변수 관리)
