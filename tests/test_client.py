"""EmailApi 클라이언트 테스트."""

from unittest.mock import patch

import httpx
import pytest
import respx

from email_mcp.client import EmailClient
from email_mcp.config import Settings


@pytest.fixture(autouse=True)
def _suppress_dotenv():
    """테스트 중 .env 파일 로드를 차단한다."""
    with patch("email_mcp.config.load_dotenv"):
        yield


@pytest.fixture()
def settings(monkeypatch) -> Settings:
    monkeypatch.setenv("API_BASE_URL", "https://api.test.local:20443")
    monkeypatch.setenv("API_BEARER_TOKEN", "test-token")
    monkeypatch.setenv("API_SSL_VERIFY", "false")
    return Settings()


@pytest.fixture()
def client(settings) -> EmailClient:
    return EmailClient(settings)


class TestEmailClient:
    """EmailClient 테스트."""

    def test_creates_httpx_client_with_settings(self, client, settings):
        """httpx 클라이언트가 설정값으로 올바르게 생성된다."""
        assert client._settings is settings

    @respx.mock
    async def test_send_html_email_success(self, client, settings):
        """HTML 이메일 발송이 성공하면 응답 메시지를 반환한다."""
        route = respx.post(settings.email_send_url).mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        result = await client.send_html(
            receivers="user@example.com",
            subject="테스트 제목",
            content="<p>HTML 본문</p>",
            sender_name="테스트 발신자",
        )

        assert result == {"message": "Email sent successfully"}
        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-token"

    @respx.mock
    async def test_send_markdown_email_success(self, client, settings):
        """Markdown 이메일 발송이 성공하면 응답 메시지를 반환한다."""
        route = respx.post(settings.email_send_markdown_url).mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        result = await client.send_markdown(
            receivers="user@example.com",
            subject="MD 테스트",
            content="# 제목\n본문",
            sender_name="테스트",
        )

        assert result == {"message": "Email sent successfully"}
        assert route.called

    @respx.mock
    async def test_send_html_without_sender_name(self, client, settings):
        """sender_name 생략 시에도 정상 발송된다."""
        route = respx.post(settings.email_send_url).mock(
            return_value=httpx.Response(200, json={"message": "Email sent successfully"})
        )

        result = await client.send_html(
            receivers="user@example.com",
            subject="제목",
            content="<p>본문</p>",
        )

        assert result == {"message": "Email sent successfully"}
        body = route.calls.last.request.read()
        import json
        payload = json.loads(body)
        assert "sender_name" not in payload

    @respx.mock
    async def test_send_html_400_raises(self, client, settings):
        """400 응답 시 에러를 발생시킨다."""
        respx.post(settings.email_send_url).mock(
            return_value=httpx.Response(400, json={"message": "필수 파라미터 누락"})
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.send_html(
                receivers="",
                subject="",
                content="",
            )

    @respx.mock
    async def test_send_html_500_raises(self, client, settings):
        """500 응답 시 에러를 발생시킨다."""
        respx.post(settings.email_send_url).mock(
            return_value=httpx.Response(500, json={"message": "메일 발송 오류"})
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.send_html(
                receivers="user@example.com",
                subject="제목",
                content="본문",
            )

    @respx.mock
    async def test_send_markdown_400_raises(self, client, settings):
        """Markdown 발송 400 응답 시 에러를 발생시킨다."""
        respx.post(settings.email_send_markdown_url).mock(
            return_value=httpx.Response(400, json={"message": "필수 파라미터 누락"})
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.send_markdown(
                receivers="",
                subject="",
                content="",
            )

    @respx.mock
    async def test_request_body_has_correct_fields(self, client, settings):
        """요청 body에 올바른 필드가 포함된다."""
        import json

        route = respx.post(settings.email_send_url).mock(
            return_value=httpx.Response(200, json={"message": "ok"})
        )

        await client.send_html(
            receivers="a@b.com, c@d.com",
            subject="제목",
            content="<b>내용</b>",
            sender_name="시스템",
        )

        payload = json.loads(route.calls.last.request.read())
        assert payload == {
            "receivers": "a@b.com, c@d.com",
            "subject": "제목",
            "content": "<b>내용</b>",
            "sender_name": "시스템",
        }
