/**
 * 모델 배포 관리 페이지
 * 모델 레지스트리 및 배포 관리
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import './ModelManagement.css';

const API_BASE_URL = 'http://localhost:8010/api/v1/admin';

export default function ModelManagement() {
  const [deployments, setDeployments] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [formData, setFormData] = useState({
    model_name: '',
    gpu_ids: [],
    port: 8000,
  });

  // 배포 목록 조회
  const fetchDeployments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/deployment/models`);
      setDeployments(response.data);
    } catch (error) {
      console.error('Failed to fetch deployments:', error);
      alert('배포 목록 조회 실패');
    } finally {
      setLoading(false);
    }
  };

  // 사용 가능한 모델 목록 조회
  const fetchAvailableModels = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/deployment/models/available`);
      setAvailableModels(response.data);
    } catch (error) {
      console.error('Failed to fetch available models:', error);
      // 실패 시 빈 배열 유지
    }
  };

  useEffect(() => {
    fetchDeployments();
    fetchAvailableModels();

    // 5초마다 배포 목록 자동 새로고침
    const interval = setInterval(fetchDeployments, 5000);
    return () => clearInterval(interval);
  }, []);

  // 모델 배포
  const handleDeploy = async (e) => {
    e.preventDefault();

    if (!formData.model_name || formData.gpu_ids.length === 0) {
      alert('모델 이름과 GPU를 선택하세요');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/deployment/models/deploy`, {
        model_name: formData.model_name,
        gpu_ids: formData.gpu_ids,
        port: parseInt(formData.port),
        vllm_config: {
          gpu_memory_utilization: 0.9,
          max_model_len: 8192
        }
      });

      alert('모델 배포 시작');
      setShowDeployModal(false);
      setFormData({ model_name: '', gpu_ids: [], port: 8000 });
      await fetchDeployments();
    } catch (error) {
      console.error('Failed to deploy model:', error);
      alert('배포 실패: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 배포 중지
  const handleStop = async (deploymentId) => {
    if (!window.confirm('이 모델의 배포를 중지하시겠습니까?')) {
      return;
    }

    try {
      await axios.post(`${API_BASE_URL}/deployment/models/${deploymentId}/stop`);
      alert('배포 중지 완료');
      await fetchDeployments();
    } catch (error) {
      console.error('Failed to stop deployment:', error);
      alert('배포 중지 실패');
    }
  };

  // 배포 시작 (재시작)
  const handleStart = async (deploymentId) => {
    try {
      await axios.post(`${API_BASE_URL}/deployment/models/${deploymentId}/start`);
      alert('배포 시작 완료');
      await fetchDeployments();
    } catch (error) {
      console.error('Failed to start deployment:', error);
      alert('배포 시작 실패');
    }
  };

  // Health Check
  const handleHealthCheck = async (deploymentId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/deployment/models/${deploymentId}/health`);
      const { healthy, response_time_ms } = response.data;

      if (healthy) {
        alert(`✅ 정상 (응답 시간: ${response_time_ms}ms)`);
      } else {
        alert('❌ 비정상');
      }
    } catch (error) {
      alert('❌ Health Check 실패');
    }
  };

  // GPU 선택 토글
  const toggleGPU = (gpuId) => {
    setFormData(prev => ({
      ...prev,
      gpu_ids: prev.gpu_ids.includes(gpuId)
        ? prev.gpu_ids.filter(id => id !== gpuId)
        : [...prev.gpu_ids, gpuId]
    }));
  };

  // 상태별 색상
  const getStatusColor = (status) => {
    const colors = {
      'serving': '#52c41a',
      'deploying': '#1890ff',
      'stopped': '#d9d9d9',
      'failed': '#ff4d4f',
    };
    return colors[status] || '#d9d9d9';
  };

  // 상태별 텍스트
  const getStatusText = (status) => {
    const texts = {
      'serving': '서빙 중',
      'deploying': '배포 중',
      'stopped': '중지됨',
      'failed': '실패',
    };
    return texts[status] || status;
  };

  return (
    <div className="model-management-page">
      <div className="page-header">
        <h1>📦 모델 레지스트리</h1>
        <div className="header-actions">
          <button className="btn-secondary" onClick={fetchDeployments} disabled={loading}>
            🔄 새로고침
          </button>
          <button className="btn-primary" onClick={() => setShowDeployModal(true)}>
            ➕ 모델 배포
          </button>
        </div>
      </div>

      <div className="deployments-table-container">
        {loading && deployments.length === 0 ? (
          <div className="loading">로딩 중...</div>
        ) : (
          <table className="deployments-table">
            <thead>
              <tr>
                <th>배포 ID</th>
                <th>모델 이름</th>
                <th>상태</th>
                <th>GPU</th>
                <th>포트</th>
                <th>엔드포인트</th>
                <th>생성일시</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {deployments.map(deployment => (
                <tr key={deployment.deployment_id}>
                  <td>{deployment.deployment_id}</td>
                  <td><strong>{deployment.model_name}</strong></td>
                  <td>
                    <span
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(deployment.status) }}
                    >
                      {getStatusText(deployment.status)}
                    </span>
                  </td>
                  <td>
                    {deployment.gpu_ids?.map(id => (
                      <span key={id} className="gpu-badge">GPU {id}</span>
                    ))}
                  </td>
                  <td>{deployment.port || '-'}</td>
                  <td>
                    {deployment.endpoint_url ? (
                      <a href={deployment.endpoint_url} target="_blank" rel="noopener noreferrer">
                        {deployment.endpoint_url}
                      </a>
                    ) : '-'}
                  </td>
                  <td>{new Date(deployment.created_at).toLocaleString('ko-KR')}</td>
                  <td>
                    <div className="action-buttons">
                      {deployment.status === 'serving' ? (
                        <button
                          className="btn-danger-small"
                          onClick={() => handleStop(deployment.deployment_id)}
                        >
                          ⏸️ 중지
                        </button>
                      ) : deployment.status === 'stopped' ? (
                        <button
                          className="btn-success-small"
                          onClick={() => handleStart(deployment.deployment_id)}
                        >
                          ▶️ 시작
                        </button>
                      ) : null}

                      <button
                        className="btn-secondary-small"
                        onClick={() => handleHealthCheck(deployment.deployment_id)}
                      >
                        🏥 Health
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && deployments.length === 0 && (
          <div className="empty-state">배포된 모델이 없습니다</div>
        )}
      </div>

      {/* 모델 배포 Modal */}
      {showDeployModal && (
        <div className="modal-overlay" onClick={() => setShowDeployModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>모델 배포</h2>
              <button className="close-btn" onClick={() => setShowDeployModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleDeploy}>
              <div className="form-group">
                <label>모델 선택 *</label>
                <select
                  value={formData.model_name}
                  onChange={e => setFormData({ ...formData, model_name: e.target.value })}
                  required
                >
                  <option value="">모델을 선택하세요</option>
                  {availableModels.map(model => (
                    <option key={model.value} value={model.value}>
                      {model.label} ({model.type})
                    </option>
                  ))}
                </select>
                {availableModels.length === 0 && (
                  <small style={{ color: '#999', marginTop: '4px' }}>
                    사용 가능한 모델을 불러오는 중...
                  </small>
                )}
              </div>

              <div className="form-group">
                <label>사용할 GPU * (최소 1개 선택)</label>
                <div className="gpu-selector">
                  {[0, 1, 2, 3, 4, 5, 6, 7].map(gpuId => (
                    <label key={gpuId} className="gpu-checkbox">
                      <input
                        type="checkbox"
                        checked={formData.gpu_ids.includes(gpuId)}
                        onChange={() => toggleGPU(gpuId)}
                      />
                      GPU {gpuId}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>포트 *</label>
                <input
                  type="number"
                  value={formData.port}
                  onChange={e => setFormData({ ...formData, port: e.target.value })}
                  min="8000"
                  max="9999"
                  required
                />
              </div>

              <div className="modal-footer">
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? '배포 중...' : '배포 시작'}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowDeployModal(false)}
                >
                  취소
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
