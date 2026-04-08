# Email MCP Server — 오프라인 설치 및 사용 가이드

> 인터넷이 차단된 환경의 개인 PC(Windows)에서  
> VS Code + Claude 확장을 통해 이메일 발송 MCP 서버를 사용하는 전체 과정을 안내합니다.

---

## 목차

1. [사전 준비 (인터넷 가능한 PC에서)](#1-사전-준비-인터넷-가능한-pc에서)
2. [오프라인 PC에 파일 전송](#2-오프라인-pc에-파일-전송)
3. [Python 설치](#3-python-설치)
4. [프로젝트 설치](#4-프로젝트-설치)
5. [환경변수 설정](#5-환경변수-설정)
6. [VS Code 설정](#6-vs-code-설정)
7. [동작 확인](#7-동작-확인)
8. [MCP 도구 사용법](#8-mcp-도구-사용법)
9. [문제 해결](#9-문제-해결)

---

## 1. 사전 준비 (인터넷 가능한 PC에서)

인터넷이 되는 PC에서 아래 파일들을 미리 다운로드한다.

### 1-1. Python 설치 파일 다운로드

Windows용 Python 3.14 임베디드 패키지 또는 설치파일을 다운로드한다.

```
https://www.python.org/downloads/
```

- Windows: `python-3.14.x-amd64.exe` (64bit 설치파일)
- Linux: `Python-3.14.x.tar.xz` (소스) 또는 배포판 패키지

> **권장**: Windows 설치파일(.exe)을 사용하면 PATH 등록까지 한 번에 처리된다.

### 1-2. Python 패키지 오프라인 번들 생성

인터넷이 되는 PC에 동일한 Python 버전을 설치한 후, wheel 파일을 다운로드한다.

```bash
# 프로젝트 디렉토리에서 실행
pip download -d ./offline-packages .
pip download -d ./offline-packages ".[dev]"
```

또는 requirements.txt로 추출 후 다운로드:

```bash
pip freeze > requirements-freeze.txt
pip download -d ./offline-packages -r requirements-freeze.txt
```

`offline-packages/` 디렉토리에 `.whl` 파일들이 저장된다.

### 1-3. VS Code 확장 다운로드

VS Code 마켓플레이스에서 `.vsix` 파일을 직접 다운로드한다.

| 확장 | 다운로드 URL |
|------|-------------|
| Claude (Anthropic) | https://marketplace.visualstudio.com/items?itemName=anthropics.claude-code → **Download Extension** |

> `.vsix` 파일을 저장한다.

### 1-4. 전송할 파일 목록 정리

```
email-mcp-server/            ← 프로젝트 전체 (이 저장소)
├── src/
├── tests/
├── docs/
├── pyproject.toml
├── .env.example
├── ...
├── offline-packages/         ← pip download로 생성한 wheel 파일들
python-3.14.x-amd64.exe      ← Python 설치파일
claude-code-x.x.x.vsix       ← VS Code 확장 파일
```

---

## 2. 오프라인 PC에 파일 전송

USB 드라이브 또는 내부 파일 서버를 통해 위 파일들을 오프라인 PC로 복사한다.

**권장 경로:**

| 항목 | Windows 경로 | Linux 경로 |
|------|-------------|-----------|
| 프로젝트 | `C:\projects\email-mcp-server` | `~/projects/email-mcp-server` |
| Python 설치파일 | `C:\temp\python-3.14.x-amd64.exe` | — |
| VS Code 확장 | `C:\temp\claude-code-x.x.x.vsix` | — |

---

## 3. Python 설치

### Windows

1. `python-3.14.x-amd64.exe` 실행
2. **반드시 체크**: `☑ Add python.exe to PATH`
3. **Install Now** 클릭
4. 설치 완료 후 확인:

```cmd
python --version
```

출력 예시: `Python 3.14.3`

### Linux (Ubuntu/Debian)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.14 python3.14-venv python3.14-dev
```

> 오프라인 환경이면 `.deb` 패키지를 미리 다운로드하여 `dpkg -i` 로 설치한다.

---

## 4. 프로젝트 설치

### 4-1. 가상환경 생성

**Windows (cmd):**

```cmd
cd C:\projects\email-mcp-server
python -m venv .venv
.venv\Scripts\activate
```

**Windows (PowerShell):**

```powershell
cd C:\projects\email-mcp-server
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> PowerShell 실행 정책 에러 발생 시:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux:**

```bash
cd ~/projects/email-mcp-server
python3.14 -m venv .venv
source .venv/bin/activate
```

### 4-2. 오프라인 패키지 설치

```bash
pip install --no-index --find-links=./offline-packages -e .
```

설치 확인:

```bash
pip list | grep email-mcp
```

출력 예시: `email-mcp  0.1.0  /path/to/email-mcp-server`

### 4-3. 설치 검증

```bash
email-mcp --help
```

또는 Python으로 직접 실행 확인:

```bash
python -c "from email_mcp.server import create_server; print('OK')"
```

---

## 5. 환경변수 설정

### 5-1. .env 파일 생성

```bash
cp .env.example .env
```

### 5-2. .env 파일 편집

`.env` 파일을 텍스트 편집기로 열어 실제 값을 입력한다.

```env
API_BASE_URL=https://app.mwm.local:20443
API_BEARER_TOKEN=여기에_실제_JWT_토큰_입력
API_SSL_VERIFY=false
```

| 변수 | 설명 | 필수 | 기본값 |
|------|------|:----:|--------|
| `API_BASE_URL` | EmailApi 서버 주소 | O | — |
| `API_BEARER_TOKEN` | JWT 인증 토큰 | O | — |
| `API_SSL_VERIFY` | SSL 인증서 검증 여부 | X | `false` |
| `API_TIMEOUT` | HTTP 요청 타임아웃(초) | X | `60` |

### 5-3. JWT 토큰 발급

리발소 웹에서 장기 토큰을 발급받는다:

```
https://app.mwm.local:20443/common/generate_long_term_token
```

> 토큰은 `.env` 파일에만 저장하고, 절대 코드에 직접 삽입하지 않는다.

---

## 6. VS Code 설정

### 6-1. Claude 확장 설치 (오프라인)

VS Code에서 `Ctrl+Shift+P` → **Extensions: Install from VSIX...** 선택 → `.vsix` 파일 지정.

### 6-2. MCP 서버 설정

VS Code 설정 파일에 MCP 서버를 등록한다.

**방법 A: 프로젝트 단위 설정 (권장)**

프로젝트 루트에 `.vscode/mcp.json` 파일을 생성한다:

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

**Linux:**

```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "/home/사용자명/projects/email-mcp-server/.venv/bin/email-mcp"
    }
  }
}
```

**방법 B: 사용자 전역 설정**

VS Code `settings.json` (`Ctrl+Shift+P` → **Preferences: Open User Settings (JSON)**):

**Windows:**

```json
{
  "mcp": {
    "servers": {
      "email-mcp": {
        "type": "stdio",
        "command": "C:\\projects\\email-mcp-server\\.venv\\Scripts\\email-mcp.exe"
      }
    }
  }
}
```

**Linux:**

```json
{
  "mcp": {
    "servers": {
      "email-mcp": {
        "type": "stdio",
        "command": "/home/사용자명/projects/email-mcp-server/.venv/bin/email-mcp"
      }
    }
  }
}
```

### 6-3. 환경변수를 VS Code에서 전달하는 방법 (선택)

`.env` 파일이 프로젝트 루트에 있으면 MCP 서버가 자동으로 로드한다.
만약 다른 경로에 `.env`가 있거나 환경변수를 직접 전달하려면:

```json
{
  "servers": {
    "email-mcp": {
      "type": "stdio",
      "command": "C:\\projects\\email-mcp-server\\.venv\\Scripts\\email-mcp.exe",
      "env": {
        "API_BASE_URL": "https://app.mwm.local:20443",
        "API_BEARER_TOKEN": "your_token_here",
        "API_SSL_VERIFY": "false"
      }
    }
  }
}
```

---

## 7. 동작 확인

### 7-1. MCP 서버 연결 확인

1. VS Code에서 Claude 채팅 패널을 연다
2. MCP 서버 목록에 **email-mcp** 가 표시되는지 확인한다
3. 도구 목록에 `send_html_email`, `send_markdown_email` 이 보이면 정상

### 7-2. 테스트 이메일 발송

Claude 채팅에서 다음과 같이 입력:

```
tiffanie.kim@samsung.com 에게 테스트 이메일 보내줘.
제목은 "MCP 서버 테스트"이고, 본문은 간단한 인사말로 작성해.
```

Claude가 `send_html_email` 또는 `send_markdown_email` 도구를 호출하여 이메일을 발송한다.

### 7-3. 커맨드라인에서 직접 테스트

가상환경을 활성화한 후:

```bash
python scripts/send_test_email.py
```

---

## 8. MCP 도구 사용법

### send_html_email

HTML 형식의 이메일을 발송한다.

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|----------|------|:----:|------|------|
| `receivers` | string | O | 수신인 (콤마로 다수 지정) | `"a@b.com, c@d.com"` |
| `subject` | string | O | 메일 제목 | `"[알림] 점검 안내"` |
| `content` | string | O | 메일 본문 (HTML) | `"<h1>안내</h1><p>내용</p>"` |
| `sender_name` | string | X | 발신인 표시 이름 | `"시스템 관리자"` |

### send_markdown_email

Markdown 본문을 HTML로 변환하여 발송한다.  
Mermaid 다이어그램, 코드 블록, 표 등이 자동 변환된다.

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|----------|------|:----:|------|------|
| `receivers` | string | O | 수신인 (콤마로 다수 지정) | `"a@b.com"` |
| `subject` | string | O | 메일 제목 | `"[보고서] 점검 결과"` |
| `content` | string | O | 메일 본문 (Markdown) | `"# 제목\n- 항목1\n- 항목2"` |
| `sender_name` | string | X | 발신인 표시 이름 | `"리발소 시스템"` |

### 사용 예시 (Claude 채팅)

```
다음 내용을 Markdown 이메일로 보내줘:
- 수신자: user@example.com
- 제목: 주간 보고서
- 내용:
  # 주간 보고
  ## 완료 항목
  - 서버 점검 완료
  - 인증서 갱신
  ## 예정 항목
  - DB 백업 정책 검토
```

---

## 9. 문제 해결

### Python을 찾을 수 없음

```
'python'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
```

→ Python 설치 시 **Add to PATH** 를 체크하지 않은 경우. 환경변수에 수동 추가:

```
시스템 속성 → 환경 변수 → Path → 편집 → 추가:
C:\Users\사용자명\AppData\Local\Programs\Python\Python314\
C:\Users\사용자명\AppData\Local\Programs\Python\Python314\Scripts\
```

### pip install 시 네트워크 에러

```
WARNING: Retrying ... after connection broken
```

→ 오프라인 설치 명령어를 사용한다:

```bash
pip install --no-index --find-links=./offline-packages -e .
```

### MCP 서버가 VS Code에서 연결되지 않음

1. `.vscode/mcp.json`의 `command` 경로가 정확한지 확인
2. 가상환경 내 실행파일 존재 여부 확인:
   - Windows: `.venv\Scripts\email-mcp.exe`
   - Linux: `.venv/bin/email-mcp`
3. 터미널에서 직접 실행해 에러 확인:
   ```bash
   .venv\Scripts\email-mcp.exe
   ```

### SSL 인증서 에러

```
ssl.SSLCertVerificationError: certificate verify failed
```

→ `.env` 파일에서 `API_SSL_VERIFY=false` 로 설정되어 있는지 확인한다.

### 토큰 만료

```
{"msg": "Token has expired"}
```

→ 리발소에서 장기 토큰을 재발급받아 `.env` 파일의 `API_BEARER_TOKEN` 값을 교체한다.

### 이메일 발송 타임아웃

```
httpx.ReadTimeout
```

→ `.env` 파일에 타임아웃 값을 늘린다:

```env
API_TIMEOUT=120
```

---

## 디렉토리 구조 참고

```
email-mcp-server/
├── .env                    ← 환경변수 (git 추적 안 함)
├── .env.example            ← 환경변수 템플릿
├── .vscode/
│   └── mcp.json            ← VS Code MCP 서버 설정
├── pyproject.toml           ← 프로젝트 메타데이터·의존성
├── src/
│   └── email_mcp/
│       ├── __init__.py
│       ├── config.py        ← 설정 관리
│       ├── client.py        ← EmailApi HTTP 클라이언트
│       └── server.py        ← MCP 서버 엔트리포인트
├── tests/                   ← 테스트 코드
├── scripts/
│   └── send_test_email.py   ← 발송 테스트 스크립트
├── docs/                    ← 문서
└── offline-packages/        ← 오프라인 설치용 wheel 파일 (선택)
```
