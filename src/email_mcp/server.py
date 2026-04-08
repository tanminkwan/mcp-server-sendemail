"""MCP 서버 — stdio 전송 방식으로 이메일 발송 도구를 제공한다."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from email_mcp.client import EmailClient
from email_mcp.config import Settings

SERVER_NAME = "email-mcp"
SERVER_INSTRUCTIONS = "EmailApi를 통해 HTML 및 Markdown 이메일을 발송하는 MCP 서버입니다."


def create_email_client() -> EmailClient:
    """Settings 를 로드하여 EmailClient 를 생성한다."""
    return EmailClient(Settings())


def create_server() -> FastMCP:
    """FastMCP 서버를 생성하고 이메일 도구를 등록한다."""
    mcp = FastMCP(name=SERVER_NAME, instructions=SERVER_INSTRUCTIONS)
    email_client = create_email_client()

    @mcp.tool()
    async def send_html_email(
        receivers: str,
        subject: str,
        content: str,
        sender_name: str | None = None,
    ) -> str:
        """HTML 이메일을 발송합니다. content에 HTML 태그가 포함된 경우 이 도구를 사용하세요. 일반 텍스트(plain text)도 이 도구로 발송할 수 있습니다.

        Args:
            receivers: 수신인 이메일 주소 (여러 명일 경우 콤마로 구분)
            subject: 메일 제목
            content: 메일 본문 (HTML 태그 또는 일반 텍스트)
            sender_name: 발신인 표시 이름 (선택)
        """
        try:
            result = await email_client.send_html(
                receivers=receivers,
                subject=subject,
                content=content,
                sender_name=sender_name,
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return f"이메일 발송 오류: {exc}"

    @mcp.tool()
    async def send_markdown_email(
        receivers: str,
        subject: str,
        content: str,
        sender_name: str | None = None,
    ) -> str:
        """Markdown 이메일을 발송합니다. content에 Markdown 문법(#, **, ```, 표, Mermaid 등)이 포함된 경우 이 도구를 사용하세요. 서버가 Markdown을 HTML로 자동 변환하여 발송합니다.

        Args:
            receivers: 수신인 이메일 주소 (여러 명일 경우 콤마로 구분)
            subject: 메일 제목
            content: 메일 본문 (Markdown 형식 — 헤더, 목록, 표, 코드블록, Mermaid 다이어그램 지원)
            sender_name: 발신인 표시 이름 (선택)
        """
        try:
            result = await email_client.send_markdown(
                receivers=receivers,
                subject=subject,
                content=content,
                sender_name=sender_name,
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return f"이메일 발송 오류: {exc}"

    return mcp


def main() -> None:
    """MCP 서버를 stdio 전송 방식으로 실행한다."""
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
