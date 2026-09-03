# Error RAG MCP 요구사항 정의서 (error_rag_mcp)

> 상태: API 스펙 확인 완료. `llm-agent`(`localhost:28000`)의 `/openapi.json`을 직접 조회하고,
> 검증용 도메인/콜렉션(`error_rag_mcp_test`)을 만들어 `POST /api/rag/search`(vector/text_matching)와
> `POST /api/rag/knowledge`를 모두 실제 호출해 요청/응답 스펙과 검색 동작을 검증한 뒤 삭제했다
> (2026-09-03). 인증(HTTPBearer)이 OpenAPI 스펙상 정의되어 있으나, 현재 `llm-agent`는 Authorization
> 헤더 없이도 정상 응답한다(추후 API Key 적용 가능성 있으므로 클라이언트는 Bearer 헤더를 선택적으로
> 실어 보낼 수 있게 구현한다). 남은 미확정 사항은 9절 참조.

## 1. 개요

### 1.1 목적
오류/장애가 탐지되었을 때, 과거에 동일하거나 유사한 오류가 있었는지 그리고 그때 어떻게 해결했는지를
RAG(Retrieval-Augmented Generation) 서비스에서 검색하고, 조치가 끝난 뒤에는 오류 내용과 조치 결과를
다시 RAG 서비스에 등록하여 지식이 누적되도록 하는 MCP 서버이다.

기존 `email_mcp`, `extract_error_log_mcp`와 동일한 스타일(아키텍처, 의존성, 환경설정 패턴)로 구성된
독립적인 3번째 MCP 서버로 추가한다.

### 1.2 배경 시나리오 (AI Agent 관점 전체 흐름)
1. 모니터링 등을 통해 오류/장애가 탐지된다.
2. (기존 `extract_error_log_mcp`를 이용해) 에러 로그를 추출한다.
3. 추출된 로그를 바탕으로 오류 내용을 요약한다.
4. **[본 서버] `search_similar_error`**: 오류 요약을 이용해 RAG 서비스에서 과거 동일/유사 오류 사례와
   해결 방법(조치 내용)을 벡터 검색으로 조회한다.
5. AI Agent(또는 담당자)가 검색된 유사 사례를 참고하여 조치를 수행한다.
6. **[본 서버] `register_error_resolution`**: 조치 완료 후, 오류 내용과 조치 결과를 정형화된 보고서
   형태로 RAG 서비스에 등록하여 다음 유사 오류 발생 시 재활용할 수 있도록 한다.

### 1.3 연동 대상
Docker로 구동되는 `llm-agent` 서비스의 REST API 2종을 사용한다.
- 검색: `POST /api/rag/search`
- 등록: `POST /api/rag/knowledge`

## 2. 기능 요구사항 요약

| 구분 | MCP 도구명 | 대상 API | 설명 |
|------|-----------|----------|------|
| 검색 | `search_similar_error` | `POST /api/rag/search` (x2 호출) | 오류 요약으로 벡터 검색 3건 + 오류 키워드로 텍스트 매칭 검색 2건 → id 기준 distinct 병합 |
| 등록 | `register_error_resolution` | `POST /api/rag/knowledge` | 오류 및 조치 결과를 표준 보고서 형식으로 RAG에 등록 |

두 도구 외 추가 기능은 범위에 포함하지 않는다 (단일 책임 원칙 — 검색/등록 각 1개 함수).

## 3. 기능 및 도구(Tools) 설계

### 3.1 `search_similar_error`
- **목적**: 오류 요약(의미)과 핵심 키워드(정확 매칭)를 함께 사용해 과거 동일/유사 오류 사례 및
  조치 방법을 조회한다. `SearchRequest.search_method`가 `vector`/`text_matching` 두 가지를 지원하므로,
  두 방식을 **병행 검색 후 병합(distinct)**하여 재현율을 높인다.

