from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import sys
import uuid
from dotenv import load_dotenv
from progress_tracker import (
    create_progress,
    update_progress,
    complete_progress,
    get_progress,
    AnalysisProgress
)

# crewai_ 및 langgraph_ 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crewai_'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langgraph_'))

# 환경변수 로드
load_dotenv()

# 사용할 에이전트 프레임워크 설정 (환경변수로 제어 가능)
# AGENT_FRAMEWORK: "crewai" 또는 "langgraph"
AGENT_FRAMEWORK = os.getenv("AGENT_FRAMEWORK", "crewai").lower()

app = FastAPI(title="투자 레포팅 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestReportRequest(BaseModel):
    company: str
    agent_framework: Optional[str] = None  # 프론트엔드에서 선택한 agent framework


class StockInfo(BaseModel):
    current_price: int
    previous_close: int
    change_rate: float
    volume: str
    market_cap: str


class FinancialData(BaseModel):
    revenue: str
    operating_profit: str
    net_profit: str
    operating_margin: str
    net_margin: str


class InvestmentPoint(BaseModel):
    title: str
    content: str


class InvestReportResponse(BaseModel):
    company: str
    industry: str
    report_date: str
    stock_info: StockInfo
    financial_data: FinancialData
    investment_points: List[InvestmentPoint]
    risk_factors: List[str]
    target_price: int
    recommendation: str
    session_id: Optional[str] = None  # 진행 상황 추적용


@app.get("/")
async def root():
    mode_str = "Demo Mode"
    if os.getenv("OPENAI_API_KEY"):
        mode_str = f"{AGENT_FRAMEWORK.upper()}-powered"

    return {
        "message": "투자 레포팅 Agent API",
        "version": "4.0.0",
        "agent_framework": AGENT_FRAMEWORK,
        "mode": mode_str,
        "endpoints": {
            "home": "/",
            "invest_report": "/invest_report",
            "progress": "/progress/{session_id}"
        }
    }


@app.get("/progress/{session_id}")
async def get_analysis_progress(session_id: str):
    """분석 진행 상황 조회"""
    progress = get_progress(session_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Session not found")

    return progress


class InvestReportStartResponse(BaseModel):
    """분석 시작 응답"""
    session_id: str
    message: str


def run_analysis_background(session_id: str, company_name: str, selected_framework: str, openai_api_key: str):
    """백그라운드에서 분석 실행"""
    import time
    bg_start = time.time()

    try:
        if selected_framework == "langgraph":
            # LangGraph를 사용한 분석
            from langgraph_agent import InvestmentReportingGraph

            print(f"\n{'='*60}")
            print(f"[백그라운드] LangGraph 분석 시작: {company_name}")
            print(f"[백그라운드] Session ID: {session_id}")
            print(f"{'='*60}\n")

            analysis_start = time.time()
            graph_system = InvestmentReportingGraph(openai_api_key)
            analysis_result = graph_system.run_analysis(company_name, session_id)
            print(f"[백그라운드 타이밍] LangGraph 분석 완료: {time.time() - analysis_start:.2f}초")

            if "error" in analysis_result:
                complete_progress(session_id, success=False, error=analysis_result["error"])
            else:
                # 결과를 InvestReportResponse로 변환하여 저장
                parse_start = time.time()
                result_response = parse_analysis_result_to_response(company_name, analysis_result, "langgraph")
                result_response.session_id = session_id
                print(f"[백그라운드 타이밍] 결과 파싱: {time.time() - parse_start:.2f}초")

                # Pydantic 모델을 딕셔너리로 변환하여 저장
                dump_start = time.time()
                result_dict = result_response.model_dump()
                print(f"[백그라운드 타이밍] model_dump(): {time.time() - dump_start:.2f}초")

                complete_start = time.time()
                complete_progress(session_id, success=True, result=result_dict)
                print(f"[백그라운드 타이밍] complete_progress(): {time.time() - complete_start:.2f}초")

        else:  # crewai (기본값)
            # CrewAI를 사용한 분석
            from crewai_agent import InvestmentReportingCrew

            print(f"\n{'='*60}")
            print(f"[백그라운드] CrewAI 분석 시작: {company_name}")
            print(f"[백그라운드] Session ID: {session_id}")
            print(f"{'='*60}\n")

            analysis_start = time.time()
            crew_system = InvestmentReportingCrew(openai_api_key)
            crew_result = crew_system.run_analysis(company_name, session_id)
            print(f"[백그라운드 타이밍] ⭐ CrewAI 분석 완료: {time.time() - analysis_start:.2f}초")

            if "error" in crew_result:
                complete_progress(session_id, success=False, error=crew_result["error"])
            else:
                # 결과를 InvestReportResponse로 변환하여 저장
                parse_start = time.time()
                result_response = parse_analysis_result_to_response(company_name, crew_result, "crewai")
                result_response.session_id = session_id
                print(f"[백그라운드 타이밍] ⭐ 결과 파싱: {time.time() - parse_start:.2f}초")

                # Pydantic 모델을 딕셔너리로 변환하여 저장
                dump_start = time.time()
                result_dict = result_response.model_dump()
                print(f"[백그라운드 타이밍] ⭐ model_dump(): {time.time() - dump_start:.2f}초")

                complete_start = time.time()
                complete_progress(session_id, success=True, result=result_dict)
                print(f"[백그라운드 타이밍] ⭐ complete_progress(): {time.time() - complete_start:.2f}초")

    except Exception as e:
        print(f"[백그라운드] {selected_framework.upper()} 분석 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        complete_progress(session_id, success=False, error=str(e))

    total_bg_time = time.time() - bg_start
    print(f"\n[백그라운드 타이밍] ⭐⭐⭐ 전체 백그라운드 작업 시간: {total_bg_time:.2f}초")
    print(f"[백그라운드] Session {session_id} 완료\n")


@app.post("/invest_report_async")
async def start_invest_report(request: InvestReportRequest, background_tasks: BackgroundTasks) -> InvestReportStartResponse:
    """비동기 분석 시작 (session_id 반환)"""
    session_id = str(uuid.uuid4())
    selected_framework = request.agent_framework or AGENT_FRAMEWORK

    # OpenAI API 키 확인
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    # 진행 상황 초기화
    create_progress(session_id, request.company, selected_framework)

    print(f"분석 시작: session_id={session_id}, company={request.company}, framework={selected_framework}")

    # 백그라운드에서 분석 실행
    background_tasks.add_task(
        run_analysis_background,
        session_id,
        request.company,
        selected_framework,
        openai_api_key
    )

    return InvestReportStartResponse(
        session_id=session_id,
        message=f"{request.company} 분석을 시작합니다."
    )


@app.post("/invest_report", response_model=InvestReportResponse)
async def get_invest_report(request: InvestReportRequest):
    company_name = request.company

    # Session ID 생성
    session_id = str(uuid.uuid4())

    # 프론트엔드에서 선택한 agent framework (없으면 환경변수 또는 기본값 사용)
    selected_framework = request.agent_framework or AGENT_FRAMEWORK
    print(f"선택된 에이전트 프레임워크: {selected_framework}")
    print(f"Session ID: {session_id}")

    # 진행 상황 초기화
    create_progress(session_id, company_name, selected_framework)

    # OpenAI API 키 확인
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key:
        # 선택된 프레임워크를 사용한 실제 분석
        try:
            if selected_framework == "langgraph":
                # LangGraph를 사용한 분석
                from langgraph_agent import InvestmentReportingGraph

                print(f"\n{'='*60}")
                print(f"LangGraph 분석 시작: {company_name}")
                print(f"{'='*60}\n")

                graph_system = InvestmentReportingGraph(openai_api_key)
                analysis_result = graph_system.run_analysis(company_name, session_id)

                if "error" in analysis_result:
                    complete_progress(session_id, success=False, error=analysis_result["error"])
                    raise HTTPException(status_code=400, detail=analysis_result["error"])

                complete_progress(session_id, success=True)
                result = parse_analysis_result_to_response(company_name, analysis_result, "langgraph")
                result.session_id = session_id
                return result

            else:  # crewai (기본값)
                # CrewAI를 사용한 분석
                from crewai_agent import InvestmentReportingCrew

                print(f"\n{'='*60}")
                print(f"CrewAI 분석 시작: {company_name}")
                print(f"{'='*60}\n")

                crew_system = InvestmentReportingCrew(openai_api_key)
                crew_result = crew_system.run_analysis(company_name, session_id)

                if "error" in crew_result:
                    complete_progress(session_id, success=False, error=crew_result["error"])
                    raise HTTPException(status_code=400, detail=crew_result["error"])

                complete_progress(session_id, success=True)
                result = parse_analysis_result_to_response(company_name, crew_result, "crewai")
                result.session_id = session_id
                return result

        except Exception as e:
            print(f"{selected_framework.upper()} 분석 오류: {str(e)}")
            print("더미 데이터로 폴백합니다...")
            import traceback
            traceback.print_exc()
            complete_progress(session_id, success=False, error=str(e))
            # 오류 발생 시 더미 데이터로 폴백
            return get_dummy_report(company_name)
    else:
        # OpenAI API 키가 없으면 더미 데이터 반환
        print(f"OPENAI_API_KEY가 설정되지 않았습니다. 더미 데이터를 반환합니다.")
        complete_progress(session_id, success=False, error="OPENAI_API_KEY not set")
        return get_dummy_report(company_name)


def parse_stock_price_data(stock_text: str) -> Dict[str, Any]:
    """주가 데이터 텍스트에서 정보 추출"""
    import re
    result = {}

    try:
        # 현재가 추출
        current_price_match = re.search(r'현재가:\s*([0-9,]+)원', stock_text)
        if current_price_match:
            result["current_price"] = int(current_price_match.group(1).replace(',', ''))

        # 전일 대비 추출
        change_match = re.search(r'전일 대비:\s*([+-]?[0-9.]+)%', stock_text)
        if change_match:
            result["change_rate"] = float(change_match.group(1))

        # 거래량 추출
        volume_match = re.search(r'거래량:\s*([0-9,]+)주', stock_text)
        if volume_match:
            result["volume"] = volume_match.group(1)

    except Exception as e:
        print(f"주가 데이터 파싱 오류: {e}")

    return result


def parse_analysis_result_to_response(company_name: str, analysis_result: Dict[str, Any], framework: str = "unknown") -> InvestReportResponse:
    """
    CrewAI 또는 LangGraph 분석 결과를 응답 형식으로 변환합니다.

    Args:
        company_name: 회사명
        analysis_result: 분석 결과
        framework: 사용된 프레임워크 ("crewai" 또는 "langgraph")
    """
    import re

    # 기본 더미 데이터를 시작점으로 사용 (딕셔너리로 변환)
    dummy_response = get_dummy_report(company_name)
    dummy = dummy_response.model_dump()

    try:
        # 실제 주가 데이터 적용
        real_data = analysis_result.get("real_data", {})
        if real_data:
            stock_data_text = real_data.get("stock_price_data", "")
            if stock_data_text:
                stock_info = parse_stock_price_data(stock_data_text)
                if stock_info:
                    # 실제 데이터로 업데이트
                    if "current_price" in stock_info:
                        dummy["stock_info"]["current_price"] = stock_info["current_price"]
                        dummy["stock_info"]["previous_close"] = int(stock_info["current_price"] / (1 + stock_info.get("change_rate", 0) / 100))
                    if "change_rate" in stock_info:
                        dummy["stock_info"]["change_rate"] = stock_info["change_rate"]
                    if "volume" in stock_info:
                        dummy["stock_info"]["volume"] = stock_info["volume"]

                    print(f"✓ 실제 주가 데이터 적용: 현재가 {dummy['stock_info']['current_price']:,}원, 변동률 {dummy['stock_info']['change_rate']}%")

        # 분석 결과에서 분석 내용 추출
        analysis_text = analysis_result.get("analysis_result", "")

        if not analysis_text or analysis_text == "":
            print("분석 결과가 비어있습니다. 더미 데이터를 반환합니다.")
            return dummy

        print("\n" + "="*60)
        print(f"{framework.upper()} 분석 결과:")
        print("="*60)
        print(analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text)
        print("="*60 + "\n")

        # 투자의견 추출
        recommendation_match = re.search(
            r'투자\s*의견\s*:\s*(\S+)',
            analysis_text,
            re.IGNORECASE
        )
        if recommendation_match:
            rec = recommendation_match.group(1).strip()
            if '매수' in rec:
                dummy["recommendation"] = "매수"
            elif '매도' in rec:
                dummy["recommendation"] = "매도"
            else:
                dummy["recommendation"] = "보유"
            print(f"추출된 투자의견: {dummy['recommendation']}")

        # 목표주가 추출
        target_price_match = re.search(
            r'목표\s*주가\s*:\s*([0-9,]+)',
            analysis_text,
            re.IGNORECASE
        )
        if target_price_match:
            price_str = target_price_match.group(1).replace(',', '')
            try:
                dummy["target_price"] = int(price_str)
                print(f"추출된 목표주가: {dummy['target_price']}")
            except ValueError:
                pass

        # 투자 포인트 추출
        investment_section = re.search(
            r'투자\s*포인트\s*:\s*\n(.*?)(?=\n\n리스크|리스크\s*요인|$)',
            analysis_text,
            re.DOTALL | re.IGNORECASE
        )

        if investment_section:
            points_text = investment_section.group(1)
            points = []
            for line in points_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    line = line[1:].strip()
                    if ':' in line:
                        title, content = line.split(':', 1)
                        points.append({
                            "title": title.strip(),
                            "content": content.strip()
                        })

            if points:
                dummy["investment_points"] = points[:3]
                print(f"추출된 투자 포인트 개수: {len(points)}")

        # 리스크 요인 추출
        risk_section = re.search(
            r'리스크\s*요인\s*:\s*\n(.*?)(?=\n\n결론|결론\s*:|$)',
            analysis_text,
            re.DOTALL | re.IGNORECASE
        )

        if risk_section:
            risks_text = risk_section.group(1)
            risks = []
            for line in risks_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    line = line[1:].strip()
                    if line:
                        risks.append(line)

            if risks:
                dummy["risk_factors"] = risks[:3]
                print(f"추출된 리스크 요인 개수: {len(risks)}")

        # 최종 결과 확인
        print(f"\n[최종 반환 데이터]")
        print(f"  회사: {dummy.get('company')}")
        print(f"  투자의견: {dummy.get('recommendation')}")
        print(f"  목표주가: {dummy.get('target_price')}")
        print(f"  투자 포인트: {len(dummy.get('investment_points', []))}개")
        print(f"  리스크 요인: {len(dummy.get('risk_factors', []))}개")
        print(f"  현재가: {dummy.get('stock_info', {}).get('current_price')}\n")

        # 딕셔너리를 InvestReportResponse 모델로 변환
        return InvestReportResponse(**dummy)

    except Exception as e:
        print(f"{framework.upper()} 결과 파싱 중 오류 발생: {str(e)}")
        print("더미 데이터를 반환합니다.")
        import traceback
        traceback.print_exc()
        # 딕셔너리를 InvestReportResponse 모델로 변환
        return InvestReportResponse(**dummy)


def get_dummy_report(company_name: str) -> InvestReportResponse:
    """더미 데이터 반환 (기존 로직 유지)"""
    dummy_reports = {
        "삼성전자": {
            "company": "삼성전자",
            "industry": "반도체/전자",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "stock_info": {
                "current_price": 72500,
                "previous_close": 71000,
                "change_rate": 2.11,
                "volume": "15,234,567",
                "market_cap": "432조 원"
            },
            "financial_data": {
                "revenue": "302.2조 원",
                "operating_profit": "35.4조 원",
                "net_profit": "26.1조 원",
                "operating_margin": "11.7%",
                "net_margin": "8.6%"
            },
            "investment_points": [
                {
                    "title": "메모리 반도체 시장 회복",
                    "content": "DRAM 및 NAND 플래시 가격 상승으로 수익성 개선 예상"
                },
                {
                    "title": "AI 시장 성장",
                    "content": "HBM(고대역폭메모리) 수요 급증으로 프리미엄 제품 판매 확대"
                },
                {
                    "title": "파운드리 경쟁력 강화",
                    "content": "3nm 공정 기술 개선 및 주요 고객사 확보"
                }
            ],
            "risk_factors": [
                "글로벌 경기 둔화에 따른 수요 감소 우려",
                "중국 반도체 업체들의 추격",
                "환율 변동성 리스크"
            ],
            "target_price": 85000,
            "recommendation": "매수"
        },
        "SK하이닉스": {
            "company": "SK하이닉스",
            "industry": "반도체",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "stock_info": {
                "current_price": 185000,
                "previous_close": 182000,
                "change_rate": 1.65,
                "volume": "2,456,789",
                "market_cap": "135조 원"
            },
            "financial_data": {
                "revenue": "48.5조 원",
                "operating_profit": "6.8조 원",
                "net_profit": "5.2조 원",
                "operating_margin": "14.0%",
                "net_margin": "10.7%"
            },
            "investment_points": [
                {
                    "title": "HBM 시장 선도",
                    "content": "HBM3E 양산으로 AI 서버 시장 공략 본격화"
                },
                {
                    "title": "DRAM 점유율 확대",
                    "content": "고부가가치 제품 비중 증가로 수익성 향상"
                },
                {
                    "title": "엔비디아 파트너십",
                    "content": "주요 고객사와의 긴밀한 협력 관계 유지"
                }
            ],
            "risk_factors": [
                "메모리 반도체 가격 변동성",
                "삼성전자와의 경쟁 심화",
                "설비 투자 부담 증가"
            ],
            "target_price": 220000,
            "recommendation": "매수"
        },
        "현대차": {
            "company": "현대차",
            "industry": "자동차",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "stock_info": {
                "current_price": 245000,
                "previous_close": 242000,
                "change_rate": 1.24,
                "volume": "1,234,567",
                "market_cap": "52조 원"
            },
            "financial_data": {
                "revenue": "162.7조 원",
                "operating_profit": "11.6조 원",
                "net_profit": "9.8조 원",
                "operating_margin": "7.1%",
                "net_margin": "6.0%"
            },
            "investment_points": [
                {
                    "title": "전기차 라인업 확대",
                    "content": "아이오닉 시리즈 판매 호조 및 신모델 출시 예정"
                },
                {
                    "title": "북미 시장 점유율 상승",
                    "content": "SUV 및 트럭 판매 증가로 수익성 개선"
                },
                {
                    "title": "배터리 기술 혁신",
                    "content": "차세대 배터리 개발로 주행거리 경쟁력 확보"
                }
            ],
            "risk_factors": [
                "원자재 가격 상승 압력",
                "글로벌 자동차 시장 경쟁 심화",
                "전기차 보조금 축소 우려"
            ],
            "target_price": 280000,
            "recommendation": "매수"
        }
    }

    # 요청된 회사의 데이터 반환, 없으면 기본 더미 데이터 반환
    if company_name in dummy_reports:
        return InvestReportResponse(**dummy_reports[company_name])
    else:
        # 기본 더미 데이터
        default_data = {
            "company": company_name,
            "industry": "기타",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "stock_info": {
                "current_price": 50000,
                "previous_close": 49000,
                "change_rate": 2.04,
                "volume": "1,000,000",
                "market_cap": "10조 원"
            },
            "financial_data": {
                "revenue": "10조 원",
                "operating_profit": "1조 원",
                "net_profit": "0.8조 원",
                "operating_margin": "10.0%",
                "net_margin": "8.0%"
            },
            "investment_points": [
                {
                    "title": "시장 성장성",
                    "content": "해당 산업의 지속적인 성장 전망"
                },
                {
                    "title": "기술 경쟁력",
                    "content": "핵심 기술력 보유로 경쟁 우위 확보"
                },
                {
                    "title": "수익성 개선",
                    "content": "비용 절감 및 효율화를 통한 이익률 향상"
                }
            ],
            "risk_factors": [
                "시장 경쟁 심화",
                "규제 리스크",
                "경기 변동성"
            ],
            "target_price": 60000,
            "recommendation": "보유"
        }
        return InvestReportResponse(**default_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
