/**
 * 시스템 배포 현황 페이지
 * GPU 사용 현황 및 시스템 모니터링
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import './SystemStatus.css';

const API_BASE_URL = '/api/v1/admin';

export default function SystemStatus() {
  const [gpuStatus, setGpuStatus] = useState(null);
  const [services, setServices] = useState([]);
  const [containers, setContainers] = useState([]);
  const [loading, setLoading] = useState(false);

  // 전체 데이터 조회
  const fetchSystemStatus = async () => {
    setLoading(true);
    try {
      const [gpuResponse, servicesResponse, containersResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/deployment/gpu/status`),
        axios.get(`${API_BASE_URL}/deployment/bentos`),
        axios.get(`${API_BASE_URL}/deployment/docker/containers`)
      ]);
      setGpuStatus(gpuResponse.data);
      setServices(servicesResponse.data.bentos);
      setContainers(containersResponse.data.containers);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();

    // 10초마다 자동 새로고침
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  // 통계 계산
  const totalGPUs = gpuStatus?.gpus?.length || 0;
  const activeGPUs = gpuStatus?.gpus?.filter(gpu => gpu.utilization > 10).length || 0;
  const avgUtilization = gpuStatus?.gpus
    ? Math.round(gpuStatus.gpus.reduce((sum, gpu) => sum + gpu.utilization, 0) / totalGPUs)
    : 0;
  const totalServices = services.length;
  const runningServices = services.filter(s => s.status === 'serving').length;
  const totalContainers = containers.length;
  const runningContainers = containers.filter(c => c.state === 'running').length;

  // 사용률 색상
  const getUtilizationColor = (utilization) => {
    if (utilization >= 90) return '#ff4d4f';
    if (utilization >= 70) return '#faad14';
    if (utilization >= 50) return '#52c41a';
    return '#1890ff';
  };

  return (
    <div className="system-status-page">
      <div className="page-header">
        <h1>📊 시스템 배포 현황</h1>
        <button className="btn-secondary" onClick={fetchSystemStatus} disabled={loading}>
          🔄 새로고침
        </button>
      </div>

      {/* 통계 카드 */}
      <div className="stats-grid-4">
        <div className="stat-card">
          <div className="stat-icon">🚀</div>
          <div className="stat-content">
            <div className="stat-label">vLLM 서비스</div>
            <div className="stat-value">
              {runningServices} <span className="stat-suffix">/ {totalServices}</span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🐳</div>
          <div className="stat-content">
            <div className="stat-label">Docker 컨테이너</div>
            <div className="stat-value">
              {runningContainers} <span className="stat-suffix">/ {totalContainers}</span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <div className="stat-label">GPU 사용 중</div>
            <div className="stat-value">
              {activeGPUs} <span className="stat-suffix">/ {totalGPUs}</span>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-label">평균 GPU 사용률</div>
            <div className="stat-value">{avgUtilization}%</div>
          </div>
        </div>
      </div>

      {/* 실행 중인 서비스 */}
      <div className="services-section">
        <h2>🎯 실행 중인 서비스</h2>
        {services.length === 0 ? (
          <div className="empty-state">실행 중인 서비스가 없습니다</div>
        ) : (
          <div className="services-grid">
            {services.map(service => (
              <div key={service.tag} className="service-item">
                <div className="service-header">
                  <div>
                    <h3>{service.model}</h3>
                    <span className="service-port">포트 {service.port}</span>
                  </div>
                  <span className={`status-badge ${service.status}`}>
                    {service.status === 'serving' ? '● 실행 중' : '○ 중지'}
                  </span>
                </div>
                <div className="service-info">
                  <div className="info-row">
                    <span className="info-label">서비스명:</span>
                    <span className="info-value">{service.name}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">엔드포인트:</span>
                    <span className="info-value">{service.endpoint_url}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Docker 컨테이너 */}
      <div className="containers-section">
        <h2>🐳 Docker 컨테이너</h2>
        {containers.length === 0 ? (
          <div className="empty-state">실행 중인 컨테이너가 없습니다</div>
        ) : (
          <div className="containers-list">
            {containers.map(container => (
              <div key={container.id} className="container-item">
                <div className="container-header">
                  <div>
                    <h4>{container.name}</h4>
                    <span className="container-id">ID: {container.id}</span>
                  </div>
                  <span className={`status-badge ${container.state}`}>
                    {container.state === 'running' ? '● 실행 중' : '○ 중지'}
                  </span>
                </div>
                <div className="container-info">
                  <div className="info-row">
                    <span className="info-label">이미지:</span>
                    <span className="info-value">{container.image}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">상태:</span>
                    <span className="info-value">{container.status}</span>
                  </div>
                  {container.ports && (
                    <div className="info-row">
                      <span className="info-label">포트:</span>
                      <span className="info-value">{container.ports}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* GPU 상세 현황 */}
      <div className="gpu-details-card">
        <h2>⚡ GPU 상세 현황</h2>

        {loading && !gpuStatus ? (
          <div className="loading">로딩 중...</div>
        ) : (
          <div className="gpu-list">
            {gpuStatus?.gpus?.map(gpu => (
              <div key={gpu.id} className="gpu-item">
                <div className="gpu-header">
                  <div className="gpu-title">
                    <span className="gpu-id">GPU {gpu.id}</span>
                    <span className="gpu-model">{gpu.name}</span>
                  </div>
                  <div className="gpu-utilization-badge">
                    {gpu.utilization}%
                  </div>
                </div>

                <div className="gpu-progress">
                  <div
                    className="gpu-progress-bar"
                    style={{
                      width: `${gpu.utilization}%`,
                      backgroundColor: getUtilizationColor(gpu.utilization)
                    }}
                  />
                </div>

                <div className="gpu-info">
                  <div className="info-item">
                    <span className="info-label">메모리</span>
                    <span className="info-value">{gpu.memory_used}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">상태</span>
                    <span
                      className="status-indicator"
                      style={{
                        backgroundColor: gpu.utilization > 10 ? '#52c41a' : '#d9d9d9'
                      }}
                    >
                      {gpu.utilization > 10 ? '활성' : '유휴'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && (!gpuStatus?.gpus || gpuStatus.gpus.length === 0) && (
          <div className="empty-state">GPU 정보를 찾을 수 없습니다</div>
        )}
      </div>

      {/* 범례 */}
      <div className="legend-card">
        <h3>사용률 범례</h3>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#1890ff' }}></div>
            <span>0-49%: 낮음</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#52c41a' }}></div>
            <span>50-69%: 정상</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#faad14' }}></div>
            <span>70-89%: 높음</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ff4d4f' }}></div>
            <span>90-100%: 위험</span>
          </div>
        </div>
      </div>
    </div>
  );
}
