"""llm-agent RAG API HTTP 클라이언트 모듈."""

from __future__ import annotations

from typing import Any

import httpx

from error_rag_mcp.config import Settings


class RagClient:
    """llm-agent RAG API(검색/등록)와 통신하는 HTTP 클라이언트.

    Settings 를 주입받아 인증·SSL 설정을 처리한다.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # -- public API -----------------------------------------------------------

    async def search(
        self, query: str, search_method: str, limit: int
    ) -> list[dict[str, Any]]:
        """지정된 검색 방식(vector/text_matching)으로 RAG 검색을 수행한다."""
        payload = {
            "collection_id": self._settings.collection_name,
            "domain_id": self._settings.domain_id,
            "query": query,
            "search_method": search_method,
            "limit": limit,
        }
        return await self._post(self._settings.search_url, payload)

    async def register(self, content: str, extended_content: str) -> dict[str, Any]:
        """지식 데이터를 신규 등록한다."""
        payload = {
            "collection_name": self._settings.collection_name,
            "domain_id": self._settings.domain_id,
            "content": content,
            "extended_content": extended_content,
            "source": self._settings.source,
        }
        return await self._post(self._settings.knowledge_url, payload)

    # -- helpers --------------------------------------------------------------

    async def _post(self, url: str, payload: dict[str, Any]) -> Any:
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
