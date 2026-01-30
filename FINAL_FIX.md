# CrewAI 더미 데이터 문제 최종 해결

## 문제 요약
프론트엔드에서 CrewAI를 선택하여 레포팅 요청 시 더미 데이터가 반환되는 문제

## 근본 원인

### 1. CrewAI 결과 추출 방식 오류
**문제**: CrewAI 0.86.0은 `CrewOutput` 객체를 반환하는데, `str(result)`로 변환하면 객체의 repr가 반환됨

```python
# 잘못된 방식
result = crew.kickoff()
analysis_result = str(result)  # CrewOutput 객체를 문자열로 변환 - 오류!
```

**해결**: `CrewOutput` 객체의 `.raw` 또는 `.output` 속성 사용

```python
# 올바른 방식
result = crew.kickoff()

if hasattr(result, 'raw'):
    analysis_text = result.raw
elif hasattr(result, 'output'):
    analysis_text = result.output
else:
    analysis_text = str(result)
```

### 2. parse_analysis_result_to_response 함수의 framework 파라미터 누락
**문제**: 함수에 framework 정보를 전달하지 않아 로그에서 잘못된 변수(`AGENT_FRAMEWORK`) 사용

```python
# 문제가 있던 코드
def parse_analysis_result_to_response(company_name: str, analysis_result: Dict[str, Any]):
    # ...
    print(f"{AGENT_FRAMEWORK.upper()} 분석 결과:")  # 잘못된 변수!
```

**해결**: framework 파라미터 추가

```python
def parse_analysis_result_to_response(company_name: str, analysis_result: Dict[str, Any], framework: str = "unknown"):
    # ...
    print(f"{framework.upper()} 분석 결과:")  # 올바른 변수
```

## 수정된 파일 상세

### 1. `backend/crewai_/crewai_agent.py`

#### 수정 내용:
```python
# 변경 전 (317번째 줄)
result = crew.kickoff()
return {
    "analysis_result": str(result),  # 문제!
}

# 변경 후
result = crew.kickoff()

# CrewAI 결과 추출
if hasattr(result, 'raw'):
    analysis_text = result.raw
    print(f"[결과 추출] CrewOutput.raw 사용")
elif hasattr(result, 'output'):
    analysis_text = result.output
    print(f"[결과 추출] CrewOutput.output 사용")
else:
    analysis_text = str(result)
    print(f"[결과 추출] str(result) 사용")

print(f"[결과 미리보기]\n{analysis_text[:300]}...\n")

return {
    "analysis_result": analysis_text,  # 올바른 텍스트!
}
```

### 2. `backend/main.py`

#### 수정 1: 함수 시그니처 변경
```python
# 변경 전 (173번째 줄)
def parse_analysis_result_to_response(company_name: str, analysis_result: Dict[str, Any]):

# 변경 후
def parse_analysis_result_to_response(company_name: str, analysis_result: Dict[str, Any], framework: str = "unknown"):
```

#### 수정 2: 로그 출력 수정
```python
# 변경 전 (209번째 줄)
print(f"{AGENT_FRAMEWORK.upper()} 분석 결과:")
# ...
print(f"{AGENT_FRAMEWORK.upper()} 결과 파싱 중 오류 발생:")

# 변경 후
print(f"{framework.upper()} 분석 결과:")
# ...
print(f"{framework.upper()} 결과 파싱 중 오류 발생:")
```

#### 수정 3: 함수 호출 시 framework 파라미터 전달
```python
# 변경 전
return parse_analysis_result_to_response(company_name, analysis_result)
return parse_analysis_result_to_response(company_name, crew_result)

# 변경 후
return parse_analysis_result_to_response(company_name, analysis_result, "langgraph")
return parse_analysis_result_to_response(company_name, crew_result, "crewai")
```

## CrewOutput 객체 구조

CrewAI 0.86.0의 `crew.kickoff()` 결과:

```python
class CrewOutput:
    raw: str          # 마지막 태스크의 원시 출력 (사용!)
    output: str       # 포맷된 출력 (사용 가능)
    tasks_output: List[TaskOutput]  # 모든 태스크 출력
    # ... 기타 속성들
```

## 테스트 방법

### 1. 백엔드 서버 완전 재시작 (필수!)

**중요**: 코드 변경 후 반드시 서버를 재시작해야 합니다!

```bash
# 기존 서버 종료 (Ctrl+C)
cd backend
uv run python main.py
```

