"""RagClient 테스트."""

import json
from unittest.mock import patch

import httpx
import pytest
import respx

from error_rag_mcp.client import RagClient
from error_rag_mcp.config import Settings


@pytest.fixture(autouse=True)
def _suppress_dotenv():
    """테스트 중 .env 파일 로드를 차단한다."""
    with patch("error_rag_mcp.config.load_dotenv"):
        yield


@pytest.fixture()
def settings(monkeypatch) -> Settings:
    monkeypatch.setenv("RAG_API_BASE_URL", "http://localhost:28000")
    monkeypatch.setenv("RAG_COLLECTION_NAME", "error_rag_test")
    monkeypatch.setenv("RAG_DOMAIN_ID", "6")
    monkeypatch.delenv("RAG_API_BEARER_TOKEN", raising=False)
    return Settings()


@pytest.fixture()
def client(settings) -> RagClient:
    return RagClient(settings)


class TestRagClientSearch:
    """RagClient.search 테스트."""

    @respx.mock
    async def test_vector_search_request_payload(self, client, settings):
        """벡터 검색 요청 payload가 SearchRequest 스펙과 일치한다."""
        route = respx.post(settings.search_url).mock(
            return_value=httpx.Response(200, json=[])
        )

        await client.search(query="DB 커넥션 풀 고갈", search_method="vector", limit=3)

        payload = json.loads(route.calls.last.request.read())
        assert payload == {
            "collection_id": "error_rag_test",
            "domain_id": 6,
            "query": "DB 커넥션 풀 고갈",
            "search_method": "vector",
            "limit": 3,
        }

    @respx.mock
    async def test_text_matching_search_request_payload(self, client, settings):
        """텍스트 매칭 검색 요청 payload가 SearchRequest 스펙과 일치한다."""
        route = respx.post(settings.search_url).mock(
            return_value=httpx.Response(200, json=[])
        )

        await client.search(query="ORA-00001", search_method="text_matching", limit=2)

        payload = json.loads(route.calls.last.request.read())
        assert payload["search_method"] == "text_matching"
        assert payload["query"] == "ORA-00001"
        assert payload["limit"] == 2

    @respx.mock
    async def test_search_returns_results(self, client, settings):
        """검색 결과 목록을 그대로 반환한다."""
        expected = [
            {
                "id": "abc-123",
                "collection": "error_rag_test",
                "score": 0.9,
                "content": "요약",
                "extended_content": "보고서",
                "domain_id": 6,
                "source": "error-resolution-report",
                "created_at": "2026-09-03T00:00:00+00:00",
            }
        ]
        respx.post(settings.search_url).mock(
            return_value=httpx.Response(200, json=expected)
        )

        result = await client.search(query="요약", search_method="vector", limit=3)

        assert result == expected

    @respx.mock
    async def test_search_no_results_returns_empty_list(self, client, settings):
        """유사 사례가 없으면 빈 리스트를 반환한다."""
        respx.post(settings.search_url).mock(return_value=httpx.Response(200, json=[]))

        result = await client.search(query="없는 오류", search_method="vector", limit=3)

        assert result == []

    @respx.mock
    async def test_search_error_raises(self, client, settings):
        """검색 API가 500을 반환하면 예외를 발생시킨다."""
        respx.post(settings.search_url).mock(return_value=httpx.Response(500))

        with pytest.raises(httpx.HTTPStatusError):
            await client.search(query="q", search_method="vector", limit=3)

    @respx.mock
    async def test_search_uses_bearer_header_when_token_set(self, monkeypatch, settings):
        """RAG_API_BEARER_TOKEN이 설정되면 Authorization 헤더를 부착한다."""
        monkeypatch.setenv("RAG_API_BEARER_TOKEN", "test-token")
        authed_settings = Settings()
        authed_client = RagClient(authed_settings)
        route = respx.post(authed_settings.search_url).mock(
            return_value=httpx.Response(200, json=[])
        )

        await authed_client.search(query="q", search_method="vector", limit=3)

        assert route.calls.last.request.headers["Authorization"] == "Bearer test-token"

    @respx.mock
    async def test_search_omits_auth_header_without_token(self, client, settings):
        """토큰이 없으면 Authorization 헤더를 보내지 않는다."""
        route = respx.post(settings.search_url).mock(
            return_value=httpx.Response(200, json=[])
        )

        await client.search(query="q", search_method="vector", limit=3)

        assert "Authorization" not in route.calls.last.request.headers


class TestRagClientRegister:
    """RagClient.register 테스트."""

    @respx.mock
    async def test_register_request_payload(self, client, settings):
        """등록 요청 payload가 KnowledgeCreate 스펙과 일치한다."""
        route = respx.post(settings.knowledge_url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "point-1",
                    "status": "success",
                    "created_at": "2026-09-03T00:00:00+00:00",
                },
            )
        )

        await client.register(
            content="요약 [ORA-00001]",
            extended_content="# 오류 및 조치 보고서",
        )

        payload = json.loads(route.calls.last.request.read())
        assert payload == {
            "collection_name": "error_rag_test",
            "domain_id": 6,
            "content": "요약 [ORA-00001]",
            "extended_content": "# 오류 및 조치 보고서",
            "source": "error-resolution-report",
        }
        assert "point_id" not in payload

    @respx.mock
    async def test_register_returns_response(self, client, settings):
        """등록 성공 응답을 그대로 반환한다."""
        expected = {
            "id": "point-1",
            "status": "success",
            "created_at": "2026-09-03T00:00:00+00:00",
        }
        respx.post(settings.knowledge_url).mock(return_value=httpx.Response(200, json=expected))

        result = await client.register(content="요약", extended_content="보고서")

        assert result == expected

    @respx.mock
    async def test_register_error_raises(self, client, settings):
        """등록 API가 422를 반환하면 예외를 발생시킨다."""
        respx.post(settings.knowledge_url).mock(return_value=httpx.Response(422))

        with pytest.raises(httpx.HTTPStatusError):
            await client.register(content="", extended_content="")
