# Extract Error Log MCP 설계서 (extract_error_log_mcp)

## 1. 개요
기존 `email_mcp` 프로젝트와 동일한 스타일(아키텍처, 의존성, 환경설정 공유)로 구성된 독립적인 MCP 서버입니다. 
AI Agent가 에러 로그를 추출하고, 추출된 마크다운 결과를 조회할 수 있도록 두 가지 핵심 도구를 제공합니다.

## 2. API 연동 확인
로컬 테스트 스크립트를 통해 API 엔드포인트 접근 및 응답을 확인했습니다.
- **로그 추출 요청 (`POST /api/v1/command_master/extract_log`)**: 정상 도달 확인 (Payload 요구 검증됨).
- **마크다운 목록 조회 (`GET /api/v1/knowledge/mdcontent/list`)**: 정상 응답 확인 (HTTP 200 OK). `search_tags` 파라미터를 통해 `command_id`로 문서를 검색할 수 있습니다.
- **마크다운 상세 조회 (`GET /api/v1/knowledge/mdcontent/{content_id}`)**: 목록에서 획득한 `content_id`를 사용하여 상세 조회가 가능합니다.

## 3. 기능 및 도구 (Tools) 설계
해당 MCP 서버는 AI Agent에게 다음 두 가지 도구를 제공합니다.

### 3.1. `request_extract_log`
- **목적**: 로그 추출 명령을 API 서버에 요청합니다.
- **입력**: 
  - `date`: 로그 추출 대상 일자 (포맷: `yyyymmdd`)
  - `host_id`: 대상 호스트 ID
  - `time_from`: 시작 시간 (포맷: `hhmiss`)
  - `time_to`: 종료 시간 (포맷: `hhmiss`)
  - `was_instance_id`: WAS 인스턴스 ID
- **조건 체크 (유효성 검사)**:
  - `date`는 8자리 숫자(`yyyymmdd`), `time_from`과 `time_to`는 6자리 숫자(`hhmiss`) 포맷이어야 합니다.
  - `time_from < time_to` 조건을 만족해야 합니다.
  - `was_instance_id`는 문자열 내에 반드시 `_MS`를 포함해야 합니다.
- **동작**: 
  1. 입력받은 5개의 파라미터를 JSON 페이로드로 구성하여 `/api/v1/command_master/extract_log` API를 호출합니다.
  2. 반환된 결과(주로 `command_id`)를 반환합니다.
- **제약사항**: 호출 완료 후 즉시 로그 추출 마크다운이 생성되지 않을 수 있으므로, AI Agent는 이 도구를 호출하고 받은 `command_id`를 간직한 채 **약 1분간 대기(Wait)** 해야 합니다.

### 3.2. `get_extracted_log`
- **목적**: 추출된 에러 로그의 마크다운 결과를 가져옵니다.
- **입력**: `command_id`
- **동작**: 
  1. **(연속 실행 1)** `/api/v1/knowledge/mdcontent/list?search_tags={command_id}&max=1` 호출을 통해 목록을 검색하고 `content_id`를 획득합니다.
  2. **(연속 실행 2)** 획득한 `content_id`를 이용하여 `/api/v1/knowledge/mdcontent/{content_id}` API를 호출하여 마크다운 본문을 조회합니다.
  3. 상세 문서의 전체 결과를 반환합니다.

## 4. 환경 변수 (`.env` 공유)
이 패키지는 기존 `email_mcp`가 사용하는 `.env` 파일과 동일한 값을 사용합니다.
- `API_BASE_URL`: API 서버의 기본 URL (예: `https://app.mwm.local:20443`)
- `API_BEARER_TOKEN`: 인증에 사용되는 JWT Bearer 토큰
- `API_SSL_VERIFY`: SSL 인증서 검증 여부 (`False` 설정)

## 5. 프로젝트 구조 변경 사항
`src/` 하위에 독립적인 `extract_error_log_mcp` 패키지를 추가하고 진입점을 분리했습니다.
```text
mcp-server/
├── pyproject.toml (entrypoint 추가: extract-error-log-mcp)
├── src/
│   ├── email_mcp/
│   │   ├── ... (기존)
│   └── extract_error_log_mcp/
│       ├── __init__.py
│       ├── config.py (설정 관리)
│       ├── client.py (HTTP 통신)
│       └── server.py (MCP Tool 등록 및 실행)
└── docs/
    └── extract_error_log_mcp_design.md (본 설계서)
```

## 6. 실행 방법
프로젝트 루트에서 패키지 재설치 후, 다음 명령어로 독립된 서버를 실행할 수 있습니다.
```bash
# 가상 환경에서 재설치 (entrypoint 반영)
pip install -e .

# 서버 실행 (stdio 모드)
extract-error-log-mcp
```
