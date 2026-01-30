"""
CrewAI 기반 투자 레포팅 Agent 시스템
순차적으로 실행되는 4개의 에이전트: 재무 분석가 -> 시장 분석가 -> 리스크 분석가 -> 투자 어드바이저
"""
import os
import sys
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from typing import Dict, Any
from datetime import datetime

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


class InvestmentReportingCrew:
    """투자 레포팅을 위한 CrewAI 시스템"""

    def __init__(self, openai_api_key: str):
        """
        Args:
            openai_api_key: OpenAI API 키
        """
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.company_name = None
        self.ticker = None

    def create_financial_analyst(self) -> Agent:
        """재무 분석가 에이전트 생성"""
        return Agent(
            role="Financial Analyst",
            goal=f"{self.company_name}의 재무 상태와 주가 동향을 분석합니다.",
            backstory="""당신은 10년 이상의 경험을 가진 전문 재무 분석가입니다.
            기업의 재무제표, 주가 데이터, 거래량 등을 분석하여
            기업의 재무 건전성과 주가 추세를 파악하는 전문가입니다.""",
            tools=[get_stock_price_data, get_company_info, calculate_financial_ratios],
            verbose=True,
            allow_delegation=False
        )

    def create_market_analyst(self) -> Agent:
        """시장 분석가 에이전트 생성"""
        return Agent(
            role="Market Analyst",
            goal=f"{self.company_name}가 속한 시장과 산업 트렌드를 분석합니다.",
            backstory="""당신은 글로벌 시장 동향과 산업 트렌드를 분석하는 전문가입니다.
            거시경제 지표, 산업 동향, 경쟁사 분석을 통해
            기업이 직면한 시장 환경을 파악합니다.""",
            tools=[get_market_index, get_stock_price_data],
            verbose=True,
            allow_delegation=False
        )

    def create_risk_analyst(self) -> Agent:
        """리스크 분석가 에이전트 생성"""
        return Agent(
            role="Risk Analyst",
            goal=f"{self.company_name}의 투자 리스크 요인을 식별하고 평가합니다.",
            backstory="""당신은 리스크 관리 전문가로서
            시장 리스크, 유동성 리스크, 재무 리스크 등 다양한 리스크 요인을
            식별하고 정량화하는 전문가입니다.""",
            tools=[calculate_financial_ratios, get_stock_price_data, get_market_index],
            verbose=True,
            allow_delegation=False
        )

    def create_investment_advisor(self) -> Agent:
        """투자 어드바이저 에이전트 생성"""
        return Agent(
            role="Investment Advisor",
            goal=f"{self.company_name}에 대한 투자 의견과 목표가를 제시합니다.",
            backstory="""당신은 고객의 재산을 책임지는 투자 자문가입니다.
            재무 분석, 시장 분석, 리스크 분석 결과를 종합하여
            명확한 투자 의견(매수/보유/매도)과 목표주가를 제시합니다.""",
            tools=[get_stock_price_data, calculate_financial_ratios],
            verbose=True,
            allow_delegation=False
        )

    def create_financial_analysis_task(self, agent: Agent) -> Task:
        """재무 분석 태스크 생성"""
        return Task(
            description=f"""
            {self.company_name}(티커: {self.ticker})의 재무 분석을 수행하세요.

            다음 항목들을 분석해주세요:
            1. 기업 기본 정보 (회사명, 티커, 업종 등)
            2. 최근 주가 동향 (현재가, 거래량, 전일 대비 등)
            3. 재무 지표 (52주 최고/최저, 변동성, 수익률 등)

            도구를 활용하여 실제 데이터를 기반으로 분석하세요.
            분석 결과를 명확하고 구조화된 형태로 작성하세요.
            """,
            expected_output="""
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
            """,
            agent=agent
        )

    def create_market_analysis_task(self, agent: Agent, context: list) -> Task:
        """시장 분석 태스크 생성"""
        return Task(
            description=f"""
            {self.company_name}가 속한 시장 환경을 분석하세요.

            다음 항목들을 분석해주세요:
            1. KOSPI/KOSDAQ 시장 지수 동향
            2. 산업 전반의 트렌드
            3. 시장 심리 및 투자자 동향

            재무 분석 결과를 참고하여 시장 맥락에서 평가하세요.
            """,
            expected_output="""
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
            """,
            agent=agent,
            context=context  # 재무 분석 결과를 컨텍스트로 받음
        )

    def create_risk_assessment_task(self, agent: Agent, context: list) -> Task:
        """리스크 평가 태스크 생성"""
        return Task(
            description=f"""
            {self.company_name}의 투자 리스크를 평가하세요.

            다음 리스크 요인들을 분석해주세요:
            1. 주가 변동성 리스크
            2. 시장 리스크 (시장 지수 대비)
            3. 재무 리스크
            4. 산업/경쟁 리스크

            재무 분석과 시장 분석 결과를 종합하여 리스크를 평가하세요.
            각 리스크 요인에 대해 구체적인 근거를 제시하세요.
            """,
            expected_output="""
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
            """,
            agent=agent,
            context=context  # 재무 분석 + 시장 분석 결과를 컨텍스트로 받음
        )

    def create_investment_recommendation_task(self, agent: Agent, context: list) -> Task:
        """투자 추천 태스크 생성"""
        return Task(
            description=f"""
            {self.company_name}에 대한 최종 투자 의견을 제시하세요.

            다음 내용을 포함하세요:
            1. 투자 의견 (매수/보유/매도 중 하나)
            2. 목표주가 (현재가 대비 구체적인 가격 제시)
            3. 투자 포인트 (3가지 이상)
            4. 투자 시 주의사항

            앞선 재무 분석, 시장 분석, 리스크 평가 결과를 종합하여
            논리적이고 설득력 있는 투자 의견을 제시하세요.
            """,
            expected_output="""
            다음 형식을 정확히 지켜서 투자 추천 결과를 제공하세요:

            투자 의견: 매수
            목표 주가: 85000

            투자 포인트:
            - 메모리 반도체 시장 회복: DRAM 및 NAND 플래시 가격 상승으로 수익성 개선 예상
            - AI 시장 성장: HBM(고대역폭메모리) 수요 급증으로 프리미엄 제품 판매 확대
            - 파운드리 경쟁력 강화: 3nm 공정 기술 개선 및 주요 고객사 확보

            리스크 요인:
            - 글로벌 경기 둔화에 따른 수요 감소 우려
            - 중국 반도체 업체들의 추격
            - 환율 변동성 리스크

            결론:
            [종합 의견을 2-3문장으로 작성]
            """,
            agent=agent,
            context=context  # 모든 이전 분석 결과를 컨텍스트로 받음
        )

    def run_analysis(self, company_name: str) -> Dict[str, Any]:
        """
        투자 레포팅 분석을 실행합니다.

        Args:
            company_name: 분석할 회사명

        Returns:
            분석 결과 딕셔너리
        """
        self.company_name = company_name
        self.ticker = get_ticker_from_company_name(company_name)

        if not self.ticker:
            return {
                "error": f"Unknown company: {company_name}",
                "supported_companies": ["삼성전자", "SK하이닉스", "현대차", "NAVER", "카카오", "LG에너지솔루션"]
            }

        # 에이전트 생성
        financial_analyst = self.create_financial_analyst()
        market_analyst = self.create_market_analyst()
        risk_analyst = self.create_risk_analyst()
        investment_advisor = self.create_investment_advisor()

        # 태스크 생성 (순차적 실행을 위한 context 설정)
        task1 = self.create_financial_analysis_task(financial_analyst)
        task2 = self.create_market_analysis_task(market_analyst, context=[task1])
        task3 = self.create_risk_assessment_task(risk_analyst, context=[task1, task2])
        task4 = self.create_investment_recommendation_task(investment_advisor, context=[task1, task2, task3])

        # Crew 생성 (순차적 프로세스)
        crew = Crew(
            agents=[financial_analyst, market_analyst, risk_analyst, investment_advisor],
            tasks=[task1, task2, task3, task4],
            process=Process.sequential,  # 순차적 실행
            verbose=True
        )

        # 분석 실행
        print(f"\n{'='*60}")
        print(f"투자 레포팅 분석 시작: {company_name}")
        print(f"{'='*60}\n")

        result = crew.kickoff()

        # 실제 주가 데이터 수집
        try:
            from stock_analysis_tool import get_stock_price_data, get_company_info, calculate_financial_ratios

            # 주가 데이터 가져오기 (Tool 객체이므로 .func 사용)
            stock_data_text = get_stock_price_data.func(self.ticker, days=30)
            company_info_text = get_company_info.func(company_name)
            financial_ratios_text = calculate_financial_ratios.func(self.ticker)

            real_data = {
                "stock_price_data": stock_data_text,
                "company_info": company_info_text,
                "financial_ratios": financial_ratios_text
            }
        except Exception as e:
            print(f"실제 데이터 수집 오류: {str(e)}")
            real_data = {}

        return {
            "company": company_name,
            "ticker": self.ticker,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "analysis_result": str(result),
            "real_data": real_data,
            "status": "success"
        }


# 테스트용 함수
if __name__ == "__main__":
    # 테스트 실행 예제
    # 실제 사용 시에는 환경변수나 .env 파일에서 API 키를 로드하세요
    import sys

    if len(sys.argv) < 2:
        print("Usage: python crewai_agent.py <company_name>")
        print("Example: python crewai_agent.py 삼성전자")
        sys.exit(1)

    company = sys.argv[1]

    # API 키는 환경변수에서 로드
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    crew_system = InvestmentReportingCrew(api_key)
    result = crew_system.run_analysis(company)

    print("\n" + "="*60)
    print("분석 완료!")
    print("="*60)
    print(result)
