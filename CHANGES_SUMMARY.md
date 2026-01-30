# 변경 사항 요약

## 완료된 작업

### 1. ✅ 프론트엔드에서 Agent 프레임워크 선택 기능 추가

**변경 파일**: `frontend/src/App.js`, `frontend/src/App.css`

#### 추가된 기능:
- **Agent 선택 드롭다운**: LangGraph / CrewAI 선택 가능
- **기본값**: LangGraph (추천)
- **UI 개선**:
  - Agent 선택 select box (보라색)
  - 기업 선택 select box (파란색)
  - 로딩 중 선택한 프레임워크 표시

#### 사용 방법:
```jsx
// App.js
const [selectedAgent, setSelectedAgent] = useState('langgraph');

// API 호출 시 선택한 agent 전송
axios.post('http://localhost:8000/invest_report', {
  company: selectedCompany,
  agent_framework: selectedAgent
});
```

---

### 2. ✅ 백엔드 Agent 선택 API 추가

**변경 파일**: `backend/main.py`

#### 수정 내용:
```python
class InvestReportRequest(BaseModel):
    company: str
    agent_framework: Optional[str] = None  # 프론트엔드에서 선택한 agent

@app.post("/invest_report")
async def get_invest_report(request: InvestReportRequest):
    # 프론트엔드에서 선택한 framework 우선, 없으면 환경변수 사용
    selected_framework = request.agent_framework or AGENT_FRAMEWORK

    if selected_framework == "langgraph":
        # LangGraph 실행
    else:
        # CrewAI 실행
```

#### 동작 방식:
1. **프론트엔드 선택 우선**: 사용자가 UI에서 선택한 agent 사용
2. **환경변수 폴백**: 선택하지 않으면 `.env`의 `AGENT_FRAMEWORK` 사용
3. **기본값**: 모두 없으면 `crewai` 사용

---

### 3. ✅ LangGraph Agent 실행 오류 수정

**변경 파일**: `backend/langgraph_/langgraph_agent.py`

#### 문제점:
- 복잡한 StateGraph 구조로 인한 상태 관리 오류
- 메시지 누적으로 인한 빈 결과 반환

#### 해결 방법:
- **StateGraph 제거**: 단순한 순차 실행 구조로 변경
- **직접 함수 호출**: 각 에이전트를 일반 메서드로 구현
- **명확한 상태 관리**: 각 에이전트 결과를 변수로 저장

```python
class InvestmentReportingGraph:
    def run_analysis(self, company_name: str):
        # 순차적으로 각 에이전트 실행
        financial_analysis = self._financial_analyst(company_name, ticker)
        market_analysis = self._market_analyst(company_name, financial_analysis)
        risk_assessment = self._risk_analyst(company_name, ticker,
                                             financial_analysis, market_analysis)
        investment_recommendation = self._investment_advisor(
            company_name, ticker, financial_analysis,
            market_analysis, risk_assessment
        )

        return {
            "analysis_result": investment_recommendation,
            "status": "success"
        }
```

---

### 4. ✅ LangGraph 실행 과정 로그 출력 추가

**변경 파일**: `backend/langgraph_/langgraph_agent.py`

#### 추가된 로그:

```python
# 전체 진행 상황
print("[진행 상황] 1/4 단계: 재무 분석")
print("[진행 상황] 2/4 단계: 시장 분석")
print("[진행 상황] 3/4 단계: 리스크 분석")
print("[진행 상황] 4/4 단계: 투자 의견 작성")

# 각 에이전트별 상세 로그
def _call_agent(self, agent_name, system_prompt, user_prompt):
    print(f"\n{'='*60}")
    print(f"[{agent_name}] 분석 시작")
    print(f"{'='*60}")

    # ... API 호출 ...

    print(f"[{agent_name}] 분석 완료 (길이: {len(result)} 문자)")
    print(f"{'='*60}\n")

# 데이터 수집 로그
print(f"[재무 분석가] {company_name}의 실제 데이터 수집 중...")
print(f"[재무 분석가] 데이터 수집 완료")
```

