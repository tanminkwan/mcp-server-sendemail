"""EmailApi HTTP 클라이언트 모듈."""

from __future__ import annotations

from typing import Any

import httpx

from email_mcp.config import Settings


class EmailClient:
    """EmailApi와 통신하는 HTTP 클라이언트.

    Settings 를 주입받아 인증·SSL 설정을 처리한다.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # -- public API -----------------------------------------------------------

    async def send_html(
        self,
        receivers: str,
        subject: str,
        content: str,
        sender_name: str | None = None,
    ) -> dict[str, Any]:
        """HTML 이메일을 발송한다."""
        payload = self._build_payload(receivers, subject, content, sender_name)
        return await self._post(self._settings.email_send_url, payload)

    async def send_markdown(
        self,
        receivers: str,
        subject: str,
        content: str,
        sender_name: str | None = None,
    ) -> dict[str, Any]:
        """Markdown 이메일을 발송한다."""
        payload = self._build_payload(receivers, subject, content, sender_name)
        return await self._post(self._settings.email_send_markdown_url, payload)

    # -- helpers --------------------------------------------------------------

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """API에 POST 요청을 보내고 JSON 응답을 반환한다."""
        async with httpx.AsyncClient(
            verify=self._settings.api_ssl_verify,
            timeout=self._settings.api_timeout,
        ) as http:
            response = await http.post(
                url,
                json=payload,
                headers=self._settings.auth_header,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _build_payload(
        receivers: str,
        subject: str,
        content: str,
        sender_name: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "receivers": receivers,
            "subject": subject,
            "content": content,
        }
        if sender_name is not None:
            payload["sender_name"] = sender_name
        return payload
