# 실시간 진행 상황 추적 기능 구현

## 개요

사용자 경험(UX) 향상을 위해 4개의 AI 에이전트가 분석을 진행하는 동안 프론트엔드에서 실시간으로 진행 상황을 시각적으로 표시하는 기능을 구현했습니다.

## 구현된 기능

### 1. 백엔드 - 진행 상황 추적 시스템

#### `backend/progress_tracker.py`
진행 상황을 추적하고 저장하는 모듈입니다.

**주요 구조:**
```python
class ProgressStep(BaseModel):
    step: str  # "financial_analyst", "market_analyst", "risk_analyst", "investment_advisor"
    status: str  # "pending", "in_progress", "completed"
    message: str
    timestamp: str

class AnalysisProgress(BaseModel):
    session_id: str
    company: str
    framework: str  # "crewai" or "langgraph"
    status: str  # "running", "completed", "failed"
    current_step: int  # 0-3
    steps: List[ProgressStep]
    start_time: str
    end_time: Optional[str] = None
    error: Optional[str] = None

# 메모리 저장소
progress_store: Dict[str, AnalysisProgress] = {}
```

**주요 함수:**
- `create_progress()`: 새로운 분석 세션 생성
- `update_progress()`: 각 단계의 진행 상황 업데이트
- `complete_progress()`: 분석 완료/실패 처리
- `get_progress()`: 진행 상황 조회

#### `backend/main.py` 수정사항

1. **Session ID 추가**
   ```python
   # Session ID 생성
   session_id = str(uuid.uuid4())

   # 진행 상황 초기화
   create_progress(session_id, company_name, selected_framework)
   ```

2. **진행 상황 조회 API 엔드포인트**
   ```python
   @app.get("/progress/{session_id}")
   async def get_analysis_progress(session_id: str):
       """분석 진행 상황 조회"""
       progress = get_progress(session_id)
       if not progress:
           raise HTTPException(status_code=404, detail="Session not found")
       return progress
   ```

3. **응답에 session_id 포함**
   ```python
   class InvestReportResponse(BaseModel):
       # ... 기존 필드들
       session_id: Optional[str] = None  # 진행 상황 추적용
   ```

### 2. AI 에이전트 수정

#### `backend/langgraph_/langgraph_agent.py`

각 에이전트 단계마다 진행 상황을 업데이트하도록 수정:

```python
def run_analysis(self, company_name: str, session_id: str = None):
    # ...

    # 1단계: 재무 분석
    if update_progress:
        update_progress(session_id, 0, "in_progress", "재무 데이터 수집 및 분석 중...")
    financial_analysis = self._financial_analyst(company_name, ticker)
    if update_progress:
        update_progress(session_id, 0, "completed", "재무 분석 완료")

    # 2단계: 시장 분석
    if update_progress:
        update_progress(session_id, 1, "in_progress", "시장 동향 및 경쟁사 분석 중...")
    market_analysis = self._market_analyst(company_name, financial_analysis)
    if update_progress:
        update_progress(session_id, 1, "completed", "시장 분석 완료")

    # ... 3단계, 4단계도 동일
```

#### `backend/crewai_/crewai_agent.py`

CrewAI는 모든 태스크를 순차적으로 실행하므로, kickoff() 완료 후 일괄 업데이트:

```python
def run_analysis(self, company_name: str, session_id: str = None):
    # ...

    if update_progress:
        update_progress(session_id, 0, "in_progress", "재무 데이터 수집 및 분석 중...")

    result = crew.kickoff()

    # 모든 단계 완료 표시
    if update_progress:
        update_progress(session_id, 0, "completed", "재무 분석 완료")
        update_progress(session_id, 1, "completed", "시장 분석 완료")
        update_progress(session_id, 2, "completed", "리스크 분석 완료")
        update_progress(session_id, 3, "completed", "투자 의견 작성 완료")
```

### 3. 프론트엔드 - 실시간 진행 상황 표시

#### `frontend/src/App.js`

**새로운 상태 추가:**
```javascript
const [progressData, setProgressData] = useState(null);
const [sessionId, setSessionId] = useState(null);
```