#### 백엔드 터미널 출력 예시:
```
============================================================
LangGraph 투자 레포팅 분석 시작: 삼성전자
============================================================

[진행 상황] 1/4 단계: 재무 분석

============================================================
[재무 분석가] 분석 시작
============================================================
[재무 분석가] 삼성전자의 실제 데이터 수집 중...
[재무 분석가] 데이터 수집 완료
[재무 분석가] 분석 완료 (길이: 1247 문자)
============================================================

[진행 상황] 2/4 단계: 시장 분석

============================================================
[시장 분석가] 분석 시작
============================================================
[시장 분석가] 시장 지수 데이터 수집 중...
[시장 분석가] 데이터 수집 완료
[시장 분석가] 분석 완료 (길이: 983 문자)
============================================================

[진행 상황] 3/4 단계: 리스크 분석

============================================================
[리스크 분석가] 분석 시작
============================================================
[리스크 분석가] 리스크 데이터 수집 중...
[리스크 분석가] 데이터 수집 완료
[리스크 분석가] 분석 완료 (길이: 876 문자)
============================================================

[진행 상황] 4/4 단계: 투자 의견 작성

============================================================
[투자 어드바이저] 분석 시작
============================================================
[투자 어드바이저] 최신 주가 데이터 확인 중...
[투자 어드바이저] 데이터 확인 완료
[투자 어드바이저] 분석 완료 (길이: 654 문자)
============================================================

============================================================
[완료] 모든 분석이 완료되었습니다!
============================================================
```

---

## 테스트 방법

### 1. 백엔드 서버 실행

```bash
cd backend
uv run python main.py
```

### 2. 프론트엔드 실행

```bash
cd frontend
npm start
```

### 3. 브라우저 테스트

1. `http://localhost:3000` 접속
2. **AI Agent 선택**: LangGraph 또는 CrewAI 선택
3. **기업 선택**: 삼성전자 등 기업 선택
4. **레포팅 요청** 버튼 클릭
5. 백엔드 터미널에서 실행 과정 확인

### 4. 기대 결과

#### 프론트엔드:
- Agent 선택 드롭다운 표시
- 로딩 중 선택한 프레임워크 표시
- 분석 완료 후 투자 레포트 표시

#### 백엔드 터미널:
```
============================================================
LangGraph 분석 시작: 삼성전자
============================================================

[진행 상황] 1/4 단계: 재무 분석
[재무 분석가] 분석 시작
...
[재무 분석가] 분석 완료

[진행 상황] 2/4 단계: 시장 분석
[시장 분석가] 분석 시작
...
[시장 분석가] 분석 완료

[진행 상황] 3/4 단계: 리스크 분석
[리스크 분석가] 분석 시작
...
[리스크 분석가] 분석 완료

[진행 상황] 4/4 단계: 투자 의견 작성
[투자 어드바이저] 분석 시작
...
[투자 어드바이저] 분석 완료

[완료] 모든 분석이 완료되었습니다!
```

---

## 변경 전/후 비교

### 변경 전
- ❌ `.env` 파일에서만 agent 선택 가능
- ❌ 서버 재시작 필요
- ❌ LangGraph 실행 시 빈 결과 반환
- ❌ 실행 과정이 터미널에 표시되지 않음

### 변경 후
- ✅ **프론트엔드 UI에서 실시간 선택 가능**
- ✅ **서버 재시작 불필요**
- ✅ **LangGraph 정상 동작 및 결과 반환**
- ✅ **상세한 실행 과정 로그 출력**

---

## 주요 개선 사항

1. **사용성 향상**: UI에서 클릭만으로 agent 전환
2. **안정성 향상**: LangGraph 에이전트 오류 수정
3. **디버깅 편의성**: 상세한 로그로 실행 과정 추적 가능
4. **유연성**: 환경변수 + UI 선택 모두 지원

---

## 파일 변경 목록

### 프론트엔드
- ✏️ `frontend/src/App.js` - Agent 선택 UI 추가
- ✏️ `frontend/src/App.css` - Agent 선택 스타일 추가

### 백엔드
- ✏️ `backend/main.py` - Agent 선택 API 파라미터 추가
- ✏️ `backend/langgraph_/langgraph_agent.py` - 완전 재작성 (오류 수정 + 로그 추가)

### 문서
- ➕ `CHANGES_SUMMARY.md` (이 파일)
- ➕ `TROUBLESHOOTING.md` (트러블슈팅 가이드)
- ➕ `backend/test_langgraph.py` (테스트 스크립트)

---

## 다음 단계 (선택사항)

- [ ] CrewAI 에이전트도 동일한 로그 출력 추가
- [ ] 프론트엔드에서 실시간 진행 상황 표시 (WebSocket)
- [ ] 분석 결과 비교 기능 (CrewAI vs LangGraph)
- [ ] 분석 결과 캐싱으로 성능 개선

---

## 문제 발생 시

`TROUBLESHOOTING.md` 파일을 참조하세요.
