# CrewAI 에이전트 수정 사항

## 발견된 문제

프론트엔드에서 CrewAI를 선택하고 요청했을 때 더미 데이터가 반환되는 문제가 있었습니다.

## 원인 분석

### 1. Import 경로 문제
**문제**: `backend/main.py`에서 잘못된 import 경로 사용
```python
# 잘못된 경로
from crewai_.crewai_agent import InvestmentReportingCrew
from langgraph_.langgraph_agent import InvestmentReportingGraph
```

**해결**: Python path에 이미 추가되어 있으므로 직접 import
```python
# 올바른 경로
from crewai_agent import InvestmentReportingCrew
from langgraph_agent import InvestmentReportingGraph
```

### 2. Tool 호출 방식 오류
**문제**: CrewAI tool을 LangChain 방식(`.invoke()`)으로 호출
```python
# 오류 코드
stock_data_text = get_stock_price_data.invoke({"ticker": self.ticker, "days": 30})
```

**해결**: CrewAI tool은 일반 함수처럼 직접 호출
```python
# 올바른 코드
stock_data_text = get_stock_price_data(self.ticker, days=30)
```

### 3. 로그 출력 변수 오류
**문제**: 오류 메시지에서 `AGENT_FRAMEWORK` 사용
```python
print(f"{AGENT_FRAMEWORK.upper()} 분석 오류: {str(e)}")
```

**해결**: `selected_framework` 사용
```python
print(f"{selected_framework.upper()} 분석 오류: {str(e)}")
```

## 수정된 파일

### 1. `backend/main.py`

#### 수정 1: Import 경로 수정
```python
# 변경 전
from crewai_.crewai_agent import InvestmentReportingCrew
from langgraph_.langgraph_agent import InvestmentReportingGraph

# 변경 후
from crewai_agent import InvestmentReportingCrew
from langgraph_agent import InvestmentReportingGraph
```

#### 수정 2: 오류 로그 변수 수정
```python
# 변경 전
except Exception as e:
    print(f"{AGENT_FRAMEWORK.upper()} 분석 오류: {str(e)}")

# 변경 후
except Exception as e:
    print(f"{selected_framework.upper()} 분석 오류: {str(e)}")
```

### 2. `backend/crewai_/crewai_agent.py`

#### 수정 1: Tool 호출 방식 수정
```python
# 변경 전
stock_data_text = get_stock_price_data.invoke({"ticker": self.ticker, "days": 30})
company_info_text = get_company_info.invoke({"company_name": company_name})
financial_ratios_text = calculate_financial_ratios.invoke({"ticker": self.ticker})

# 변경 후
stock_data_text = get_stock_price_data(self.ticker, days=30)
company_info_text = get_company_info(company_name)
financial_ratios_text = calculate_financial_ratios(self.ticker)
```

#### 수정 2: 상세 로그 추가
```python
# 분석 실행
print(f"\n{'='*60}")
print(f"CrewAI 투자 레포팅 분석 시작: {company_name}")
print(f"{'='*60}\n")

print("[진행 상황] CrewAI Crew 실행 시작")
print(f"- 에이전트 수: 4개")
print(f"- 태스크 수: 4개")
print(f"- 프로세스: Sequential (순차 실행)\n")

result = crew.kickoff()

print(f"\n{'='*60}")
print(f"[완료] CrewAI 분석이 완료되었습니다!")
print(f"{'='*60}\n")
```

#### 수정 3: 데이터 수집 로그 추가
```python
print(f"[데이터 수집 완료] 실제 주가 데이터 수집 성공")
```

## CrewAI vs LangGraph Tool 차이

### CrewAI Tool
```python
from crewai.tools.base_tool import tool

@tool("Get Stock Price Data")
def get_stock_price_data(ticker: str, days: int = 30) -> str:
    # ...
    return result

# 사용 방법: 일반 함수처럼 호출
data = get_stock_price_data("005930", days=30)
```

### LangGraph Tool (LangChain)
```python
from langchain_core.tools import tool

@tool
def get_stock_price_data(ticker: str, days: int = 30) -> str:
    # ...
    return result

# 사용 방법: .invoke() 메서드 사용
data = get_stock_price_data.invoke({"ticker": "005930", "days": 30})
```

## 테스트 방법

### 1. CrewAI 직접 테스트
```bash
cd backend
uv run python test_crewai.py
```

### 2. 백엔드 서버 재시작
```bash
cd backend
uv run python main.py
```

### 3. 프론트엔드에서 테스트
1. `http://localhost:3000` 접속
2. **AI Agent 선택**: CrewAI 선택
3. **기업 선택**: 삼성전자 선택
4. **레포팅 요청** 클릭

### 4. 백엔드 터미널 출력 확인

#### 정상 동작 시:
```
============================================================
CrewAI 분석 시작: 삼성전자
============================================================

[진행 상황] CrewAI Crew 실행 시작
- 에이전트 수: 4개
- 태스크 수: 4개
- 프로세스: Sequential (순차 실행)

# Agent: Financial Analyst
## Task: ...
## Using tool: Get Stock Price Data
...

# Agent: Market Analyst
## Task: ...
...

# Agent: Risk Analyst
## Task: ...
...

# Agent: Investment Advisor
## Task: ...
...

============================================================
[완료] CrewAI 분석이 완료되었습니다!
============================================================

[데이터 수집 완료] 실제 주가 데이터 수집 성공
```

#### 오류 발생 시:
```
CREWAI 분석 오류: [오류 메시지]
더미 데이터로 폴백합니다...
[상세 스택 트레이스]
```

## 예상 결과

### 프론트엔드
- CrewAI 선택 시 정상적인 투자 레포트 표시
- 실제 주가 데이터 기반 분석 결과

### 백엔드
- CrewAI verbose 모드로 상세한 에이전트 실행 과정 출력
- 4개 에이전트 순차 실행 과정 확인 가능
- 각 에이전트의 tool 사용 내역 출력

## 주요 개선 사항

1. ✅ **Import 경로 수정**: 올바른 모듈 import
2. ✅ **Tool 호출 수정**: CrewAI 방식으로 tool 호출
3. ✅ **로그 개선**: 상세한 실행 과정 출력
4. ✅ **오류 처리**: 명확한 오류 메시지 및 스택 트레이스

## 문제 해결 체크리스트

CrewAI가 여전히 작동하지 않으면:

- [ ] 백엔드 서버를 완전히 재시작했는가?
- [ ] `OPENAI_API_KEY`가 `.env`에 올바르게 설정되어 있는가?
- [ ] `uv pip install -r requirements.txt`로 의존성을 설치했는가?
- [ ] CrewAI 버전이 `0.86.0`인가? (`uv pip list | grep crewai`)
- [ ] 백엔드 터미널에 오류 메시지가 출력되는가?

## 다음 단계

CrewAI와 LangGraph 모두 정상 동작하면:

1. 두 프레임워크의 결과 비교
2. 실행 시간 및 성능 비교
3. 분석 품질 비교
4. 프론트엔드에서 편리하게 전환하며 테스트