> ⚠️ **`llm-agent` 소스 확인 결과 (`libs/core/service.py`)**: `text_matching`은 Qdrant의
> `MatchText` 필터로 **`content` 필드만** 검색한다(`extended_content`는 검색 대상이 아님).
> 콜렉션 생성 시 `content` 필드에만 `PayloadSchemaType.TEXT` 인덱스(주석: "BM25 키워드 검색용")를
> 걸기 때문이다. 즉, `error_keyword`(오류 코드 등)로 text_matching 검색이 히트하려면, **등록 시점의
> `content`에 그 키워드가 실제로 포함되어 있어야 한다.** 이에 따라 `register_error_resolution`은
> `content`를 `error_summary`와 `error_keyword`를 서버가 직접 결합해 생성한다(3.2절) — 호출자가
> 수동으로 챙기지 않아도 항상 키워드가 포함되도록 보장한다.
- **입력**:
  - `error_summary` (str, 필수): 벡터 검색 쿼리로 사용할 오류 내용 요약. 300자 이내, bge-m3 tokenizing에
    적합하게 작성된 문장 (4절 작성 기준과 동일).
  - `error_keyword` (str, 필수): 텍스트 매칭 검색 쿼리로 사용할 핵심 식별 키워드. 오류 코드
    (예: `ORA-00001`, `HTTP 500`)나 예외 클래스명 등 정확히 일치해야 의미 있는 토큰.
- **동작**:
  1. **벡터 검색**: `search_method="vector"`, `query=error_summary`, `limit=RAG_VECTOR_SEARCH_LIMIT`
     (기본 3)로 `POST /api/rag/search` 호출.
  2. **텍스트 매칭 검색**: `search_method="text_matching"`, `query=error_keyword`,
     `limit=RAG_TEXT_MATCHING_LIMIT`(기본 2)로 `POST /api/rag/search` 호출.
  3. 두 호출 모두 환경변수로 고정된 `collection_id`, `domain_id`를 동일하게 사용한다.
  4. 두 결과 리스트를 병합하고, `SearchResult.id`(지식 데이터 고유 ID) 기준으로 **distinct** 처리한다.
     동일 `id`가 두 검색 모두에서 나오면 벡터 검색 결과(먼저 수집된 항목)를 채택해 순서를 유지한다.
     (이 병합/중복제거 로직은 이 도구에 특화된 것이므로 범용 `RagClient`가 아니라 `server.py`의 도구
     함수 내부에 둔다 — SRP: `RagClient`는 단일 검색 호출만 책임진다.)
  5. 병합된 목록을 그대로 AI Agent가 읽을 수 있는 JSON 문자열로 반환한다. 조치 방법 판단은 AI
     Agent에게 위임(본 서버는 검색만 수행).
- **출력**: 병합·중복제거된 `SearchResult[]`의 JSON 문자열. 최대 5건(모두 상이할 경우) ~ 최소 3건
  (텍스트 매칭 결과가 전부 벡터 결과와 중복일 경우), 둘 다 없으면 빈 배열 `[]`.

### 3.2 `register_error_resolution`
- **목적**: 오류 및 조치 결과를 표준 "오류 및 조치 보고서" 형식으로 RAG에 등록한다.
- **입력** (모두 필수):
  - `error_summary` (str): 오류 요약. **300자 이내**(단독 기준 — keyword 결합과 무관하게 이 필드
    자체의 길이만 검증), bge-m3 tokenizing에 친화적으로 작성(불필요한 특수문자·중복 표현 배제,
    핵심 키워드 중심의 간결한 문장).
  - `error_keyword` (list[str]): `search_similar_error`의 text_matching 검색이 향후 이 사례를 찾을 수
    있도록 쓰이는 오류 코드/식별 키워드 목록(예: `["ORA-00001", "HTTP 500"]`). **최대 3개**까지 지정
    가능(1개 이상 필수).
  - `error_occurred_at` (str): 오류 발생일시
  - `error_content` (str): 오류 내용 (상세)
  - `action_taken_at` (str): 조치일시
  - `actor` (str): 조치자
  - `action_content` (str): 조치 내용
