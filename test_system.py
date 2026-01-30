"""
프로젝트 전체 시스템 테스트 스크립트
"""
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'crewai_'))

def test_imports():
    """모듈 import 테스트"""
    print("=" * 60)
    print("모듈 Import 테스트")
    print("=" * 60)

    try:
        print("\n1. FinanceDataReader 테스트...")
        import FinanceDataReader as fdr
        print("   [OK] FinanceDataReader import 성공")
    except Exception as e:
        print(f"   [FAIL] FinanceDataReader import 실패: {e}")
        return False

    try:
        print("\n2. CrewAI 테스트...")
        from crewai import Agent, Task, Crew, Process
        print("   [OK] CrewAI import 성공")
    except Exception as e:
        print(f"   [FAIL] CrewAI import 실패: {e}")
        return False

    try:
        print("\n3. stock_analysis_tool 테스트...")
        from stock_analysis_tool import (
            get_stock_price_data,
            get_company_info,
            calculate_financial_ratios,
            get_market_index,
            get_ticker_from_company_name
        )
        print("   [OK] stock_analysis_tool import 성공")
    except Exception as e:
        print(f"   [FAIL] stock_analysis_tool import 실패: {e}")
        return False

    try:
        print("\n4. crewai_agent 테스트...")
        from crewai_agent import InvestmentReportingCrew
        print("   [OK] crewai_agent import 성공")
    except Exception as e:
        print(f"   [FAIL] crewai_agent import 실패: {e}")
        return False

    print("\n" + "=" * 60)
    print("모든 모듈 import 성공!")
    print("=" * 60)
    return True


def test_finance_data_reader():
    """FinanceDataReader 기능 테스트"""
    print("\n" + "=" * 60)
    print("FinanceDataReader 기능 테스트")
    print("=" * 60)

    try:
        from stock_analysis_tool import get_ticker_from_company_name, get_stock_price_data

        company = "삼성전자"
        ticker = get_ticker_from_company_name(company)
        print(f"\n회사명: {company}")
        print(f"티커: {ticker}")

        if ticker:
            print(f"\n주가 데이터 조회 중...")
            # get_stock_price_data is a Tool object, need to call .func
            result = get_stock_price_data.func(ticker, days=7)
            print("\n" + result)
            print("\n[OK] FinanceDataReader 기능 테스트 성공")
            return True
        else:
            print("[FAIL] 티커를 찾을 수 없습니다")
            return False

    except Exception as e:
        print(f"[FAIL] FinanceDataReader 기능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_integration():
    """백엔드 통합 테스트"""
    print("\n" + "=" * 60)
    print("백엔드 통합 테스트")
    print("=" * 60)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from main import get_dummy_report

        print("\n더미 데이터 테스트...")
        result = get_dummy_report("삼성전자")
        print(f"[OK] 회사: {result['company']}")
        print(f"[OK] 산업: {result['industry']}")
        print(f"[OK] 투자의견: {result['recommendation']}")
        print(f"[OK] 목표주가: {result['target_price']:,}원")

        print("\n[OK] 백엔드 통합 테스트 성공")
        return True

    except Exception as e:
        print(f"[FAIL] 백엔드 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 테스트 실행"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "시스템 테스트 시작")
    print("=" * 60)

    results = []

    # 1. Import 테스트
    results.append(("모듈 Import", test_imports()))

    # 2. FinanceDataReader 테스트
    if results[-1][1]:  # Import가 성공했으면
        results.append(("FinanceDataReader", test_finance_data_reader()))

    # 3. 백엔드 통합 테스트
    results.append(("백엔드 통합", test_backend_integration()))

    # 결과 요약
    print("\n")
    print("=" * 60)
    print(" " * 18 + "테스트 결과 요약")
    print("=" * 60)

    for name, success in results:
        status = "[OK] 성공" if success else "[FAIL] 실패"
        print(f"{name:20s}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("모든 테스트 통과!")
        print("\n다음 단계:")
        print("1. backend/.env 파일에 OPENAI_API_KEY 설정 (선택사항)")
        print("2. backend 서버 실행: cd backend && uv run python main.py")
        print("3. frontend 서버 실행: cd frontend && npm start")
    else:
        print("일부 테스트 실패")
        print("\n의존성을 설치했는지 확인하세요:")
        print("  cd backend")
        print("  uv pip install -r requirements.txt")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
