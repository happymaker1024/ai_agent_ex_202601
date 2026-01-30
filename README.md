# 국내 상장사 투자 레포팅 Agent

React 프론트엔드와 FastAPI 백엔드를 사용한 투자 레포팅 시스템입니다.

## 프로젝트 구조

```
ai_agent_ex/
├── frontend/          # React 프론트엔드
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
│
├── backend/           # FastAPI 백엔드
│   ├── main.py
│   ├── pyproject.toml
│   ├── .python-version
│   └── requirements.txt
│
└── README.md
```

## 기능

- 국내 주요 상장사 선택
- 투자 레포트 자동 생성
- 주가 정보, 재무 정보, 투자 포인트, 리스크 요인 제공
- 목표주가 및 투자의견 제시

## 필수 요구사항

- **uv**: Python 패키지 관리자 (백엔드)
  - 설치: `pip install uv` 또는 [공식 문서](https://github.com/astral-sh/uv) 참고
- **Node.js**: 18.x 이상 (프론트엔드)
- **Python**: 3.10 이상

## 빠른 시작

```bash
# 1. 백엔드 설정 및 실행
cd backend
uv venv                         # 가상환경 생성
uv pip install -r requirements.txt  # 의존성 설치
uv run python main.py           # 서버 실행

# 2. 새 터미널에서 프론트엔드 실행
cd frontend
npm install                     # 의존성 설치
npm start                       # 개발 서버 실행
```

브라우저에서 `http://localhost:3000` 접속

## 설치 방법

### 백엔드 설치 (uv 사용)

1. backend 디렉토리로 이동:
```bash
cd backend
```

2. uv를 사용하여 가상환경 생성 및 패키지 설치:
```bash
uv venv
```

3. 가상환경 활성화:
- Windows:
```bash
.venv\Scripts\activate
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

4. 의존성 설치:
```bash
uv pip install -r requirements.txt
```

### 프론트엔드 설치

1. frontend 디렉토리로 이동:
```bash
cd frontend
```

2. npm 패키지 설치:
```bash
npm install
```

## 실행 방법

### 백엔드 실행

1. backend 디렉토리로 이동 및 가상환경 활성화:
```bash
cd backend
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2. 서버 실행:
```bash
python main.py
```

또는 uvicorn으로 직접 실행:
```bash
uv run uvicorn main:app --reload
```

또는 가상환경 활성화 없이 실행:
```bash
uv run python main.py
```

백엔드 서버는 `http://localhost:8000`에서 실행됩니다.

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 프론트엔드 실행

1. frontend 디렉토리에서 실행:
```bash
cd frontend
npm start
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

## API 엔드포인트

- `GET /` - API 정보 및 사용 가능한 엔드포인트 목록
- `POST /invest_report` - 투자 레포트 요청
  - Request Body: `{ "company": "삼성전자" }`
  - Response: 투자 레포트 JSON 데이터

## 지원 종목

CrewAI 및 FinanceDataReader로 실시간 분석 가능한 종목:
- 삼성전자
- SK하이닉스
- 현대차
- NAVER
- 카카오
- LG에너지솔루션

## 에이전트 프레임워크 선택

이 프로젝트는 **CrewAI**와 **LangGraph** 두 가지 에이전트 프레임워크를 지원합니다.

### 프레임워크 전환 방법

`.env` 파일에서 `AGENT_FRAMEWORK` 환경변수를 설정하여 프레임워크를 선택할 수 있습니다:

```bash
# CrewAI 사용 (기본값)
AGENT_FRAMEWORK=crewai

# 또는 LangGraph 사용
AGENT_FRAMEWORK=langgraph
```

환경변수를 설정하지 않으면 기본값으로 CrewAI가 사용됩니다.

## AI 에이전트 설정 (선택사항)

CrewAI 또는 LangGraph를 활용한 실제 AI 분석을 원하시면:

1. OpenAI API 키 발급: https://platform.openai.com/api-keys

2. backend 디렉토리에 `.env` 파일 생성:
```bash
cd backend
cp .env.example .env
```

3. `.env` 파일에 API 키와 프레임워크 설정:
```
OPENAI_API_KEY=your-actual-api-key-here
AGENT_FRAMEWORK=crewai  # 또는 langgraph
```

4. 의존성 재설치:
```bash
uv pip install -r requirements.txt
```

**주의:** OpenAI API 키가 없으면 더미 데이터로 작동합니다.

## Agent 시스템 구조

### CrewAI vs LangGraph

두 프레임워크 모두 동일한 4개 에이전트 구조를 사용합니다:

- **CrewAI**: Task와 Agent 기반의 협업 구조
- **LangGraph**: StateGraph 기반의 상태 관리 구조

백엔드는 다음 4개의 에이전트가 순차적으로 실행됩니다:

### 에이전트 실행 흐름

```
사용자 요청 (예: "삼성전자")
    ↓
1. 재무 분석가 (Financial Analyst)
   📊 FinanceDataReader로 주가, 재무 데이터 수집
   - 현재가, 거래량, 52주 최고/최저
   - 수익률 (1개월, 3개월, 6개월)
   - 변동성 분석
    ↓
2. 시장 분석가 (Market Analyst)
   📈 시장 환경 및 산업 분석
   - KOSPI/KOSDAQ 지수 동향
   - 산업 트렌드 분석
   - 경쟁사 비교
    ↓
3. 리스크 분석가 (Risk Analyst)
   ⚠️  위험 요인 평가
   - 주가 변동성 리스크
   - 시장 리스크
   - 재무/산업 리스크
    ↓
4. 투자 자문가 (Investment Advisor)
   💡 최종 투자 의견 생성
   - 투자 의견 (매수/보유/매도)
   - 목표주가 제시
   - 투자 포인트 3가지
   - 주요 리스크 요인 정리
    ↓
프론트엔드로 결과 전송
```

### 데이터 흐름

1. **프론트엔드**: 사용자가 기업 선택 → 백엔드에 POST 요청
2. **백엔드**:
   - OpenAI API 키가 있으면: 선택된 프레임워크(CrewAI/LangGraph) 에이전트 실행
   - OpenAI API 키가 없으면: 더미 데이터 반환
3. **AI 에이전트 (CrewAI 또는 LangGraph)**:
   - FinanceDataReader로 실시간 데이터 수집
   - 4개 에이전트가 순차적으로 분석 수행
   - 각 에이전트는 이전 에이전트의 결과를 context로 받음
4. **결과 파싱**:
   - LLM이 생성한 텍스트에서 투자 포인트, 리스크, 목표주가 추출
   - JSON 형식으로 변환
5. **프론트엔드**: 분석 결과를 시각적으로 표시

### 실행 시간

- AI 에이전트 분석 (CrewAI/LangGraph): 약 30초~1분 소요
- 더미 데이터 모드: 즉시 응답

## 프로젝트 구조

```
backend/
├── crewai_/              # CrewAI 구현
│   ├── crewai_agent.py
│   └── stock_analysis_tool.py
├── langgraph_/           # LangGraph 구현
│   ├── langgraph_agent.py
│   └── stock_analysis_tool.py
├── main.py               # FastAPI 서버 (프레임워크 전환 로직 포함)
└── requirements.txt
```

## 향후 개발 계획

- ✅ CrewAI 및 실시간 데이터 분석 연동 완료
- ✅ LangGraph 프레임워크 추가 및 전환 기능 구현
- 추가 종목 데이터 확장
- 차트 및 그래프 시각화
- PDF 레포트 다운로드 기능
- LLM 응답 파싱 및 구조화