- **동작**:
  1. `error_summary`가 300자를 초과하면 등록을 거부한다. 이 검증은 **`error_summary` 문자열
     단독**에만 적용한다(상수 `MAX_ERROR_SUMMARY_LENGTH = 300`, `config.py`에서 관리).
  2. `error_keyword` 개수를 검증한다: 1개 이상 `MAX_ERROR_KEYWORD_COUNT = 3`(`config.py` 상수) 이하가
     아니면 등록을 거부한다.
  3. **`content`를 `error_summary`와 `error_keyword` 목록을 결합해 서버가 직접 생성한다** — 호출자가
     요약문 안에 키워드를 수동으로 끼워 넣도록 요구하는 대신, `config.py`의 결합 템플릿 상수
     (`CONTENT_COMPOSE_TEMPLATE = "{error_summary} [{keywords}]"`, `keywords`는 `", ".join(error_keyword)`)
     로 항상 모든 키워드가 포함되도록 보장한다. 이렇게 하면 text_matching이 `content` 필드만 검색하는
     제약(3.1절)을 빠뜨릴 위험이 없다. 결합 후 `content`의 최종 길이에는 **별도 상한을 두지 않는다**
     (요구사항: keyword 최대 3개 제한으로 충분히 짧게 유지되므로 별도 300자 재검증 없음).
  4. 위 5개 보고서 필드를 **표준 보고서 템플릿**(3.3절)에 대입하여 `extended_content`를 생성한다.
  5. `KnowledgeCreate` 페이로드(`collection_name`, `domain_id` — 환경변수 고정값, `content`(3번에서
     결합 생성한 값), `extended_content`, `source`)를 구성한다. `source`는 신규 등록 건이므로
     `point_id`는 지정하지 않는다 (수정/Upsert는 본 도구의 범위 밖).
     - `source` 값은 환경변수 `RAG_SOURCE`(기본값 `"error-resolution-report"`)로 고정 관리한다 — 검색 시
       출처 필터링에 활용 가능.
  6. `POST /api/rag/knowledge` 호출 후 응답(등록된 `point_id` 등)을 반환한다.
- **출력**: 등록 결과 JSON 문자열.

### 3.3 오류 및 조치 보고서 템플릿 (`extended_content`)
표준 오류 조치 보고서 양식을 고정 템플릿으로 `config.py`에 상수로 정의하고, 입력값을 대입해 생성한다.

```text
# 오류 및 조치 보고서

- 오류 발생일시: {error_occurred_at}
- 오류 내용: {error_content}
- 조치일시: {action_taken_at}
- 조치자: {actor}
- 조치 내용: {action_content}
```

## 4. `content` / `extended_content` 필드 설계 원칙

| 필드 | 용도 | 작성 기준 |
|------|------|-----------|
| `content` | 벡터 검색(임베딩) **및** text_matching 검색(`MatchText`, `content`에만 걸린 TEXT 인덱스) 대상 | `error_summary`(bge-m3 tokenizer 친화적 요약 문장, **단독 300자 이내**) + `error_keyword` 목록(최대 3개)을 **서버가 결합 템플릿으로 조합**한 최종 문자열. 결합 후 문자열 자체에는 별도 길이 상한 없음(keyword 개수 제한으로 충분히 제어됨) |
| `extended_content` | 검색 결과에서 실제 활용할 정보. **검색 대상 아님**(벡터·text_matching 모두 미포함) | 3.3절 템플릿에 따른 오류 및 조치 보고서 전문(全文) |

- `search_similar_error`의 벡터 검색 쿼리는 `error_summary`(요약 문장만, keyword 결합 전)를 그대로
  사용한다. 등록 시 `content`는 keyword가 결합된 값이지만, 임베딩 모델 특성상 요약 문장이 벡터의
  대부분을 지배하므로 순수 요약으로 질의해도 유사도 검색은 정상 동작한다.
- 등록 시 `content`에는 최대 3개의 `error_keyword` 원문이 모두 결합되어 들어가므로, 검색 시
  `search_similar_error`의 `error_keyword`(단일 문자열, 3.1절)가 그 3개 중 **어느 하나와**라도 정확히
  일치하면 `MatchText`가 히트한다.
- **`extended_content`는 어떤 검색 방식으로도 검색되지 않는다**(`llm-agent` 소스 확인). 그래서
  `error_keyword` 목록을 `extended_content`(보고서 본문)에만 적어두는 것으로는 부족하며, 반드시
  `content` 결합 시점에 함께 들어가야 한다 — 이를 호출자 책임(수동 포함 후 검증/거부)이 아니라
  **서버 로직으로 강제**하는 것이 이번 설계의 핵심이다.

