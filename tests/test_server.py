"""MCP 서버 테스트."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from email_mcp.server import create_server, create_email_client


@pytest.fixture(autouse=True)
def _suppress_dotenv():
    """테스트 중 .env 파일 로드를 차단한다."""
    with patch("email_mcp.config.load_dotenv"):
        yield


@pytest.fixture()
def _env(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://api.test.local:20443")
    monkeypatch.setenv("API_BEARER_TOKEN", "test-token")
    monkeypatch.setenv("API_SSL_VERIFY", "false")


@pytest.fixture()
def mcp(_env):
    return create_server()


@pytest.fixture()
def client(_env):
    return create_email_client()


class TestCreateServer:
    """서버 생성 테스트."""

    def test_server_name(self, mcp):
        """서버 이름이 올바르게 설정된다."""
        assert mcp.name == "email-mcp"

    def test_server_has_tools(self, mcp):
        """이메일 발송 도구가 등록되어 있다."""
        # FastMCP 내부 도구 목록 확인
        tool_names = list(mcp._tool_manager._tools.keys())
        assert "send_html_email" in tool_names
        assert "send_markdown_email" in tool_names


class TestSendHtmlEmailTool:
    """send_html_email 도구 테스트."""

    @respx.mock
    async def test_send_html_email_returns_success(self, mcp, _env):
        """HTML 이메일 발송 도구가 성공 메시지를 반환한다."""
        respx.post("https://api.test.local:20443/api/v1/email/send").mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        tool_fn = mcp._tool_manager._tools["send_html_email"].fn
        result = await tool_fn(
            receivers="user@example.com",
            subject="제목",
            content="<p>본문</p>",
            sender_name="발신자",
        )

        assert "Email sent successfully" in result

    @respx.mock
    async def test_send_html_email_without_sender_name(self, mcp, _env):
        """sender_name 없이 HTML 이메일 발송이 가능하다."""
        respx.post("https://api.test.local:20443/api/v1/email/send").mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        tool_fn = mcp._tool_manager._tools["send_html_email"].fn
        result = await tool_fn(
            receivers="user@example.com",
            subject="제목",
            content="<p>본문</p>",
        )

        assert "Email sent successfully" in result

    @respx.mock
    async def test_send_html_email_api_error(self, mcp, _env):
        """API 에러 시 에러 메시지를 반환한다."""
        respx.post("https://api.test.local:20443/api/v1/email/send").mock(
            return_value=httpx.Response(500, json={"message": "메일 발송 오류"})
        )

        tool_fn = mcp._tool_manager._tools["send_html_email"].fn
        result = await tool_fn(
            receivers="user@example.com",
            subject="제목",
            content="<p>본문</p>",
        )

        assert "오류" in result or "error" in result.lower() or "500" in result


class TestSendMarkdownEmailTool:
    """send_markdown_email 도구 테스트."""

    @respx.mock
    async def test_send_markdown_email_returns_success(self, mcp, _env):
        """Markdown 이메일 발송 도구가 성공 메시지를 반환한다."""
        respx.post("https://api.test.local:20443/api/v1/email/send_markdown").mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        tool_fn = mcp._tool_manager._tools["send_markdown_email"].fn
        result = await tool_fn(
            receivers="user@example.com",
            subject="제목",
            content="# 제목\n본문",
            sender_name="발신자",
        )

        assert "Email sent successfully" in result

    @respx.mock
    async def test_send_markdown_email_api_error(self, mcp, _env):
        """Markdown 발송 API 에러 시 에러 메시지를 반환한다."""
        respx.post("https://api.test.local:20443/api/v1/email/send_markdown").mock(
            return_value=httpx.Response(400, json={"message": "필수 파라미터 누락"})
        )

        tool_fn = mcp._tool_manager._tools["send_markdown_email"].fn
        result = await tool_fn(
            receivers="",
            subject="",
            content="",
        )

        assert "오류" in result or "error" in result.lower() or "400" in result
