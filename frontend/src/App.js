import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState('langgraph'); // 기본값: langgraph
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const companies = ['삼성전자', 'SK하이닉스', '현대차', 'NAVER', '카카오', 'LG에너지솔루션'];

  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
  };

  const pollProgress = async (sid) => {
    try {
      const response = await axios.get(`http://localhost:8000/progress/${sid}`);
      console.log('[프론트엔드] Progress 업데이트:', {
        status: response.data.status,
        current_step: response.data.current_step,
        steps: response.data.steps.map(s => ({ step: s.step, status: s.status, message: s.message }))
      });
      setProgressData(response.data);

      // 분석이 완료되지 않았으면 계속 폴링
      if (response.data.status === 'running') {
        setTimeout(() => pollProgress(sid), 500); // 0.5초마다 업데이트
      } else if (response.data.status === 'completed') {
        // 분석 완료 - 최종 결과 가져오기
        console.log('[프론트엔드] 분석 완료! 결과를 가져옵니다...');
        await fetchFinalResult(sid);
      } else if (response.data.status === 'failed') {
        console.error('[프론트엔드] 분석 실패:', response.data.error);
        setError('분석 중 오류가 발생했습니다: ' + (response.data.error || '알 수 없는 오류'));
        setLoading(false);
      }
    } catch (err) {
      console.error('[프론트엔드] Progress polling error:', err);
    }
  };

  const fetchFinalResult = async (sid) => {
    try {
      console.log('[프론트엔드] 최종 결과 요청 시작...');
      // 진행 상황에서 저장된 결과 가져오기
      const response = await axios.get(`http://localhost:8000/progress/${sid}`);
      console.log('[프론트엔드] 최종 결과 수신:', response.data.result ? '있음' : '없음');
      if (response.data.result) {
        setReportData(response.data.result);
        setLoading(false);
        console.log('[프론트엔드] 로딩 완료!');
      } else {
        console.error('[프론트엔드] 결과가 없음');
        setError('분석 결과를 찾을 수 없습니다.');
        setLoading(false);
      }
    } catch (err) {
      setError('최종 결과를 가져오는데 실패했습니다.');
      console.error('[프론트엔드] Error fetching final result:', err);
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedCompany) {
      setError('기업을 선택해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setProgressData(null);
    setReportData(null);

    try {
      // 비동기 분석 시작 (즉시 session_id 반환)
      const response = await axios.post('http://localhost:8000/invest_report_async', {
        company: selectedCompany,
        agent_framework: selectedAgent
      });

      const sid = response.data.session_id;
      setSessionId(sid);
      console.log('분석 시작:', response.data.message, 'Session ID:', sid);

      // 진행 상황 폴링 시작
      pollProgress(sid);

    } catch (err) {
      setError('분석 시작에 실패했습니다. 백엔드 서버를 확인해주세요.');
      console.error('Error starting analysis:', err);
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return num?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  };

  return (
    <div className="App">
      <div className="container">
        <h1 className="title">국내 상장사 투자 레포팅 Agent</h1>

        {!reportData ? (
          <>
            <p className="subtitle">AI Agent 프레임워크와 종목을 선택하고 레포팅 요청을 하세요.</p>

            <div className="input-section">
              {/* Agent 선택 */}
              <div className="select-wrapper">
                <label className="select-label">AI Agent 선택:</label>
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="agent-select"
                  disabled={loading}
                >
                  <option value="langgraph">LangGraph (추천)</option>
                  <option value="crewai">CrewAI</option>
                </select>
              </div>

              {/* 기업 선택 */}
              <div className="select-wrapper">
                <label className="select-label">기업 선택:</label>
                <select
                  value={selectedCompany || ''}
                  onChange={(e) => setSelectedCompany(e.target.value)}
                  className="company-select"
                  disabled={loading}
                >
                  <option value="" disabled>기업을 선택하세요</option>
                  {companies.map((company) => (
                    <option key={company} value={company}>
                      {company}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleSubmit}
                className="report-button"
                disabled={loading || !selectedCompany}
              >
                {loading ? '레포팅 중...' : '레포팅 요청'}
              </button>
            </div>

            {loading && (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <div className="loading-text">
                  <h3>{selectedAgent === 'langgraph' ? 'LangGraph' : 'CrewAI'} 에이전트가 {selectedCompany} 분석 중입니다...</h3>
                  <p className="framework-info">사용 중인 프레임워크: {selectedAgent.toUpperCase()}</p>
                  <div className="agent-steps">
                    {progressData && progressData.steps ? (
                      progressData.steps.map((step, index) => (
                        <div
                          key={index}
                          className={`step ${step.status === 'completed' ? 'completed' : step.status === 'in_progress' ? 'active' : ''}`}
                        >
                          <span className={`step-icon ${step.status === 'in_progress' ? 'pulse' : ''}`}>
                            {index === 0 ? '📊' : index === 1 ? '📈' : index === 2 ? '⚠️' : '💡'}
                          </span>
                          <span>
                            {step.message}
                            {step.status === 'completed' && ' ✓'}
                            {step.status === 'in_progress' && ' ...'}
                          </span>
                        </div>
                      ))
                    ) : (
                      <>
                        <div className="step">
                          <span className="step-icon">📊</span>
                          <span>재무 분석가: 재무 데이터 수집 및 분석</span>
                        </div>
                        <div className="step">
                          <span className="step-icon">📈</span>
                          <span>시장 분석가: 시장 동향 및 경쟁사 분석</span>
                        </div>
                        <div className="step">
                          <span className="step-icon">⚠️</span>
                          <span>리스크 분석가: 위험 요인 평가</span>
                        </div>
                        <div className="step">
                          <span className="step-icon">💡</span>
                          <span>투자 자문가: 최종 투자 의견 작성</span>
                        </div>
                      </>
                    )}
                  </div>
                  <p className="loading-note">이 작업은 30초~1분 정도 소요될 수 있습니다.</p>
                </div>
              </div>
            )}

            {error && !loading && (
              <div className="error-message">
                {error}
              </div>
            )}
          </>
        ) : (
          <button
            onClick={() => {
              setReportData(null);
              setSelectedCompany(null);
              setError(null);
            }}
            className="back-button"
          >
            ← 돌아가기
          </button>
        )}

        {reportData && (
          <div className="report-container">
            <div className="report-header">
              <h2>{reportData.company}</h2>
              <div className="report-meta">
                <span className="industry">{reportData.industry}</span>
                <span className="date">리포트 날짜: {reportData.report_date}</span>
              </div>
            </div>

            <div className="report-section">
              <h3>주가 정보</h3>
              <div className="info-grid">
                <div className="info-item">
                  <span className="label">현재가</span>
                  <span className="value price">{formatNumber(reportData.stock_info.current_price)}원</span>
                </div>
                <div className="info-item">
                  <span className="label">전일 대비</span>
                  <span className={`value ${reportData.stock_info.change_rate >= 0 ? 'positive' : 'negative'}`}>
                    {reportData.stock_info.change_rate >= 0 ? '+' : ''}{reportData.stock_info.change_rate}%
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">거래량</span>
                  <span className="value">{reportData.stock_info.volume}</span>
                </div>
                <div className="info-item">
                  <span className="label">시가총액</span>
                  <span className="value">{reportData.stock_info.market_cap}</span>
                </div>
              </div>
            </div>

            <div className="report-section">
              <h3>재무 정보</h3>
              <div className="info-grid">
                <div className="info-item">
                  <span className="label">매출액</span>
                  <span className="value">{reportData.financial_data.revenue}</span>
                </div>
                <div className="info-item">
                  <span className="label">영업이익</span>
                  <span className="value">{reportData.financial_data.operating_profit}</span>
                </div>
                <div className="info-item">
                  <span className="label">순이익</span>
                  <span className="value">{reportData.financial_data.net_profit}</span>
                </div>
                <div className="info-item">
                  <span className="label">영업이익률</span>
                  <span className="value">{reportData.financial_data.operating_margin}</span>
                </div>
              </div>
            </div>

            <div className="report-section">
              <h3>투자 포인트</h3>
              <div className="investment-points">
                {reportData.investment_points.map((point, index) => (
                  <div key={index} className="point-card">
                    <h4>{point.title}</h4>
                    <p>{point.content}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="report-section">
              <h3>리스크 요인</h3>
              <ul className="risk-list">
                {reportData.risk_factors.map((risk, index) => (
                  <li key={index}>{risk}</li>
                ))}
              </ul>
            </div>

            <div className="report-footer">
              <div className="recommendation-card">
                <div className="target-price">
                  <span className="label">목표주가</span>
                  <span className="value">{formatNumber(reportData.target_price)}원</span>
                </div>
                <div className={`recommendation ${reportData.recommendation}`}>
                  <span className="label">투자의견</span>
                  <span className="value">{reportData.recommendation}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