## 5. API 연동 설계 (확인 완료 — `llm-agent` `/openapi.json` 및 실제 호출로 검증)

`llm-agent`(로컬 `http://localhost:28000`, 컨테이너 내부 `8000`포트, `docker-compose.yml`의
`aipro-plus` 프로젝트에서 기동)의 OpenAPI 스펙(`GET /openapi.json`)을 직접 조회하고,
`POST /api/rag/search`를 실제 호출해 아래 스펙을 확인했다.

> ⚠️ 두 엔드포인트 모두 OpenAPI 문서상 `security: [{"HTTPBearer": []}]`가 선언되어 있으나, 실제로는
> Authorization 헤더 없이 200 응답이 확인되었다 (사용자 확인: "현재는 api-key 없이 접근 가능"). 향후
> 인증이 활성화될 수 있으므로 클라이언트는 `RAG_API_BEARER_TOKEN`이 설정된 경우에만 Bearer 헤더를
> 실어 보내도록 구현한다(선택적 인증).

### 5.1 검색: `POST /api/rag/search` — Request: `SearchRequest`
`search_similar_error`는 아래 두 요청을 **순차 또는 병행 호출**한 뒤 결과를 병합한다.
```json
// 호출 1: 벡터 검색 (오류 요약 기반, 의미 유사도)
{
  "collection_id": "<ENV: RAG_COLLECTION_NAME>",
  "domain_id": "<ENV: RAG_DOMAIN_ID (int)>",
  "query": "<error_summary>",
  "search_method": "vector",
  "limit": 3
}
```
```json
// 호출 2: 텍스트 매칭 검색 (오류 코드 등 핵심 키워드, 정확 일치)
{
  "collection_id": "<ENV: RAG_COLLECTION_NAME>",
  "domain_id": "<ENV: RAG_DOMAIN_ID (int)>",
  "query": "<error_keyword>",
  "search_method": "text_matching",
  "limit": 2
}
```
Response: `SearchResult[]` (실제 호출로 확인된 필드; 두 응답을 `id` 기준 distinct 병합)
```json
[
  {
    "id": "3cf5d958-...",
    "collection": "ec_v0_2_validation",
    "score": 0.7221702,
    "content": "...",
    "extended_content": "...",
    "domain_id": 4,
    "source": "ANOMALY",
    "created_at": "2026-09-03T08:27:22.766161+00:00"
  }
]
```
- 유사 사례가 없으면 빈 배열 `[]`을 반환한다(별도 에러 아님).
- `collection_id`/`domain_id`는 `null` 허용(전체 대상 검색)이지만, 본 서버는 환경변수로 **항상 고정값**을
  채워 넣어 특정 collection/domain으로 검색을 제한한다.

### 5.2 등록: `POST /api/rag/knowledge` — Request: `KnowledgeCreate`
```json
{
  "collection_name": "<ENV: RAG_COLLECTION_NAME>",
  "domain_id": "<ENV: RAG_DOMAIN_ID (int)>",
  "content": "<error_summary, 300자 이내>",
  "extended_content": "<오류 및 조치 보고서 전문>",
  "source": "<ENV: RAG_SOURCE, 기본 'error-resolution-report'>"
}
```
- `collection_name`, `domain_id`, `content`, `extended_content`, `source` 모두 **필수** 필드다
  (OpenAPI 스펙상 `required`).
- `point_id`는 선택 필드로, 지정 시 기존 데이터 수정(Upsert)이 된다. 본 서버는 항상 신규 등록만
  수행하므로 `point_id`를 채우지 않는다.
- Response (확인 완료 — 테스트 전용 도메인/콜렉션을 만들어 실제 등록 호출로 검증 후 삭제함):
  ```json
  {
    "id": "4b743bdf-6a28-4977-be78-d51aadee7405",
    "status": "success",
    "created_at": "2026-09-03T09:22:13.740900+00:00"
  }
  ```
  `id`는 등록된 지식의 `point_id`(검색 응답의 `SearchResult.id`와 동일한 UUID), `status`는 성공
  시 `"success"` 고정 문자열, `created_at`은 ISO 8601 등록 시각이다.
