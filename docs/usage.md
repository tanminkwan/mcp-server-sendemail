# 사용 가이드 (요약)

> 오프라인 환경 설치를 포함한 상세 가이드는 [installation-guide.md](installation-guide.md)를 참조한다.

## 빠른 시작 (인터넷 가능한 환경)

```bash
# 1. 가상환경 생성 및 활성화
python3.14 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. 의존성 설치
pip install -e ".[dev]"

# 3. 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력

# 4. 실행 (stdio)
email-mcp
```

## 환경변수

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `API_BASE_URL` | EmailApi 서버 주소 | O | — |
| `API_BEARER_TOKEN` | JWT 인증 토큰 | O | — |
| `API_SSL_VERIFY` | SSL 인증서 검증 여부 | X | `false` |
| `API_TIMEOUT` | HTTP 요청 타임아웃(초) | X | `60` |
| `EMAIL_RECIPIENT_MAPPING` | 수신자 이름-이메일 매핑 (JSON 또는 `이름:이메일` 콤마 구분) | X | — |

> **수신자 이름 매핑**: `EMAIL_RECIPIENT_MAPPING` 환경변수에 이름과 이메일을 등록해두면, `receivers`에 이메일 대신 이름을 입력해도 서버가 이메일 주소로 자동 변환합니다. (예: `EMAIL_RECIPIENT_MAPPING=홍길동:hong@example.com`)

## MCP 도구

| 도구명 | 설명 | 파라미터 |
|--------|------|----------|
| `send_html_email` | HTML 이메일 발송 | `receivers` (이름 또는 이메일), `subject`, `content`, `sender_name`(선택) |
| `send_markdown_email` | Markdown 이메일 발송 | `receivers` (이름 또는 이메일), `subject`, `content`, `sender_name`(선택) |


## 테스트

```bash
pytest
```

커버리지 리포트 포함 (최소 85% 이상 유지).
