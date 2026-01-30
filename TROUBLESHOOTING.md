# 트러블슈팅 가이드

## 문제: 프론트엔드에서 더미 데이터만 표시됨

### 원인 진단

1. **백엔드 서버가 실행되지 않음**
2. **백엔드 서버가 `.env` 변경사항을 반영하지 않음**
3. **OpenAI API 키가 제대로 설정되지 않음**
4. **LangGraph 의존성이 설치되지 않음**

---

## 해결 방법

### 1단계: 환경변수 확인

`backend/.env` 파일이 존재하고 올바르게 설정되어 있는지 확인:

```bash
cd backend
cat .env
```

다음과 같이 설정되어 있어야 합니다:

```
OPENAI_API_KEY=sk-proj-...  (실제 API 키)
AGENT_FRAMEWORK=langgraph   (또는 crewai)
```

### 2단계: 의존성 설치 확인

LangGraph 패키지가 설치되어 있는지 확인:

```bash
cd backend
uv pip list | grep langgraph
```

만약 설치되지 않았다면:

```bash
cd backend
uv pip install -r requirements.txt
```

### 3단계: 백엔드 서버 재시작

**중요**: `.env` 파일을 수정한 후에는 **반드시 서버를 재시작**해야 합니다!

#### 방법 1: 터미널에서 재시작

1. 현재 실행 중인 백엔드 서버를 중지 (`Ctrl+C`)
2. 다시 시작:

```bash
cd backend
uv run python main.py
```

또는

```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 방법 2: 프로세스 강제 종료 후 재시작 (Windows)

```bash
# 포트 8000을 사용하는 프로세스 찾기
netstat -ano | findstr :8000

# PID 확인 후 종료 (예: PID가 12345인 경우)
taskkill /PID 12345 /F

# 서버 재시작
cd backend
uv run python main.py
```

### 4단계: 백엔드 상태 확인

서버가 제대로 실행되면 다음 명령으로 확인:

```bash
curl http://localhost:8000/
```

출력 예시:
```json
{
  "message": "투자 레포팅 Agent API",
  "version": "3.0.0",
  "agent_framework": "langgraph",  // ← 여기를 확인!
  "mode": "LANGGRAPH-powered",
  "endpoints": {
    "home": "/",
    "invest_report": "/invest_report"
  }
}
```

**`agent_framework`가 `langgraph`로 표시되어야 합니다!**

### 5단계: 프론트엔드 테스트

1. 브라우저에서 `http://localhost:3000` 접속
2. 기업 선택 (예: 삼성전자)
3. "레포팅 요청" 버튼 클릭
4. 백엔드 콘솔에서 다음 메시지 확인:

```
============================================================
LangGraph 분석 시작: 삼성전자
============================================================

✓ 재무 분석 완료
✓ 시장 분석 완료
✓ 리스크 분석 완료
✓ 투자 의견 작성 완료
```

---

## 추가 디버깅

### LangGraph 직접 테스트

```bash
cd backend
uv run python test_langgraph.py
```

성공 시 출력:
```
[OK] OPENAI_API_KEY found
============================================================
LangGraph Agent Test Started
============================================================

[OK] LangGraph system initialized
Analyzing: Samsung Electronics (005930)
...
[OK] LangGraph agent test successful!
```

### 로그 확인

백엔드 서버 실행 시 콘솔 출력을 자세히 확인:

- `"LangGraph 분석 시작"` 메시지가 보이는지
- 오류 메시지가 있는지
- API 키 관련 오류가 있는지

---

## 자주 발생하는 오류

### 1. `ModuleNotFoundError: No module named 'langgraph'`

**해결**:
```bash
cd backend
uv pip install langgraph>=0.2.0 langchain-core>=0.3.0
```

### 2. `OpenAI API error: Incorrect API key provided`

**해결**: `.env` 파일의 `OPENAI_API_KEY`가 올바른지 확인
- https://platform.openai.com/api-keys 에서 키 확인

### 3. `CORS error` (프론트엔드에서)

**확인**:
- 백엔드가 `http://localhost:8000`에서 실행 중인지
- 프론트엔드가 `http://localhost:3000`에서 실행 중인지

### 4. 여전히 더미 데이터가 표시됨

**체크리스트**:
- [ ] `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는가?
- [ ] `.env` 파일에 `AGENT_FRAMEWORK=langgraph`가 설정되어 있는가?
- [ ] 백엔드 서버를 재시작했는가?
- [ ] `curl http://localhost:8000/`에서 `agent_framework: langgraph`가 표시되는가?
- [ ] 백엔드 콘솔에서 "LangGraph 분석 시작" 메시지가 보이는가?

---

## 완전 초기화 방법

모든 것을 처음부터 다시 시작:

```bash
# 1. 백엔드 서버 중지 (Ctrl+C)

# 2. 의존성 재설치
cd backend
uv pip install -r requirements.txt

# 3. .env 파일 확인/수정
# OPENAI_API_KEY=sk-proj-...
# AGENT_FRAMEWORK=langgraph

# 4. 백엔드 재시작
uv run python main.py

# 5. 새 터미널에서 프론트엔드 실행
cd frontend
npm start
```

---

## 도움이 필요하면

1. 백엔드 콘솔의 전체 오류 메시지 복사
2. `curl http://localhost:8000/` 출력 확인
3. `.env` 파일 내용 확인 (API 키는 제외)