- 검증 시 등록한 `content`(`"... [ORA-00001, CONN_POOL_EXHAUSTED]"`)로 실제 검색까지 재확인:
  - 벡터 검색(원본 요약 문장으로 질의) → 정상 히트 (score 0.90).
  - text_matching 검색(`query="ORA-00001"`) → 정상 히트 (score 1.0).
  - text_matching 검색(`extended_content`에만 있는 문구로 질의) → **빈 배열** — `extended_content`가
    검색 대상이 아님을 실증(3.1/4절 내용과 일치).

### 5.3 검색 요청의 `collection_id` vs 등록 요청의 `collection_name`
두 API가 같은 대상을 가리키는 필드명이 다르다(`SearchRequest.collection_id` / `KnowledgeCreate.collection_name`).
환경변수는 의미상 하나의 값(고정 콜렉션 식별자)이며, 클라이언트 내부에서 각 요청 스키마에 맞는
필드명으로 매핑한다(예: env `RAG_COLLECTION_NAME` 값을 검색 시 `collection_id`, 등록 시
`collection_name`으로 각각 세팅).

## 6. 환경 변수

`email_mcp`, `extract_error_log_mcp`와 동일하게 `.env` 기반 `Settings` 클래스로 관리하며, 모든 상수는
`config.py`에서 관리한다 (하드코딩 금지 원칙).

| 변수명 | 필수 여부 | 설명 |
|--------|-----------|------|
| `RAG_API_BASE_URL` | 필수 | `llm-agent` 서비스 기본 URL (현재 로컬 기동: `http://localhost:28000`) |
| `RAG_API_BEARER_TOKEN` | 선택 | 인증 토큰. 현재는 미인증 접근 가능하므로 비워두면 Authorization 헤더를 생략한다 |
| `RAG_API_SSL_VERIFY` | 선택 (기본 `false`) | SSL 인증서 검증 여부 |
| `RAG_API_TIMEOUT` | 선택 (기본 `60`) | HTTP 타임아웃(초) |
| `RAG_COLLECTION_NAME` | 필수 | 고정 콜렉션 식별자. 검색 시 `collection_id`, 등록 시 `collection_name`으로 매핑 |
| `RAG_DOMAIN_ID` | 필수 | 고정 도메인 ID. **정수**로 파싱하여 두 API 모두에 전달 |
| `RAG_VECTOR_SEARCH_LIMIT` | 선택 (기본 `3`) | 벡터 검색(`search_method=vector`) 시 `SearchRequest.limit` |
| `RAG_TEXT_MATCHING_LIMIT` | 선택 (기본 `2`) | 텍스트 매칭 검색(`search_method=text_matching`) 시 `SearchRequest.limit` |
| `RAG_SOURCE` | 선택 (기본 `error-resolution-report`) | 등록 시 `KnowledgeCreate.source` 값(출처 태그) |

`MAX_ERROR_SUMMARY_LENGTH`(300), `MAX_ERROR_KEYWORD_COUNT`(3), `CONTENT_COMPOSE_TEMPLATE`,
보고서 템플릿 문자열 등은 환경변수가 아니라 **도메인 상수**이므로 `config.py` 내 상수로 관리한다
(환경별로 바뀌는 값이 아님).

## 7. 프로젝트 구조 (예정)

```text
mcp-server/
├── pyproject.toml (entrypoint 추가: error-rag-mcp)
├── src/
│   ├── email_mcp/                 (기존)
│   ├── extract_error_log_mcp/     (기존)
│   └── error_rag_mcp/             (신규)
│       ├── __init__.py
│       ├── config.py   # Settings, 상수(엔드포인트 경로, MAX_ERROR_SUMMARY_LENGTH, MAX_ERROR_KEYWORD_COUNT, 보고서 템플릿)
│       ├── client.py   # RagClient — search() / register() (httpx 기반)
│       └── server.py   # MCPServer 생성, search_similar_error / register_error_resolution 등록, main()
├── tests/
│   └── (error_rag_mcp용 test_config.py / test_client.py / test_server.py 추가 필요)
└── docs/
    └── error_rag_mcp_requirements.md (본 문서)
```

