"""
LangGraph 기반 투자 레포팅 Agent 시스템
순차적으로 실행되는 4개의 에이전트: 재무 분석가 -> 시장 분석가 -> 리스크 분석가 -> 투자 어드바이저
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, TypedDict, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 현재 파일의 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from stock_analysis_tool import (
    get_stock_price_data,
    get_company_info,
    calculate_financial_ratios,
    get_market_index,
    get_ticker_from_company_name
)


class InvestmentReportingGraph:
    """투자 레포팅을 위한 LangGraph 시스템"""

    def __init__(self, openai_api_key: str):
        """
        Args:
            openai_api_key: OpenAI API 키
        """
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    def _call_agent(self, agent_name: str, system_prompt: str, user_prompt: str) -> str:
        """
        에이전트를 호출하고 결과를 반환합니다.

        Args:
            agent_name: 에이전트 이름
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트

        Returns:
            에이전트 응답
        """
        print(f"\n{'='*60}")
        print(f"[{agent_name}] 분석 시작")
        print(f"{'='*60}")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        result = response.content

        print(f"[{agent_name}] 분석 완료 (길이: {len(result)} 문자)")
        print(f"{'='*60}\n")

        return result

    def _financial_analyst(self, company_name: str, ticker: str) -> str:
        """재무 분석가 에이전트"""

        # 실제 데이터 수집
        print(f"[재무 분석가] {company_name}의 실제 데이터 수집 중...")
        stock_data = get_stock_price_data.invoke({"ticker": ticker, "days": 30})
        company_info = get_company_info.invoke({"company_name": company_name})
        financial_ratios = calculate_financial_ratios.invoke({"ticker": ticker})

        print(f"[재무 분석가] 데이터 수집 완료")

        system_prompt = """당신은 10년 이상의 경험을 가진 전문 재무 분석가입니다.
실제 데이터를 기반으로 기업의 재무 상태를 객관적으로 분석하세요."""

        user_prompt = f"""
{company_name}(티커: {ticker})의 재무 분석을 수행하세요.

수집된 실제 데이터:

{company_info}

{stock_data}

{financial_ratios}

다음 형식으로 재무 분석 결과를 제공하세요:

# 재무 분석 리포트

## 기업 개요
- 회사명, 티커, 시장, 업종

## 주가 분석
- 현재가 및 최근 동향
- 거래량 분석
- 주가 변동성

## 재무 지표
- 52주 최고/최저가
- 수익률 (1개월, 3개월, 6개월)
- 주요 재무 비율
"""

        return self._call_agent("재무 분석가", system_prompt, user_prompt)

    def _market_analyst(self, company_name: str, financial_analysis: str) -> str:
        """시장 분석가 에이전트"""

        # 시장 데이터 수집
        print(f"[시장 분석가] 시장 지수 데이터 수집 중...")
        market_data = get_market_index.invoke({"days": 30})
        print(f"[시장 분석가] 데이터 수집 완료")

        system_prompt = """당신은 글로벌 시장 동향과 산업 트렌드를 분석하는 전문가입니다.
실제 시장 데이터를 바탕으로 객관적인 분석을 제공하세요."""

        user_prompt = f"""
{company_name}가 속한 시장 환경을 분석하세요.

재무 분석 결과:
{financial_analysis}

시장 지수 데이터:
{market_data}

다음 형식으로 시장 분석 결과를 제공하세요:

# 시장 분석 리포트

## 시장 지수 분석
- KOSPI 동향
- 시장 전반의 분위기

## 산업 분석
- 해당 산업의 현황
- 산업 내 위치

## 투자 환경
- 거시경제 영향
- 시장 기회 요인
"""

        return self._call_agent("시장 분석가", system_prompt, user_prompt)

    def _risk_analyst(self, company_name: str, ticker: str, financial_analysis: str, market_analysis: str) -> str:
        """리스크 분석가 에이전트"""

        # 리스크 데이터 수집
        print(f"[리스크 분석가] 리스크 데이터 수집 중...")
        volatility_data = calculate_financial_ratios.invoke({"ticker": ticker})
        print(f"[리스크 분석가] 데이터 수집 완료")

        system_prompt = """당신은 리스크 관리 전문가입니다.
실제 데이터를 바탕으로 투자 리스크를 객관적으로 평가하세요."""

        user_prompt = f"""
{company_name}의 투자 리스크를 평가하세요.

재무 분석 결과:
{financial_analysis}

시장 분석 결과:
{market_analysis}

변동성 데이터:
{volatility_data}

다음 형식으로 리스크 평가 결과를 제공하세요:

# 리스크 평가 리포트

## 주요 리스크 요인
1. [리스크 요인 1]
   - 설명
   - 영향도

2. [리스크 요인 2]
   - 설명
   - 영향도

3. [리스크 요인 3]
   - 설명
   - 영향도

## 종합 리스크 평가
- 전체적인 리스크 수준 (높음/중간/낮음)
- 주의사항
"""

        return self._call_agent("리스크 분석가", system_prompt, user_prompt)

    def _investment_advisor(self, company_name: str, ticker: str,
                           financial_analysis: str, market_analysis: str, risk_assessment: str) -> str:
        """투자 어드바이저 에이전트"""

        # 최신 주가 데이터
        print(f"[투자 어드바이저] 최신 주가 데이터 확인 중...")
        current_price_data = get_stock_price_data.invoke({"ticker": ticker, "days": 5})
        print(f"[투자 어드바이저] 데이터 확인 완료")

        system_prompt = """당신은 고객의 재산을 책임지는 투자 자문가입니다.
