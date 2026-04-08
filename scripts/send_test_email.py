"""Markdown 이메일 발송 테스트 스크립트."""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트의 .env 로드
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from email_mcp.client import EmailClient
from email_mcp.config import Settings

RECEIVER = "tiffanie.kim@samsung.com"
SUBJECT = "[테스트] Email MCP Server 발송 테스트"
SENDER_NAME = "Email MCP Server"

CONTENT = """\
# Email MCP Server 발송 테스트

안녕하세요, 이 메일은 **Email MCP Server**에서 자동 발송된 테스트 메일입니다.

## 테스트 항목

| 항목 | 상태 |
|------|------|
| Markdown → HTML 변환 | 확인 중 |
| 수신자 전달 | 확인 중 |
| Bearer Token 인증 | 확인 중 |

## 코드 블록 예시

```python
from email_mcp.client import EmailClient

client = EmailClient(settings)
await client.send_markdown(receivers="user@example.com", subject="제목", content="# 본문")
```

## Mermaid 다이어그램

```mermaid
graph LR
    A[MCP Client] --> B[MCP Server]
    B --> C[EmailApi]
    C --> D[SMTP]
    D --> E[수신자]
```

---

> 본 메일은 테스트 목적으로 발송되었습니다.
"""


async def main() -> None:
    settings = Settings()
    client = EmailClient(settings)

    print(f"수신자: {RECEIVER}")
    print(f"제목: {SUBJECT}")
    print(f"API: {settings.email_send_markdown_url}")
    print("발송 중...")

    result = await client.send_markdown(
        receivers=RECEIVER,
        subject=SUBJECT,
        content=CONTENT,
        sender_name=SENDER_NAME,
    )

    print(f"결과: {result}")


if __name__ == "__main__":
    asyncio.run(main())