패키지명은 `error_rag_mcp`(제안)로 하며, 기존 두 서버와 동일하게 `client.py`(HTTP) →
`config.py`(ENV) 의존, `server.py`(MCP) → `client.py` 의존 구조를 따른다 (의존성 역전: `RagClient`는
`Settings`를 주입받음).

## 8. 비기능 요구사항 (CLAUDE.md 그라운드 룰 매핑)

- **TDD**: `test_config.py`(환경변수 로딩/검증), `test_client.py`(search/register HTTP 호출, respx 목킹),
  `test_server.py`(도구 등록, 벡터+텍스트 매칭 2회 호출 및 `id` 기준 distinct 병합 로직, `content`
  결합 템플릿 조합 결과, `error_summary` 300자 초과 거부, `error_keyword` 개수(0개/4개 이상) 초과
  거부 등 예외 케이스) 선 작성 후 구현. 커버리지 85% 이상 유지.
- **SOLID**: config(설정)/client(통신)/server(MCP 도구) 3계층 분리를 유지해 단일 책임을 지키고,
  `RagClient`는 `Settings` 추상에 의존(의존성 역전)한다.
- **하드코딩 금지**: API 경로, `MAX_ERROR_SUMMARY_LENGTH`, `MAX_ERROR_KEYWORD_COUNT`,
  `CONTENT_COMPOSE_TEMPLATE`, 보고서 템플릿 문자열은 모두 `config.py` 상수로 관리.
- **문서 최신화**: 구현 완료 시 `docs/architecture.md`, `docs/usage.md`, `docs/installation-guide.md`에
  본 서버 관련 내용을 반영해야 한다.

## 9. Open Issues

해결됨:
- ~~인증 방식~~ → 확인 완료: 현재 API Key 없이 접근 가능 (5절 참조). 인증 재도입 대비, 클라이언트는
  `RAG_API_BEARER_TOKEN` 설정 시에만 Bearer 헤더를 선택적으로 부착.
- ~~요청/응답 필드명~~ → 확인 완료: `SearchRequest`/`SearchResult`/`KnowledgeCreate` 스키마 확보 (5절).
- ~~검색 결과 없음 시 응답 형태~~ → 확인 완료: 빈 배열 `[]`.
- ~~text_matching이 `content`/`extended_content` 중 무엇을 검색하는지~~ → 확인 완료:
  `aipro-plus/libs/core/service.py`의 `create_collection()`(Qdrant `content` 필드에만
  `PayloadSchemaType.TEXT` 인덱스 생성)과 검색 로직(`qmodels.MatchText(text=query)`를 `content` 키에만
  적용) 확인. **`content`만 검색되며 `extended_content`는 검색 대상이 아니다.** → 3.1/3.2/4절에 반영
  (`error_keyword`(최대 3개)는 서버가 `content` 결합 시 항상 함께 넣도록 강제함).
- ~~등록 API(`POST /api/rag/knowledge`) 응답 바디 형태~~ → 확인 완료: 테스트 전용 도메인
  (`error_rag_mcp_test`, id=6)/콜렉션(`error_rag_mcp_test`)을 새로 만들어 실제 등록 호출로 검증한 뒤
  삭제함(운영 데이터 오염 없음). 응답은 `{"id": "<point_id, uuid>", "status": "success", "created_at":
  "<ISO 8601>"}` (5.2절 참조). 같은 세션에서 등록한 `content`로 벡터 검색·text_matching 검색·
  `extended_content` 미검색까지 모두 재검증됨.

구현 착수 전 남은 확인 필요 사항:
1. `RAG_COLLECTION_NAME`(콜렉션 식별자)과 `RAG_DOMAIN_ID`(도메인 ID, 정수) 값으로 실제 사용할
   운영값 확정 — 검증에 쓴 테스트 값(`error_rag_mcp_test`/`6`)은 삭제되었으며, 운영에는 별도의
   전용 콜렉션/도메인을 새로 만들어야 한다.
2. `error_summary` 300자 제한이 문자 수 기준인지, bge-m3 토큰 수 기준인지 최종 확정 필요(현재는
   문자 수 300 기준으로 가정).
3. `RAG_SOURCE` 기본값(`error-resolution-report`)이 조직의 기존 `source` 태그 컨벤션(예: 검색
   테스트에서 관측된 `"ANOMALY"`)과 일관되는지 확인.
