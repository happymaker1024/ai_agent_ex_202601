"""
API 엔드포인트 테스트 - CrewAI와 LangGraph 모두 테스트
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# main.py의 경로를 추가
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crewai_'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langgraph_'))

def test_crewai_through_main():
    """main.py를 통한 CrewAI 호출 테스트"""
    from main import get_invest_report, InvestReportRequest
    import asyncio

    print("="*60)
    print("CrewAI API 호출 테스트")
    print("="*60)

    request = InvestReportRequest(
        company="삼성전자",
        agent_framework="crewai"
    )

    try:
        result = asyncio.run(get_invest_report(request))
        print(f"\n결과 타입: {type(result)}")
        print(f"회사명: {result.company}")
        print(f"추천: {result.recommendation}")
        print(f"목표가: {result.target_price}")
        print(f"투자 포인트 개수: {len(result.investment_points)}")
        print(f"리스크 요인 개수: {len(result.risk_factors)}")

        # 더미 데이터인지 확인
        if result.target_price == 85000 and result.recommendation == "매수":
            print("\n⚠️  경고: 더미 데이터가 반환되었습니다!")
            return False
        else:
            print("\n✅ 실제 분석 데이터가 반환되었습니다!")
            return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_langgraph_through_main():
    """main.py를 통한 LangGraph 호출 테스트"""
    from main import get_invest_report, InvestReportRequest
    import asyncio

    print("\n" + "="*60)
    print("LangGraph API 호출 테스트")
    print("="*60)

    request = InvestReportRequest(
        company="삼성전자",
        agent_framework="langgraph"
    )

    try:
        result = asyncio.run(get_invest_report(request))
        print(f"\n결과 타입: {type(result)}")
        print(f"회사명: {result.company}")
        print(f"추천: {result.recommendation}")
        print(f"목표가: {result.target_price}")
        print(f"투자 포인트 개수: {len(result.investment_points)}")
        print(f"리스크 요인 개수: {len(result.risk_factors)}")

        # 더미 데이터인지 확인
        if result.target_price == 85000 and result.recommendation == "매수":
            print("\n⚠️  경고: 더미 데이터가 반환되었습니다!")
            return False
        else:
            print("\n✅ 실제 분석 데이터가 반환되었습니다!")
            return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        sys.exit(1)

    print(f"✓ OPENAI_API_KEY 확인됨: {api_key[:20]}...\n")

    # CrewAI 테스트
    crewai_success = test_crewai_through_main()

    # LangGraph 테스트
    langgraph_success = test_langgraph_through_main()

    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"CrewAI: {'✅ 성공' if crewai_success else '❌ 실패'}")
    print(f"LangGraph: {'✅ 성공' if langgraph_success else '❌ 실패'}")

    sys.exit(0 if (crewai_success and langgraph_success) else 1)