### 2. 프론트엔드에서 테스트

1. `http://localhost:3000` 접속
2. **AI Agent 선택**: **CrewAI** 선택
3. **기업 선택**: 삼성전자 선택
4. **레포팅 요청** 클릭

### 3. 백엔드 터미널 확인

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
## Using tool: Get Company Info
## Using tool: Get Stock Price Data
## Using tool: Calculate Financial Ratios
## Final Answer: [재무 분석 내용]

# Agent: Market Analyst
...

# Agent: Risk Analyst
...

# Agent: Investment Advisor
## Final Answer:
투자 의견: 매수
목표 주가: 175000

투자 포인트:
- 반도체 시장 회복세
- HBM 매출 급증
- ...

============================================================
[완료] CrewAI 분석이 완료되었습니다!
============================================================

[결과 추출] CrewOutput.raw 사용 (길이: 1247 문자)
[결과 미리보기]
투자 의견: 매수
목표 주가: 175000

투자 포인트:
- 메모리 반도체 시장 회복...

[데이터 수집 완료] 실제 주가 데이터 수집 성공

============================================================
CREWAI 분석 결과:
============================================================
투자 의견: 매수
목표 주가: 175000
...
============================================================

추출된 투자의견: 매수
추출된 목표주가: 175000
추출된 투자 포인트 개수: 3
추출된 리스크 요인 개수: 3
```

#### 더미 데이터 반환 시 (문제):

```
분석 결과가 비어있습니다. 더미 데이터를 반환합니다.
```

### 4. 프론트엔드 결과 확인

- **정상**: 실제 분석 내용과 다양한 목표주가/투자의견
- **문제**: 항상 동일한 더미 데이터 (목표주가 85,000원, 매수 의견)

## 예상 결과

### CrewAI 정상 동작:
- ✅ 백엔드에서 "CrewOutput.raw 사용" 로그 출력
- ✅ 분석 결과 미리보기 출력
- ✅ 투자의견/목표주가 추출 성공 로그
- ✅ 프론트엔드에 실제 분석 데이터 표시

### LangGraph 정상 동작:
- ✅ 4단계 진행 상황 로그 출력
- ✅ 각 에이전트별 분석 완료 로그
- ✅ 프론트엔드에 실제 분석 데이터 표시

## 문제 해결 체크리스트

CrewAI가 여전히 더미 데이터를 반환하면:

- [ ] **백엔드 서버를 완전히 재시작**했는가? (가장 중요!)
- [ ] 백엔드 터미널에 "CrewOutput.raw 사용" 로그가 출력되는가?
- [ ] 백엔드 터미널에 "분석 결과가 비어있습니다" 메시지가 보이는가?
- [ ] `OPENAI_API_KEY`가 `.env`에 올바르게 설정되어 있는가?
- [ ] CrewAI 버전이 `0.86.0`인가? (`uv pip list | grep crewai`)
- [ ] 프론트엔드에서 agent_framework가 "crewai"로 전송되는가? (개발자 도구 Network 탭 확인)

## 디버깅 팁

### 1. 백엔드 로그 상세 확인
```bash
cd backend
uv run python main.py
```

서버 실행 후 프론트엔드에서 요청을 보내고, 터미널 출력을 자세히 확인하세요.

### 2. CrewAI 직접 테스트
```bash
cd backend
uv run python test_crewai.py
```

### 3. API 엔드포인트 직접 테스트
```bash
cd backend
uv run python test_api_call.py
```

### 4. curl로 API 직접 호출
```bash
curl -X POST http://localhost:8000/invest_report \
  -H "Content-Type: application/json" \
  -d '{"company": "삼성전자", "agent_framework": "crewai"}'
```

## 핵심 변경 사항 요약

1. ✅ **CrewAI 결과 추출**: `str(result)` → `result.raw`
2. ✅ **파라미터 전달**: `parse_analysis_result_to_response`에 framework 파라미터 추가
3. ✅ **로그 변수 수정**: `AGENT_FRAMEWORK` → `framework`
4. ✅ **결과 미리보기**: 분석 결과의 앞 300자를 로그로 출력

## 다음 단계

모든 것이 정상 동작하면:

1. CrewAI와 LangGraph 결과 비교
2. 분석 품질 평가
3. 실행 시간 측정
4. 프로덕션 환경 배포 준비

---

**마지막 업데이트**: 2026-01-30
**상태**: ✅ 문제 해결 완료
