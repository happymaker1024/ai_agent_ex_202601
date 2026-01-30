"""
CrewAI 에이전트 테스트 스크립트
"""
import sys
import os
from pathlib import Path

# crewai_ 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent / 'crewai_'))

from dotenv import load_dotenv
load_dotenv()

def test_crewai_agent():
    """CrewAI 에이전트를 테스트합니다."""
    from crewai_agent import InvestmentReportingCrew

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found")
        return False

    print("[OK] OPENAI_API_KEY found")
    print(f"API Key: {api_key[:20]}...")

    try:
        print("\n" + "="*60)
        print("CrewAI Agent Test Started")
        print("="*60 + "\n")

        # CrewAI 시스템 초기화
        crew_system = InvestmentReportingCrew(api_key)
        print("[OK] CrewAI system initialized")

        # Samsung Electronics analysis
        company = "Samsung Electronics (005930)"
        print(f"\nAnalyzing: {company}\n")

        result = crew_system.run_analysis("삼성전자")

        print("\n" + "="*60)
        print("Analysis Result:")
        print("="*60)
        print(f"Company: {result.get('company')}")
        print(f"Ticker: {result.get('ticker')}")
        print(f"Date: {result.get('report_date')}")
        print(f"Status: {result.get('status')}")

        if result.get('analysis_result'):
            print("\nInvestment Recommendation:")
            print(result['analysis_result'][:500] + "...")

        print("\n[OK] CrewAI agent test successful!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crewai_agent()
    sys.exit(0 if success else 1)
