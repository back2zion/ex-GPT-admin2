/**
 * 모델 서비스 관리 페이지
 * 실행 중인 서비스 모니터링 및 관리
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import './ServiceManagement.css';

const API_BASE_URL = '/api/v1/admin';

export default function ServiceManagement() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  // 서비스 목록 조회
  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/deployment/bentos`);
      console.log('Fetched services:', response.data.bentos);
      setServices(response.data.bentos);
    } catch (error) {
      console.error('Failed to fetch services:', error);
      alert('서비스 목록 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();

    // 10초마다 자동 새로고침
    const interval = setInterval(fetchServices, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="service-management-page">
      <div className="page-header">
        <div>
          <h1>🎯 모델 서비스 관리</h1>
          <p className="page-description">실행 중인 AI 모델 서비스 모니터링 및 관리</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={fetchServices} disabled={loading}>
            🔄 새로고침
          </button>
        </div>
      </div>

      {loading && services.length === 0 ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>서비스 목록을 불러오는 중...</p>
        </div>
      ) : services.length === 0 ? (
        <div className="empty-state-container">
          <div className="empty-icon">📭</div>
          <h3>실행 중인 서비스가 없습니다</h3>
          <p>vLLM 모델 서비스를 시작하면 여기에 표시됩니다</p>
        </div>
      ) : (
        <div className="services-grid">
          {services.map((service, index) => {
            console.log(`Rendering card ${index}:`, service.model, service.port);
            return (
            <div key={service.tag} className="service-card">
              <div className="service-header">
                <div>
                  <h3>{service.model}</h3>
                  <span className="service-tag">{service.tag}</span>
                </div>
                <span className={`status-badge ${service.status}`}>
                  {service.status === 'serving' ? '● 실행 중' : '○ 중지'}
                </span>
              </div>

              <div className="service-body">
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-icon">🏷️</span>
                    <div>
                      <div className="info-label">서비스 이름</div>
                      <div className="info-value">{service.name}</div>
                    </div>
                  </div>

                  <div className="info-item">
                    <span className="info-icon">🔌</span>
                    <div>
                      <div className="info-label">포트</div>
                      <div className="info-value">{service.port}</div>
                    </div>
                  </div>

                  <div className="info-item">
                    <span className="info-icon">🌐</span>
                    <div>
                      <div className="info-label">엔드포인트</div>
                      <div className="info-value endpoint">
                        {`${window.location.protocol}//${window.location.hostname}:${service.port}`}
                      </div>
                    </div>
                  </div>

                  <div className="info-item">
                    <span className="info-icon">⏱️</span>
                    <div>
                      <div className="info-label">생성 시간</div>
                      <div className="info-value">
                        {new Date(service.created_at).toLocaleString('ko-KR')}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="service-footer">
                <button
                  className="btn-action"
                  onClick={() => window.open(`/api/v1/admin/deployment/services/${service.port}/docs`, '_blank')}
                  title="API 문서 보기"
                >
                  📄 API 문서
                </button>
                <button
                  className="btn-action"
                  onClick={async () => {
                    try {
                      const response = await axios.get(`${API_BASE_URL}/deployment/services/${service.port}/health`);
                      alert(`포트 ${service.port} 상태: ${response.data.status}\n상태 코드: ${response.data.status_code}`);
                    } catch (error) {
                      alert(`Health check 실패: ${error.response?.data?.error || error.message}`);
                    }
                  }}
                  title="Health Check"
                >
                  🏥 Health
                </button>
              </div>
            </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