모든 분석 결과를 종합하여 실행 가능한 투자 의견을 제시하세요."""

        user_prompt = f"""
{company_name}에 대한 최종 투자 의견을 제시하세요.

재무 분석 결과:
{financial_analysis}

시장 분석 결과:
{market_analysis}

리스크 평가 결과:
{risk_assessment}

현재 주가 정보:
{current_price_data}

다음 형식을 정확히 지켜서 투자 추천 결과를 제공하세요:

투자 의견: [매수/보유/매도 중 하나 선택]
목표 주가: [구체적인 숫자만, 단위 없이]

투자 포인트:
- [투자 포인트 1]
- [투자 포인트 2]
- [투자 포인트 3]

리스크 요인:
- [리스크 1]
- [리스크 2]
- [리스크 3]

결론:
[2-3문장으로 종합 의견 작성]
"""

        return self._call_agent("투자 어드바이저", system_prompt, user_prompt)

    def run_analysis(self, company_name: str, session_id: str = None) -> Dict[str, Any]:
        """
        투자 레포팅 분석을 실행합니다.

        Args:
            company_name: 분석할 회사명
            session_id: 진행 상황 추적을 위한 세션 ID (선택)

        Returns:
            분석 결과 딕셔너리
        """
        # progress_tracker 임포트 (선택적)
        if session_id:
            try:
                from progress_tracker import update_progress
            except ImportError:
                update_progress = None
        else:
            update_progress = None

        ticker = get_ticker_from_company_name(company_name)

        if not ticker:
            return {
                "error": f"Unknown company: {company_name}",
                "supported_companies": ["삼성전자", "SK하이닉스", "현대차", "NAVER", "카카오", "LG에너지솔루션"]
            }

        print(f"\n{'='*60}")
        print(f"LangGraph 투자 레포팅 분석 시작: {company_name}")
        print(f"{'='*60}\n")

        try:
            # 순차적으로 각 에이전트 실행
            print("[진행 상황] 1/4 단계: 재무 분석")
            if update_progress:
                update_progress(session_id, 0, "in_progress", "재무 데이터 수집 및 분석 중...")
            financial_analysis = self._financial_analyst(company_name, ticker)
            if update_progress:
                update_progress(session_id, 0, "completed", "재무 분석 완료")

            print("[진행 상황] 2/4 단계: 시장 분석")
            if update_progress:
                update_progress(session_id, 1, "in_progress", "시장 동향 및 경쟁사 분석 중...")
            market_analysis = self._market_analyst(company_name, financial_analysis)
            if update_progress:
                update_progress(session_id, 1, "completed", "시장 분석 완료")

            print("[진행 상황] 3/4 단계: 리스크 분석")
            if update_progress:
                update_progress(session_id, 2, "in_progress", "위험 요인 평가 중...")
            risk_assessment = self._risk_analyst(company_name, ticker, financial_analysis, market_analysis)
            if update_progress:
                update_progress(session_id, 2, "completed", "리스크 분석 완료")

            print("[진행 상황] 4/4 단계: 투자 의견 작성")
            if update_progress:
                update_progress(session_id, 3, "in_progress", "최종 투자 의견 작성 중...")
            investment_recommendation = self._investment_advisor(
                company_name, ticker, financial_analysis, market_analysis, risk_assessment
            )
            if update_progress:
                update_progress(session_id, 3, "completed", "투자 의견 작성 완료")

            # 실제 주가 데이터 수집
            stock_data_text = get_stock_price_data.invoke({"ticker": ticker, "days": 30})
            company_info_text = get_company_info.invoke({"company_name": company_name})
            financial_ratios_text = calculate_financial_ratios.invoke({"ticker": ticker})

            real_data = {
                "stock_price_data": stock_data_text,
                "company_info": company_info_text,
                "financial_ratios": financial_ratios_text
            }

            print(f"\n{'='*60}")
            print(f"[완료] 모든 분석이 완료되었습니다!")
            print(f"{'='*60}\n")

            return {
                "company": company_name,
                "ticker": ticker,
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_result": investment_recommendation,
                "financial_analysis": financial_analysis,
                "market_analysis": market_analysis,
                "risk_assessment": risk_assessment,
                "real_data": real_data,
                "status": "success"
            }

        except Exception as e:
            print(f"\n[오류] 분석 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "error": str(e),
                "status": "failed"
            }


# 테스트용 함수
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python langgraph_agent.py <company_name>")
        print("Example: python langgraph_agent.py 삼성전자")
        sys.exit(1)

    company = sys.argv[1]

    # API 키는 환경변수에서 로드
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    graph_system = InvestmentReportingGraph(api_key)
    result = graph_system.run_analysis(company)

    print("\n" + "="*60)
    print("분석 완료!")
    print("="*60)

    if "error" in result:
        print(f"오류: {result['error']}")
    else:
        print(f"회사: {result['company']}")
        print(f"티커: {result['ticker']}")
        print(f"\n투자 의견:\n{result['analysis_result'][:300]}...")
