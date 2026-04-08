# CLAUDE.md

## 개발 그라운드 룰

모든 작업에서 아래 규칙을 반드시 준수한다.

### 1. TDD 기반 개발
- 테스트를 먼저 작성한 후 구현한다.
- test coverage 85% 이상을 항상 유지한다.

### 2. SOLID 원칙 준수
- **S** — 단일 책임 원칙 (Single Responsibility)
- **O** — 개방-폐쇄 원칙 (Open/Closed)
- **L** — 리스코프 치환 원칙 (Liskov Substitution)
- **I** — 인터페이스 분리 원칙 (Interface Segregation)
- **D** — 의존성 역전 원칙 (Dependency Inversion)

### 3. 하드코딩 금지
- 코드 내 상수 직접 삽입 금지.
- 모든 상수는 별도 config 파일에서 관리한다.

### 4. 문서 항상 최신화
- 요구사항, 아키텍처 정의, 기능 설계, 사용 가이드 등 관련 문서를 작업마다 업데이트한다.
