"""
재무 분석 툴 - FinanceDataReader를 활용한 한국 주식 데이터 수집 (LangGraph용)
"""
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
from langchain_core.tools import tool


@tool
def get_stock_price_data(ticker: str, days: int = 30) -> str:
    """
    주식의 가격 데이터를 조회합니다.

    Args:
        ticker: 주식 티커 (예: '005930' for 삼성전자)
        days: 조회할 일수 (기본 30일)

    Returns:
        가격 데이터 문자열
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = fdr.DataReader(ticker, start_date, end_date)

        if df.empty:
            return f"Error: No price data found for ticker {ticker}"

        # 최신 데이터
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        result = f"""
주식 가격 정보 (티커: {ticker}):
- 최근 거래일: {df.index[-1].strftime('%Y-%m-%d')}
- 현재가: {latest['Close']:,.0f}원
- 시가: {latest['Open']:,.0f}원
- 고가: {latest['High']:,.0f}원
- 저가: {latest['Low']:,.0f}원
- 거래량: {latest['Volume']:,.0f}주
- 전일 대비: {((latest['Close'] - prev['Close']) / prev['Close'] * 100):.2f}%

최근 {days}일 통계:
- 평균 거래가: {df['Close'].mean():,.0f}원
- 최고가: {df['High'].max():,.0f}원
- 최저가: {df['Low'].min():,.0f}원
- 평균 거래량: {df['Volume'].mean():,.0f}주
"""
        return result

    except Exception as e:
        return f"Error fetching stock price data: {str(e)}"


@tool
def get_company_info(company_name: str) -> str:
    """
    회사의 기본 정보를 조회합니다.

    Args:
        company_name: 회사명 (예: '삼성전자')

    Returns:
        회사 정보 문자열
    """
    # 주요 한국 기업 티커 매핑
    ticker_map = {
        '삼성전자': '005930',
        'SK하이닉스': '000660',
        '현대차': '005380',
        'NAVER': '035420',
        '카카오': '035720',
        'LG에너지솔루션': '373220',
    }

    ticker = ticker_map.get(company_name)

    if not ticker:
        return f"Error: Unknown company '{company_name}'. Please use one of: {', '.join(ticker_map.keys())}"

    try:
        # KRX 상장 기업 정보
        krx_list = fdr.StockListing('KRX')
        company_info = krx_list[krx_list['Code'] == ticker]

        if company_info.empty:
            return f"회사명: {company_name}\n티커: {ticker}\n상장: KOSPI/KOSDAQ"

        info = company_info.iloc[0]

        result = f"""
기업 정보:
- 회사명: {info.get('Name', company_name)}
- 티커: {ticker}
- 시장: {info.get('Market', 'N/A')}
- 업종: {info.get('Sector', 'N/A')}
- 상장주식수: {info.get('Stocks', 'N/A')}
"""
        return result

    except Exception as e:
        return f"""
기업 정보:
- 회사명: {company_name}
- 티커: {ticker}
- 시장: KOSPI/KOSDAQ
Note: Detailed information unavailable - {str(e)}
"""


@tool
def calculate_financial_ratios(ticker: str) -> str:
    """
    재무 비율을 계산합니다.

    Args:
        ticker: 주식 티커

    Returns:
        재무 비율 정보 문자열
    """
    try:
        # 최근 1년 데이터
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        df = fdr.DataReader(ticker, start_date, end_date)

        if df.empty:
            return f"Error: No data available for ticker {ticker}"

        # 가격 변동성 계산
        returns = df['Close'].pct_change()
        volatility = returns.std() * (252 ** 0.5) * 100  # 연간 변동성

        # 52주 최고/최저
        high_52w = df['High'].max()
        low_52w = df['Low'].min()
        current_price = df['Close'].iloc[-1]

        # 현재가가 52주 범위에서 어디에 위치하는지
        position_in_range = ((current_price - low_52w) / (high_52w - low_52w) * 100) if high_52w != low_52w else 50

        result = f"""
재무 지표 (티커: {ticker}):
- 52주 최고가: {high_52w:,.0f}원
- 52주 최저가: {low_52w:,.0f}원
- 현재 위치: {position_in_range:.1f}% (52주 범위 내)
- 연간 변동성: {volatility:.2f}%
- 1개월 수익률: {((df['Close'].iloc[-1] / df['Close'].iloc[-22] - 1) * 100) if len(df) > 22 else 0:.2f}%
- 3개월 수익률: {((df['Close'].iloc[-1] / df['Close'].iloc[-66] - 1) * 100) if len(df) > 66 else 0:.2f}%
- 6개월 수익률: {((df['Close'].iloc[-1] / df['Close'].iloc[-132] - 1) * 100) if len(df) > 132 else 0:.2f}%
"""
        return result

    except Exception as e:
        return f"Error calculating financial ratios: {str(e)}"


@tool
def get_market_index(days: int = 30) -> str:
    """
    시장 지수 정보를 조회합니다.

    Args:
        days: 조회할 일수 (기본 30일)

    Returns:
        시장 지수 정보 문자열
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # KOSPI 지수
        kospi = fdr.DataReader('KS11', start_date, end_date)

        if kospi.empty:
            return "Error: No KOSPI data available"

        latest_kospi = kospi['Close'].iloc[-1]
        prev_kospi = kospi['Close'].iloc[-2] if len(kospi) > 1 else latest_kospi
        kospi_change = ((latest_kospi - prev_kospi) / prev_kospi * 100)

        result = f"""
시장 지수 정보:
- KOSPI: {latest_kospi:,.2f}
- 전일 대비: {kospi_change:+.2f}%
- {days}일 평균: {kospi['Close'].mean():,.2f}
- {days}일 최고: {kospi['Close'].max():,.2f}
- {days}일 최저: {kospi['Close'].min():,.2f}
"""

        return result

    except Exception as e:
        return f"Error fetching market index: {str(e)}"


def get_ticker_from_company_name(company_name: str) -> Optional[str]:
    """
    회사명으로부터 티커를 가져옵니다.

    Args:
        company_name: 회사명

    Returns:
        티커 문자열 또는 None
    """
    ticker_map = {
        '삼성전자': '005930',
        'SK하이닉스': '000660',
        '현대차': '005380',
        'NAVER': '035420',
        '카카오': '035720',
        'LG에너지솔루션': '373220',
    }

    return ticker_map.get(company_name)
