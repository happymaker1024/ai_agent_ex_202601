"""
분석 진행 상황 추적 모듈
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel


class ProgressStep(BaseModel):
    """진행 단계"""
    step: str  # "financial_analyst", "market_analyst", "risk_analyst", "investment_advisor"
    status: str  # "pending", "in_progress", "completed"
    message: str
    timestamp: str


class AnalysisProgress(BaseModel):
    """분석 진행 상황"""
    session_id: str
    company: str
    framework: str  # "crewai" or "langgraph"
    status: str  # "running", "completed", "failed"
    current_step: int  # 0-3
    steps: List[ProgressStep]
    start_time: str
    end_time: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None  # 분석 결과 저장


# 전역 진행 상황 저장소 (메모리)
progress_store: Dict[str, AnalysisProgress] = {}


def create_progress(session_id: str, company: str, framework: str) -> AnalysisProgress:
    """새로운 진행 상황 생성"""
    steps = [
        ProgressStep(
            step="financial_analyst",
            status="pending",
            message="재무 데이터 수집 및 분석",
            timestamp=""
        ),
        ProgressStep(
            step="market_analyst",
            status="pending",
            message="시장 동향 및 경쟁사 분석",
            timestamp=""
        ),
        ProgressStep(
            step="risk_analyst",
            status="pending",
            message="위험 요인 평가",
            timestamp=""
        ),
        ProgressStep(
            step="investment_advisor",
            status="pending",
            message="최종 투자 의견 작성",
            timestamp=""
        )
    ]

    progress = AnalysisProgress(
        session_id=session_id,
        company=company,
        framework=framework,
        status="running",
        current_step=0,
        steps=steps,
        start_time=datetime.now().isoformat()
    )

    progress_store[session_id] = progress
    return progress


def update_progress(session_id: str, step_index: int, status: str, message: Optional[str] = None):
    """진행 상황 업데이트"""
    if session_id not in progress_store:
        return

    progress = progress_store[session_id]

    if 0 <= step_index < len(progress.steps):
        progress.steps[step_index].status = status
        progress.steps[step_index].timestamp = datetime.now().isoformat()

        if message:
            progress.steps[step_index].message = message

        if status == "in_progress":
            progress.current_step = step_index
        elif status == "completed":
            # 다음 단계로 이동
            if step_index < len(progress.steps) - 1:
                progress.current_step = step_index + 1


def complete_progress(session_id: str, success: bool = True, error: Optional[str] = None, result: Optional[Dict[str, Any]] = None):
    """분석 완료 처리"""
    if session_id not in progress_store:
        return

    progress = progress_store[session_id]
    progress.status = "completed" if success else "failed"
    progress.end_time = datetime.now().isoformat()

    if error:
        progress.error = error

    if result:
        progress.result = result


def get_progress(session_id: str) -> Optional[AnalysisProgress]:
    """진행 상황 조회"""
    return progress_store.get(session_id)


def clear_old_progress(hours: int = 24):
    """오래된 진행 상황 삭제"""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(hours=hours)
    to_delete = []

    for session_id, progress in progress_store.items():
        start_time = datetime.fromisoformat(progress.start_time)
        if start_time < cutoff:
            to_delete.append(session_id)

    for session_id in to_delete:
        del progress_store[session_id]
