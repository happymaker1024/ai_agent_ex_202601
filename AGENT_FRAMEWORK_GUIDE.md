# Agent Framework 전환 가이드

이 프로젝트는 **CrewAI**와 **LangGraph** 두 가지 에이전트 프레임워크를 지원합니다.

## 프레임워크 비교

### CrewAI
- **특징**: Task와 Agent 기반의 협업 구조
- **장점**:
  - 에이전트 간 역할 분담이 명확
  - Task 기반 워크플로우가 직관적
  - 에이전트 협업 시나리오에 최적화
- **사용 사례**: 여러 에이전트가 협업하여 복잡한 작업을 수행

### LangGraph
- **특징**: StateGraph 기반의 상태 관리 구조
- **장점**:
  - 상태 관리가 명시적이고 추적 가능
  - 복잡한 워크플로우 제어가 용이
  - 조건부 분기와 반복 로직 구현이 유연
- **사용 사례**: 복잡한 상태 전이와 워크플로우 제어가 필요한 경우

## 프레임워크 전환 방법

### 1. 환경변수 설정

`backend/.env` 파일을 생성하거나 수정합니다:

```bash
# CrewAI 사용 (기본값)
AGENT_FRAMEWORK=crewai
```

또는

```bash
# LangGraph 사용
AGENT_FRAMEWORK=langgraph
```

### 2. 의존성 설치

LangGraph를 처음 사용하는 경우, 의존성을 다시 설치합니다:

```bash
cd backend
uv pip install -r requirements.txt
```

### 3. 서버 재시작

백엔드 서버를 재시작합니다:

```bash
cd backend
uv run python main.py
```

## 동작 확인

### API 엔드포인트 확인

브라우저에서 `http://localhost:8000`에 접속하면 현재 사용 중인 프레임워크를 확인할 수 있습니다:

```json
{
  "message": "투자 레포팅 Agent API",
  "version": "3.0.0",
  "agent_framework": "crewai",  // 또는 "langgraph"
  "mode": "CREWAI-powered",      // 또는 "LANGGRAPH-powered"
  "endpoints": {
    "home": "/",
    "invest_report": "/invest_report"
  }
}
```

### 프론트엔드에서 테스트

프론트엔드(`http://localhost:3000`)에서 기업을 선택하고 레포트를 생성하면, 백엔드 콘솔에서 어떤 프레임워크가 사용되는지 확인할 수 있습니다:

```
============================================================
CrewAI 분석 시작: 삼성전자
============================================================
```

또는

```
============================================================
LangGraph 분석 시작: 삼성전자
============================================================
```

## 구현 세부사항

### 공통 기능
- 4개의 에이전트: 재무 분석가 → 시장 분석가 → 리스크 분석가 → 투자 어드바이저
- 동일한 도구(Tools): `get_stock_price_data`, `get_company_info`, `calculate_financial_ratios`, `get_market_index`
- 순차적 실행: 각 에이전트는 이전 에이전트의 결과를 받아 분석

### CrewAI 구현 (`backend/crewai_/`)
```python
# Agent와 Task를 생성하고 Crew로 조합
crew = Crew(
    agents=[financial_analyst, market_analyst, risk_analyst, investment_advisor],
    tasks=[task1, task2, task3, task4],
    process=Process.sequential
)
result = crew.kickoff()
```

### LangGraph 구현 (`backend/langgraph_/`)
```python
# StateGraph로 워크플로우 정의
workflow = StateGraph(AgentState)
workflow.add_node("financial_analyst", self._financial_analyst_node)
workflow.add_node("market_analyst", self._market_analyst_node)
# ... 노드와 엣지 추가
graph = workflow.compile()
result = graph.invoke(initial_state)
```

## 문제 해결

### 프레임워크가 전환되지 않는 경우

1. `.env` 파일이 `backend/` 디렉토리에 있는지 확인
2. 환경변수 이름이 정확한지 확인: `AGENT_FRAMEWORK`
3. 값이 올바른지 확인: `crewai` 또는 `langgraph` (소문자)
4. 서버를 완전히 재시작

### 의존성 오류가 발생하는 경우

```bash
cd backend
uv pip install -r requirements.txt
```

### OpenAI API 오류가 발생하는 경우

`.env` 파일에 올바른 OpenAI API 키가 설정되어 있는지 확인:

```bash
OPENAI_API_KEY=sk-...
```

## 성능 비교

두 프레임워크는 비슷한 성능을 보이며, 실행 시간은 주로 OpenAI API 호출에 의해 결정됩니다:

- **CrewAI**: 약 30~60초
- **LangGraph**: 약 30~60초

실제 성능은 네트워크 상태와 OpenAI API 응답 시간에 따라 달라집니다.

## 추가 정보

- CrewAI 공식 문서: https://docs.crewai.com/
- LangGraph 공식 문서: https://langchain-ai.github.io/langgraph/
