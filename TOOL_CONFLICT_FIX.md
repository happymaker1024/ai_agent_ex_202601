# Tool Import 충돌 문제 해결

## 문제 증상

CrewAI 선택 시 다음 오류 발생:

```
ValidationError: 3 validation errors for Agent
tools.0
  Input should be a valid dictionary or instance of BaseTool [type=model_type,
  input_value=StructuredTool(name='get_...), input_type=StructuredTool]
```

## 근본 원인

### sys.path 충돌

`main.py`에서 두 디렉토리를 모두 sys.path에 추가:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crewai_'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langgraph_'))  # 먼저 추가됨!
```

**결과**: `langgraph_`가 먼저 추가되어, `stock_analysis_tool`을 import하면 **LangGraph 버전**이 import됨!

### Tool 타입 불일치

- **CrewAI Tool**: `@tool` from `crewai.tools.base_tool`
- **LangGraph Tool**: `@tool` from `langchain_core.tools` → `StructuredTool` 생성

CrewAI Agent는 CrewAI Tool만 받을 수 있는데, LangGraph의 `StructuredTool`이 전달되어 **타입 검증 실패**!

## 해결 방법

### importlib을 사용한 명시적 모듈 로드

`crewai_agent.py`에서 파일 경로로 직접 모듈을 로드:

```python
import importlib.util
from pathlib import Path

# 현재 디렉토리의 stock_analysis_tool을 동적으로 로드
current_dir = Path(__file__).parent
tool_file = current_dir / "stock_analysis_tool.py"

# 모듈을 명시적으로 로드
spec = importlib.util.spec_from_file_location("crewai_stock_analysis_tool", tool_file)
tool_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_module)

# Tool 함수들을 가져오기
get_stock_price_data = tool_module.get_stock_price_data
get_company_info = tool_module.get_company_info
calculate_financial_ratios = tool_module.calculate_financial_ratios
get_market_index = tool_module.get_market_index
get_ticker_from_company_name = tool_module.get_ticker_from_company_name
```

### 장점

1. ✅ **sys.path 충돌 완전 회피**: import 경로에 의존하지 않음
2. ✅ **명시적 로딩**: 정확히 어떤 파일을 로드하는지 명확
3. ✅ **독립성**: LangGraph의 tool과 완전히 분리

## 수정된 파일

### `backend/crewai_/crewai_agent.py`

**변경 전**:
```python
from stock_analysis_tool import (
    get_stock_price_data,
    # ...
)
```

**변경 후**:
```python
import importlib.util
from pathlib import Path

current_dir = Path(__file__).parent
tool_file = current_dir / "stock_analysis_tool.py"

spec = importlib.util.spec_from_file_location("crewai_stock_analysis_tool", tool_file)
tool_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_module)

get_stock_price_data = tool_module.get_stock_price_data
# ...
```

## 검증 방법

### 1. 백엔드 서버 재시작

```bash
cd backend
# Ctrl+C로 기존 서버 종료
uv run python main.py
```

### 2. Tool 타입 확인 로그

서버 시작 시 다음 로그가 출력되어야 함:

```
[CrewAI] Tool 로드 완료:
  get_stock_price_data 타입: <class 'crewai.tools.base_tool.BaseTool'>
  모듈: crewai_stock_analysis_tool
```

### 3. CrewAI 테스트

프론트엔드에서:
1. **AI Agent**: CrewAI 선택
2. **기업**: SK하이닉스 선택
3. **레포팅 요청** 클릭

### 4. 정상 동작 확인

백엔드 터미널에서:
```
============================================================
CrewAI 분석 시작: SK하이닉스
============================================================

[진행 상황] CrewAI Crew 실행 시작
...

# Agent: Financial Analyst
## Using tool: Get Company Information
## Using tool: Get Stock Price Data
...
```

**오류 없이 진행**되어야 함!

## Tool 타입 비교

### CrewAI Tool (@tool from crewai.tools.base_tool)

```python
from crewai.tools.base_tool import tool

@tool("Get Stock Price Data")
def get_stock_price_data(ticker: str, days: int = 30) -> str:
    # ...

# 타입: <class 'crewai.tools.base_tool.BaseTool'>
```

### LangGraph Tool (@tool from langchain_core.tools)

```python
from langchain_core.tools import tool

@tool
def get_stock_price_data(ticker: str, days: int = 30) -> str:
    # ...

# 타입: <class 'langchain_core.tools.StructuredTool'>
```

## 대안적 해결 방법 (참고)

### 방법 1: sys.path 순서 조정

```python
# main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langgraph_'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crewai_'))  # 나중에 추가하면 우선순위 높음
```

**단점**: 여전히 import 순서에 의존

### 방법 2: 별칭 사용

```python
# crewai_/crewai_stock_tool.py로 이름 변경
from crewai_stock_tool import get_stock_price_data
```

**단점**: 파일명 변경 필요

### 방법 3 (채택): importlib 사용

**장점**:
- ✅ 파일명 변경 불필요
- ✅ sys.path 독립적
- ✅ 명시적이고 안전

## 트러블슈팅

### 여전히 ValidationError 발생 시

1. **백엔드 재시작 확인**
   ```bash
   # 반드시 Ctrl+C로 종료 후 재시작!
   cd backend
   uv run python main.py
   ```

2. **Tool 타입 로그 확인**
   서버 시작 시 `[CrewAI] Tool 로드 완료` 로그 확인

3. **오류 메시지 확인**
   - `StructuredTool` 언급 → LangGraph tool이 로드됨 (문제!)
   - `BaseTool` 타입 → CrewAI tool이 로드됨 (정상!)

4. **캐시 문제 확인**
   ```bash
   cd backend
   # __pycache__ 삭제
   find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
   uv run python main.py
   ```

## 결론

- ✅ **근본 원인**: sys.path에서 LangGraph가 우선순위로 인해 잘못된 tool import
- ✅ **해결 방법**: importlib을 사용한 명시적 모듈 로드
- ✅ **효과**: CrewAI와 LangGraph의 tool 완전 분리

---

**업데이트**: 2026-01-30
**상태**: ✅ 해결 완료