**진행 상황 폴링 함수:**
```javascript
const pollProgress = async (sid) => {
  try {
    const response = await axios.get(`http://localhost:8000/progress/${sid}`);
    setProgressData(response.data);

    // 분석이 완료되지 않았으면 계속 폴링
    if (response.data.status === 'running') {
      setTimeout(() => pollProgress(sid), 500); // 0.5초마다 업데이트
    }
  } catch (err) {
    console.error('Progress polling error:', err);
  }
};
```

**분석 시작 시 폴링 시작:**
```javascript
const response = await axios.post('http://localhost:8000/invest_report', {
  company: selectedCompany,
  agent_framework: selectedAgent
});

// session_id가 있으면 진행 상황 폴링 시작
if (response.data.session_id) {
  setSessionId(response.data.session_id);
  pollProgress(response.data.session_id);
}
```

**진행 상황 UI 표시:**
```jsx
{progressData && progressData.steps ? (
  progressData.steps.map((step, index) => (
    <div
      key={index}
      className={`step ${step.status === 'completed' ? 'completed' : step.status === 'in_progress' ? 'active' : ''}`}
    >
      <span className={`step-icon ${step.status === 'in_progress' ? 'pulse' : ''}`}>
        {index === 0 ? '📊' : index === 1 ? '📈' : index === 2 ? '⚠️' : '💡'}
      </span>
      <span>
        {step.message}
        {step.status === 'completed' && ' ✓'}
        {step.status === 'in_progress' && ' ...'}
      </span>
    </div>
  ))
) : (
  // 기본 단계 표시
)}
```

#### `frontend/src/App.css`

**진행 상황 시각적 효과:**

1. **활성 단계 (in_progress)**
   ```css
   .step.active {
     background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
     border-left: 4px solid #1e88e5;
     box-shadow: 0 4px 12px rgba(30, 136, 229, 0.2);
     transform: scale(1.02);
   }

   .step.active span:last-child {
     color: #1565c0;
     font-weight: 600;
   }
   ```

2. **완료된 단계 (completed)**
   ```css
   .step.completed {
     background: linear-gradient(135deg, #e8f5e9 0%, #fff 100%);
     border-left: 4px solid #4caf50;
     opacity: 0.8;
   }

   .step.completed span:last-child {
     color: #2e7d32;
   }
   ```

3. **아이콘 애니메이션**
   ```css
   .step-icon.pulse {
     animation: pulse 1.5s ease-in-out infinite;
   }

   @keyframes pulse {
     0%, 100% {
       transform: scale(1);
     }
     50% {
       transform: scale(1.2);
     }
   }
   ```

## 동작 방식

### 분석 시작부터 완료까지의 플로우

1. **사용자가 "레포팅 요청" 버튼 클릭**
   - 프론트엔드: `/invest_report` API 호출
   - 백엔드: `session_id` 생성 및 진행 상황 초기화

2. **백엔드에서 분석 시작**
   - CrewAI 또는 LangGraph 에이전트 실행
   - 각 단계마다 `update_progress()` 호출

3. **프론트엔드 폴링 시작**
   - 0.5초마다 `/progress/{session_id}` API 호출
   - 받은 진행 상황을 UI에 반영

4. **각 에이전트 단계 시각화**
   - 대기 중 (pending): 기본 흰색 배경
   - 진행 중 (in_progress): 파란색 그라데이션 + 펄스 애니메이션
   - 완료 (completed): 초록색 그라데이션 + 체크 마크

5. **분석 완료**
   - 백엔드: `complete_progress()` 호출
   - 프론트엔드: 폴링 중지, 최종 레포트 표시

## 4단계 에이전트 진행 상황

| 단계 | 아이콘 | 에이전트 | 설명 |
|------|--------|----------|------|
| 0 | 📊 | Financial Analyst | 재무 데이터 수집 및 분석 |
| 1 | 📈 | Market Analyst | 시장 동향 및 경쟁사 분석 |
| 2 | ⚠️ | Risk Analyst | 위험 요인 평가 |
| 3 | 💡 | Investment Advisor | 최종 투자 의견 작성 |

## 사용 예시

### 시각적 피드백 변화

```
[대기 중]
📊 재무 데이터 수집 및 분석
📈 시장 동향 및 경쟁사 분석
⚠️ 위험 요인 평가
💡 최종 투자 의견 작성

[1단계 진행 중]
📊 재무 데이터 수집 및 분석 중... (파란색, 펄스 애니메이션)
📈 시장 동향 및 경쟁사 분석
⚠️ 위험 요인 평가
💡 최종 투자 의견 작성

[1단계 완료, 2단계 진행 중]
📊 재무 분석 완료 ✓ (초록색)
📈 시장 동향 및 경쟁사 분석 중... (파란색, 펄스 애니메이션)
⚠️ 위험 요인 평가
💡 최종 투자 의견 작성

... (계속)

[모두 완료]
📊 재무 분석 완료 ✓ (초록색)
📈 시장 분석 완료 ✓ (초록색)
⚠️ 리스크 분석 완료 ✓ (초록색)
💡 투자 의견 작성 완료 ✓ (초록색)
```

## 테스트 방법

### 1. 백엔드 시작
```bash
cd backend
uv run python main.py
```

### 2. 프론트엔드 시작
```bash
cd frontend
npm start
```

### 3. 브라우저에서 테스트
1. `http://localhost:3000` 접속
2. AI Agent 선택 (LangGraph 또는 CrewAI)
3. 기업 선택 (예: 삼성전자)
4. "레포팅 요청" 버튼 클릭
5. 실시간 진행 상황 확인:
   - 각 단계가 순차적으로 활성화되는 모습
   - 활성 단계의 아이콘 펄스 애니메이션
   - 완료된 단계의 초록색 체크 마크

### 4. 진행 상황 API 직접 확인
```bash
# 분석 실행 중 session_id 확인 (백엔드 로그에서)
curl http://localhost:8000/progress/{session_id}
```

## 개선 사항

### 구현된 기능
- ✅ 메모리 기반 진행 상황 저장소
- ✅ 4단계 에이전트 진행 상황 추적
- ✅ 0.5초마다 자동 폴링
- ✅ 시각적 상태 표시 (대기/진행중/완료)
- ✅ 아이콘 펄스 애니메이션
- ✅ CrewAI와 LangGraph 모두 지원

### 향후 개선 가능 사항
- WebSocket을 통한 실시간 푸시 (폴링 대신)
- 진행률 퍼센트 표시 (0%, 25%, 50%, 75%, 100%)
- 각 단계별 소요 시간 표시
- 진행 상황 데이터베이스 저장 (메모리 대신)
- 오래된 진행 상황 자동 삭제 스케줄러

## 주의사항

1. **메모리 저장소**: 현재는 메모리에만 저장되므로 서버 재시작 시 진행 상황이 사라집니다.
2. **폴링 간격**: 0.5초마다 폴링하므로 많은 사용자가 동시에 사용 시 서버 부하가 있을 수 있습니다.
3. **세션 관리**: `clear_old_progress()` 함수를 주기적으로 호출하여 오래된 세션을 정리해야 합니다.

## 파일 변경 사항 요약

### 새로 생성된 파일
- `backend/progress_tracker.py` - 진행 상황 추적 모듈

### 수정된 파일
- `backend/main.py` - 진행 상황 API 및 session_id 추가
- `backend/langgraph_/langgraph_agent.py` - 단계별 진행 상황 업데이트
- `backend/crewai_/crewai_agent.py` - 단계별 진행 상황 업데이트
- `frontend/src/App.js` - 진행 상황 폴링 및 UI 표시
- `frontend/src/App.css` - 진행 상황 시각적 스타일

## 결론

이제 사용자는 AI 에이전트가 어느 단계를 실행 중인지 실시간으로 확인할 수 있어, 대기 시간 동안 불안감이 줄어들고 전체적인 사용자 경험이 크게 향상되었습니다. 🎉
