/**
 * 사용자 관리 페이지 (완전 개편)
 * - 탭 2개: 사용자 관리, 접근승인관리
 * - 고급 필터, 소트, 권한/모델 토글, 통계 모달
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Checkbox,
  Pagination,
  Typography,
  IconButton,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  LinearProgress,
  CircularProgress,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import BarChartIcon from '@mui/icons-material/BarChart';
import * as XLSX from 'xlsx';
import axios from '../axiosConfig';

// dayjs 한국어 설정
dayjs.locale('ko');

// API Base
const API_BASE = '/api/v1/admin';

// TableSortLabel 스타일 (클릭 시 텍스트 사라지는 버그 수정)
const sortLabelStyle = {
  '&.MuiTableSortLabel-root': {
    color: 'inherit',
  },
  '&.MuiTableSortLabel-root.Mui-active': {
    color: 'inherit',
  },
  '& .MuiTableSortLabel-icon': {
    color: 'inherit !important',
  },
};

/**
 * 날짜 포맷팅
 */
function formatDateTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 미접속 일수 계산 (숫자 반환)
 */
function getInactiveDays(lastLogin) {
  if (!lastLogin) return null;
  const now = new Date();
  const last = new Date(lastLogin);
  const days = Math.floor((now - last) / (1000 * 60 * 60 * 24));
  return days;
}

/**
 * 미접속 시간 계산 (문자열 반환)
 */
function calculateInactiveDays(lastLogin) {
  if (!lastLogin) return '접속 이력 없음';
  const days = getInactiveDays(lastLogin);
  return `${days}일`;
}

/**
 * 부서명 파싱 (본부와 부/처 분리)
 * 예: "서울경기본부 기술처" => { headquarters: "서울경기본부", division: "기술처" }
 */
function parseDepartmentName(departmentName) {
  if (!departmentName) return { headquarters: '-', division: '-' };

  const parts = departmentName.split(' ');
  if (parts.length >= 2) {
    return {
      headquarters: parts[0],
      division: parts.slice(1).join(' ')
    };
  }
  return {
    headquarters: departmentName,
    division: '-'
  };
}

/**
 * 사용자 관리 페이지
 */
export default function UsersPage() {
  // 탭 상태
  const [tabValue, setTabValue] = useState(0);

  // 필터 상태
  const [searchType, setSearchType] = useState('전체');
  const [searchText, setSearchText] = useState('');
  const [accessFilter, setAccessFilter] = useState('전체');
  const [modelFilter, setModelFilter] = useState('전체');
  const [longInactive, setLongInactive] = useState(false);

  // 테이블 상태
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [orderBy, setOrderBy] = useState('id');
  const [order, setOrder] = useState('asc');

  // 선택 상태
  const [selected, setSelected] = useState([]);

  // 모달 상태
  const [alertOpen, setAlertOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [statsOpen, setStatsOpen] = useState(false);
  const [departmentStats, setDepartmentStats] = useState([]);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState('');
  const [currentApprovalUser, setCurrentApprovalUser] = useState(null);

  // 권한 변경 이력 탭 상태
  const [history, setHistory] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyRowsPerPage, setHistoryRowsPerPage] = useState(20);
  const [historyActionFilter, setHistoryActionFilter] = useState('전체');

  // 로딩 상태
  const [isLoading, setIsLoading] = useState(false);

  // 대량 작업 진행률
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkProgressMessage, setBulkProgressMessage] = useState('');
  const [showBulkProgress, setShowBulkProgress] = useState(false);

  /**
   * 사용자 목록 로드
   */
  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();

      // 장기 미접속 필터
      if (longInactive) {
        params.append('inactive_days', '90');
      }

      const response = await axios.get(`${API_BASE}/gpt-access/users?${params.toString()}`);

      let filteredUsers = response.data.users || [];

      // 프론트엔드에서 필터링
      // 검색 필터링
      if (searchText) {
        filteredUsers = filteredUsers.filter(user => {
          const searchLower = searchText.toLowerCase();

          // '전체' 선택 시 모든 필드에서 검색
          if (searchType === '전체') {
            return (
              user.employee_number?.toLowerCase().includes(searchLower) ||
              user.full_name?.toLowerCase().includes(searchLower) ||
              user.department_name?.toLowerCase().includes(searchLower) ||
              user.team?.toLowerCase().includes(searchLower) ||
              user.username?.toLowerCase().includes(searchLower) ||
              user.email?.toLowerCase().includes(searchLower)
            );
          }

          // 특정 필드 선택 시 해당 필드에서만 검색
          switch (searchType) {
            case '사번':
              return user.employee_number?.toLowerCase().includes(searchLower);
            case '이름':
              return user.full_name?.toLowerCase().includes(searchLower);
            case '본부':
              return user.department_name?.toLowerCase().includes(searchLower);
            case '부처':
              return user.department_name?.toLowerCase().includes(searchLower);
            case '팀':
              return user.team?.toLowerCase().includes(searchLower);
            default:
              return false;
          }
        });
      }

      // 권한 필터링
      if (accessFilter !== '전체') {
        filteredUsers = filteredUsers.filter(user =>
          accessFilter === 'Y' ? user.gpt_access_granted : !user.gpt_access_granted
        );
      }

      // 모델 필터링
      if (modelFilter !== '전체') {
        filteredUsers = filteredUsers.filter(user => user.allowed_model === modelFilter);
      }

      // 프론트엔드에서 정렬
      filteredUsers.sort((a, b) => {
        let aVal = a[orderBy] || '';
        let bVal = b[orderBy] || '';
        if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase();
          bVal = bVal.toLowerCase();
        }
        if (order === 'asc') {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });

      setTotal(filteredUsers.length);

      // 프론트엔드 페이지네이션
      const startIdx = (page - 1) * rowsPerPage;
      const endIdx = startIdx + rowsPerPage;
      setUsers(filteredUsers.slice(startIdx, endIdx));

    } catch (error) {
      console.error('사용자 목록 로드 실패:', error);
      // Fallback to mock data on error
      const mockUsers = generateMockUsers(20);
      setUsers(mockUsers);
      setTotal(100);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (tabValue === 0) {
      loadUsers();
    }
  }, [tabValue, page, rowsPerPage, orderBy, order, searchText, searchType, accessFilter, modelFilter, longInactive]);

  useEffect(() => {
    if (tabValue === 1) {
      loadHistory();
    }
  }, [tabValue, historyPage, historyRowsPerPage, historyActionFilter]);

  /**
   * 권한 변경 이력 로드
   */
  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();

      // 액션 필터
      if (historyActionFilter !== '전체') {
        params.append('action', historyActionFilter);
      }

      // 조회 개수 제한
      params.append('limit', '1000');

      const response = await axios.get(`${API_BASE}/gpt-access/history?${params.toString()}`);
      const historyData = response.data.history || [];

      setHistoryTotal(historyData.length);

      // 프론트엔드 페이징
      const startIdx = (historyPage - 1) * historyRowsPerPage;
      const endIdx = startIdx + historyRowsPerPage;

      setHistory(historyData.slice(startIdx, endIdx));
    } catch (error) {
      console.error('[권한 변경 이력] API 호출 실패:', error);
      setAlertMessage(`권한 변경 이력 로드 실패: ${error.response?.data?.detail || error.message}`);
      setAlertOpen(true);
      setHistory([]);
      setHistoryTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 검색
   */
  const handleSearch = () => {
    setPage(1);
    loadUsers();
  };

  /**
   * 초기화
   */
  const handleReset = () => {
    setSearchType('전체');
    setSearchText('');
    setAccessFilter('전체');
    setModelFilter('전체');
    setLongInactive(false);
    setPage(1);
    loadUsers();
  };

  /**
   * 현재 페이지 전체 선택
   */
  const handleSelectAllFiltered = () => {
    const allIds = users.map(user => user.id);
    setSelected(allIds);
  };

  /**
   * 권한 변경 이력 필터 초기화
   */
  const handleHistoryReset = () => {
    setHistoryActionFilter('전체');
    setHistoryPage(1);
    loadHistory();
  };

  /**
   * 소트
   */
  const handleSort = (column) => {
    const isAsc = orderBy === column && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(column);
  };

  /**
   * 전체 선택/해제
   */
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(users.map((user) => user.id));
    } else {
      setSelected([]);
    }
  };

  /**
   * 개별 선택/해제
   */
  const handleSelect = (id) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    setSelected(newSelected);
  };

  /**
   * 권한 토글
   */
  const handleAccessToggle = async (userId, currentAccess) => {
    try {
      if (currentAccess) {
        // 권한 회수
        await axios.post(`${API_BASE}/gpt-access/revoke`, {
          user_ids: [userId]
        });
      } else {
        // 권한 부여 - 모델 선택 모달 표시
        setCurrentApprovalUser([userId]);
        setSelectedModel('');
        setApprovalModalOpen(true);
        return;
      }
      loadUsers();
    } catch (error) {
      console.error('권한 변경 실패:', error);
      setAlertMessage('권한 변경에 실패했습니다');
      setAlertOpen(true);
    }
  };

  /**
   * 모델 변경
   */
  const handleModelChange = async (userId, model) => {
    try {
      await axios.post(`${API_BASE}/gpt-access/grant`, {
        user_ids: [userId],
        model: model
      });
      loadUsers();
    } catch (error) {
      console.error('모델 변경 실패:', error);
      setAlertMessage('모델 변경에 실패했습니다');
      setAlertOpen(true);
    }
  };

  /**
   * 권한 회수 (대량 작업 with 진행률)
   */
  const handleRevokeAccess = async () => {
    if (selected.length === 0) {
      setAlertMessage('선택 후 버튼을 클릭해주세요');
      setAlertOpen(true);
      return;
    }

    const confirmRevoke = window.confirm(
      `선택된 ${selected.length}명의 GPT 접근 권한을 회수하시겠습니까?`
    );

    if (!confirmRevoke) return;

    try {
      setShowBulkProgress(true);
      setBulkProgress(0);
      setBulkProgressMessage(`${selected.length}명의 권한을 회수하는 중...`);

      await axios.post(`${API_BASE}/gpt-access/revoke`, {
        user_ids: selected
      });

      setBulkProgress(100);
      setBulkProgressMessage('권한 회수 완료!');

      setTimeout(() => {
        setShowBulkProgress(false);
        setAlertMessage(`${selected.length}명의 권한이 회수되었습니다`);
        setAlertOpen(true);
        setSelected([]);
        loadUsers();
      }, 1500);
    } catch (error) {
      console.error('권한 회수 실패:', error);
      setShowBulkProgress(false);
      setAlertMessage('권한 회수에 실패했습니다: ' + (error.response?.data?.detail || error.message));
      setAlertOpen(true);
    }
  };

  /**
   * 권한 부여 (모델 선택 모달 표시)
   */
  const handleGrantAccess = async () => {
    if (selected.length === 0) {
      setAlertMessage('선택 후 버튼을 클릭해주세요');
      setAlertOpen(true);
      return;
    }
    // 모델 선택을 위한 모달 표시
    setCurrentApprovalUser(selected);
    setSelectedModel('');
    setApprovalModalOpen(true);
  };

  /**
   * 권한통계보기
   */
  const handleShowStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/gpt-access/stats/departments`);
      const departments = response.data.departments || [];
      const statsData = departments.map(dept => ({
        id: dept.id,
        team: dept.name,
        count: dept.users_with_gpt_access
      }));
      setDepartmentStats(statsData);
      setStatsOpen(true);
    } catch (error) {
      console.error('통계 로드 실패:', error);
      setAlertMessage('통계 조회에 실패했습니다');
      setAlertOpen(true);
    }
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = () => {
    const excelData = users.map((user, index) => {
      const { headquarters, division } = parseDepartmentName(user.department_name);
      return {
        번호: (page - 1) * rowsPerPage + index + 1,
        본부: headquarters,
        '부/처': division,
        팀: user.team || '-',
        직종: user.job_category || '-',
        직급: user.position || '-',
        직위: user.rank || '-',
        사번: user.employee_number || '-',
        이름: user.full_name || '-',
        최종접속일: formatDateTime(user.last_login_at),
        미접속시간: calculateInactiveDays(user.last_login_at),
        권한: user.gpt_access_granted ? 'Y' : 'N',
        모델선택: user.allowed_model || '-',
      };
    });

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '사용자목록');
    XLSX.writeFile(wb, `사용자목록_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };


  /**
   * 모델 할당 확인
   */
  const handleConfirmApproval = async () => {
    if (!selectedModel) {
      alert('모델을 선택해주세요');
      return;
    }

    try {
      setApprovalModalOpen(false);
      setShowBulkProgress(true);
      setBulkProgress(0);
      setBulkProgressMessage(`${currentApprovalUser.length}명에게 ${selectedModel} 모델을 할당하는 중...`);

      await axios.post(`${API_BASE}/gpt-access/grant`, {
        user_ids: currentApprovalUser,
        model: selectedModel
      });

      setBulkProgress(100);
      setBulkProgressMessage('모델 할당 완료!');

      setTimeout(() => {
        setShowBulkProgress(false);
        setAlertMessage(`${currentApprovalUser.length}명에게 ${selectedModel} 모델이 할당되었습니다`);
        setAlertOpen(true);
        setSelected([]);
        setSelectedRequests([]);

        if (tabValue === 0) {
          loadUsers();
        } else {
          loadHistory();  // Tab 1은 이제 권한 변경 이력
        }
      }, 1500);

      setCurrentApprovalUser(null);
      setSelectedModel('');
    } catch (error) {
      console.error('모델 할당 실패:', error);
      setShowBulkProgress(false);
      setAlertMessage('모델 할당에 실패했습니다: ' + (error.response?.data?.detail || error.message));
      setAlertOpen(true);
    }
  };

  /**
   * 권한 변경 이력 엑셀 다운로드
   */
  const handleDownloadHistoryExcel = () => {
    const excelData = history.map((record, index) => {
      const actionText = {
        'grant': '권한 부여',
        'revoke': '권한 회수',
        'model_change': '모델 변경',
        'approve': '승인',
        'reject': '거부'
      }[record.action] || record.action;

      return {
        번호: (historyPage - 1) * historyRowsPerPage + index + 1,
        사번: record.employee_number || '-',
        이름: record.full_name || '-',
        부서: record.department_name || '-',
        액션: actionText,
        이전값: record.old_value || '-',
        새값: record.new_value || '-',
        변경일시: formatDateTime(record.changed_at),
        관리자: record.admin_name || '-',
        사유: record.reason || '-'
      };
    });

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '권한변경이력');
    XLSX.writeFile(wb, `권한변경이력_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  /**
   * 통계 엑셀 다운로드
   */
  const handleDownloadStatsExcel = () => {
    const excelData = departmentStats.map((stat, index) => ({
      번호: index + 1,
      팀: stat.team,
      인원: stat.count,
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '부서별통계');
    XLSX.writeFile(wb, `부서별사용자통계_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* 헤더 */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        👥 사용자 관리
      </Typography>

      {/* 탭 */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="사용자 관리" />
          <Tab label="권한 변경 이력" />
        </Tabs>
      </Paper>

      {/* 탭 1: 사용자 관리 */}
      {tabValue === 0 && (
        <>
          {/* 빠른 필터 단축버튼 */}
          <Paper elevation={2} sx={{ p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              빠른 필터
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant={accessFilter === 'N' ? 'contained' : 'outlined'}
                size="small"
                onClick={() => {
                  setAccessFilter('N');
                  setPage(1);
                }}
              >
                권한 없는 사용자
              </Button>
              <Button
                variant={longInactive ? 'contained' : 'outlined'}
                size="small"
                onClick={() => {
                  setLongInactive(!longInactive);
                  setPage(1);
                }}
              >
                장기 미접속자 (90일+)
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setAccessFilter('N');
                  setLongInactive(true);
                  setPage(1);
                }}
              >
                권한 없는 + 미접속자
              </Button>
              <Button
                variant="outlined"
                size="small"
                color="secondary"
                onClick={handleReset}
              >
                필터 초기화
              </Button>
            </Box>
          </Paper>

          {/* 검색 필터 */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              {/* 검색 유형 */}
              <Select
                size="small"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                sx={{ minWidth: 120 }}
              >
                <MenuItem value="전체">전체</MenuItem>
                <MenuItem value="사번">사번</MenuItem>
                <MenuItem value="이름">이름</MenuItem>
                <MenuItem value="본부">본부</MenuItem>
                <MenuItem value="부/처">부/처</MenuItem>
                <MenuItem value="팀">팀</MenuItem>
              </Select>

              {/* 검색어 */}
              <TextField
                size="small"
                placeholder="검색어 입력"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                sx={{ minWidth: 200 }}
              />

              {/* 권한 필터 */}
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>권한</Typography>
              <Select
                size="small"
                value={accessFilter}
                onChange={(e) => setAccessFilter(e.target.value)}
                sx={{ minWidth: 100 }}
              >
                <MenuItem value="전체">전체</MenuItem>
                <MenuItem value="Y">Y</MenuItem>
                <MenuItem value="N">N</MenuItem>
              </Select>

              {/* 모델 필터 */}
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>모델</Typography>
              <Select
                size="small"
                value={modelFilter}
                onChange={(e) => setModelFilter(e.target.value)}
                sx={{ minWidth: 140 }}
              >
                <MenuItem value="전체">전체</MenuItem>
                <MenuItem value="Qwen235B">Qwen235B</MenuItem>
                <MenuItem value="Qwen32B">Qwen32B</MenuItem>
              </Select>

              {/* 장기미접속자 */}
              <FormControlLabel
                control={<Checkbox checked={longInactive} onChange={(e) => setLongInactive(e.target.checked)} />}
                label="장기미접속자"
              />

              {/* 검색/초기화 */}
              <Button variant="contained" startIcon={<SearchIcon />} onClick={handleSearch}>
                검색
              </Button>
              <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleReset}>
                초기화
              </Button>
            </Box>
          </Paper>

          {/* 선택 요약 및 대량 작업 */}
          {selected.length > 0 && (
            <Paper elevation={3} sx={{ p: 2, mb: 2, backgroundColor: '#e3f2fd' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <Typography variant="h6" color="primary">
                    {selected.length}명 선택됨
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSelected([])}
                  >
                    선택 해제
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleGrantAccess}
                    disabled={selected.length === 0}
                  >
                    선택된 {selected.length}명에게 권한 부여
                  </Button>
                  <Button
                    variant="contained"
                    color="error"
                    onClick={handleRevokeAccess}
                    disabled={selected.length === 0}
                  >
                    선택된 {selected.length}명 권한 회수
                  </Button>
                </Box>
              </Box>
            </Paper>
          )}

          {/* 테이블 상단 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Typography variant="body2">
                총 <strong>{total.toLocaleString()}</strong>건
              </Typography>
              <Select
                size="small"
                value={rowsPerPage}
                onChange={(e) => {
                  setRowsPerPage(e.target.value);
                  setPage(1);
                }}
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={30}>30</MenuItem>
                <MenuItem value={40}>40</MenuItem>
                <MenuItem value={50}>50</MenuItem>
              </Select>
              {/* 필터된 전체 선택 버튼 */}
              <Button
                variant="outlined"
                size="small"
                onClick={handleSelectAllFiltered}
                disabled={users.length === 0}
              >
                현재 페이지 전체 선택 ({users.length}명)
              </Button>
            </Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadExcel}
            >
              엑셀 다운로드
            </Button>
          </Box>

          {/* 테이블 */}
          <TableContainer
            component={Paper}
            elevation={3}
            sx={{
              minHeight: '400px',
              maxHeight: '70vh',
              overflow: 'auto',
              position: 'relative'
            }}
          >
            <Table sx={{ minWidth: 1400 }}>
              <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={users.length > 0 && selected.length === users.length}
                      indeterminate={selected.length > 0 && selected.length < users.length}
                      onChange={handleSelectAll}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'id'}
                      direction={orderBy === 'id' ? order : 'asc'}
                      onClick={() => handleSort('id')}
                      sx={sortLabelStyle}
                    >
                      번호
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'headquarters'}
                      direction={orderBy === 'headquarters' ? order : 'asc'}
                      onClick={() => handleSort('headquarters')}
                      sx={sortLabelStyle}
                    >
                      본부
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'division'}
                      direction={orderBy === 'division' ? order : 'asc'}
                      onClick={() => handleSort('division')}
                    >
                      부/처
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'team'}
                      direction={orderBy === 'team' ? order : 'asc'}
                      onClick={() => handleSort('team')}
                    >
                      팀
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'job_category'}
                      direction={orderBy === 'job_category' ? order : 'asc'}
                      onClick={() => handleSort('job_category')}
                    >
                      직종
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'position'}
                      direction={orderBy === 'position' ? order : 'asc'}
                      onClick={() => handleSort('position')}
                    >
                      직급
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'rank'}
                      direction={orderBy === 'rank' ? order : 'asc'}
                      onClick={() => handleSort('rank')}
                    >
                      직위
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'employee_number'}
                      direction={orderBy === 'employee_number' ? order : 'asc'}
                      onClick={() => handleSort('employee_number')}
                    >
                      사번
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'full_name'}
                      direction={orderBy === 'full_name' ? order : 'asc'}
                      onClick={() => handleSort('full_name')}
                    >
                      이름
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      sx={sortLabelStyle}
                      active={orderBy === 'last_login_at'}
                      direction={orderBy === 'last_login_at' ? order : 'asc'}
                      onClick={() => handleSort('last_login_at')}
                    >
                      최종접속일
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'last_login_at'}
                      direction={orderBy === 'last_login_at' ? order : 'asc'}
                      onClick={() => handleSort('last_login_at')}
                      sx={sortLabelStyle}
                    >
                      미접속시간
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>권한</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>모델선택</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user, index) => {
                  const isSelected = selected.indexOf(user.id) !== -1;
                  const { headquarters, division } = parseDepartmentName(user.department_name);
                  const inactiveDays = getInactiveDays(user.last_login_at);
                  const isLongInactive = inactiveDays !== null && inactiveDays > 30; // 31일부터 빨간색

                  return (
                    <TableRow key={user.id} hover selected={isSelected}>
                      <TableCell padding="checkbox">
                        <Checkbox checked={isSelected} onChange={() => handleSelect(user.id)} />
                      </TableCell>
                      <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                      <TableCell>{headquarters}</TableCell>
                      <TableCell>{division}</TableCell>
                      <TableCell>{user.team || '-'}</TableCell>
                      <TableCell>{user.job_category || '-'}</TableCell>
                      <TableCell>{user.position || '-'}</TableCell>
                      <TableCell>{user.rank || '-'}</TableCell>
                      <TableCell>{user.employee_number || '-'}</TableCell>
                      <TableCell>{user.full_name || '-'}</TableCell>
                      <TableCell>{formatDateTime(user.last_login_at)}</TableCell>
                      <TableCell
                        sx={{
                          color: isLongInactive ? '#d32f2f' : 'inherit',
                          fontWeight: isLongInactive ? 'bold' : 'normal'
                        }}
                      >
                        {calculateInactiveDays(user.last_login_at)}
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={user.gpt_access_granted || false}
                          onChange={() => handleAccessToggle(user.id, user.gpt_access_granted)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Select
                          size="small"
                          value={user.allowed_model || ''}
                          onChange={(e) => handleModelChange(user.id, e.target.value)}
                          sx={{ minWidth: 120 }}
                        >
                          <MenuItem value="">미선택</MenuItem>
                          <MenuItem value="Qwen235B">Qwen235B</MenuItem>
                          <MenuItem value="Qwen32B">Qwen32B</MenuItem>
                        </Select>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={14} align="center" sx={{ py: 4 }}>
                      데이터가 없습니다.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* 페이지네이션 및 통계 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
            <Button variant="outlined" onClick={handleShowStats} startIcon={<BarChartIcon />}>
              권한통계보기
            </Button>
            <Box />
          </Box>

          {/* 페이지네이션 */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={Math.ceil(total / rowsPerPage)}
              page={page}
              onChange={(e, value) => setPage(value)}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        </>
      )}

      {/* 탭 2: 권한 변경 이력 */}
      {tabValue === 1 && (
        <>
          {/* 필터 */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>액션 필터</Typography>
              <Select
                size="small"
                value={historyActionFilter}
                onChange={(e) => setHistoryActionFilter(e.target.value)}
                sx={{ minWidth: 150 }}
              >
                <MenuItem value="전체">전체</MenuItem>
                <MenuItem value="grant">권한 부여</MenuItem>
                <MenuItem value="revoke">권한 회수</MenuItem>
                <MenuItem value="model_change">모델 변경</MenuItem>
              </Select>
              <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleHistoryReset}>
                초기화
              </Button>
            </Box>
          </Paper>

          {/* 테이블 상단 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Typography variant="body2">
                총 <strong>{historyTotal.toLocaleString()}</strong>건
              </Typography>
              <Select
                size="small"
                value={historyRowsPerPage}
                onChange={(e) => {
                  setHistoryRowsPerPage(e.target.value);
                  setHistoryPage(1);
                }}
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={30}>30</MenuItem>
                <MenuItem value={40}>40</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
              </Select>
            </Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadHistoryExcel}
            >
              엑셀 다운로드
            </Button>
          </Box>

          {/* 테이블 */}
          <TableContainer
            component={Paper}
            elevation={3}
            sx={{
              minHeight: '400px',
              maxHeight: '70vh',
              overflow: 'auto',
              position: 'relative'
            }}
          >
            <Table sx={{ minWidth: 1000 }}>
              <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>사번</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>이름</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>부서</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>액션</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>이전값</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>새값</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>변경일시</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>관리자</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>사유</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((record, index) => {
                  const actionText = {
                    'grant': '권한 부여',
                    'revoke': '권한 회수',
                    'model_change': '모델 변경',
                    'approve': '승인',
                    'reject': '거부'
                  }[record.action] || record.action;

                  const actionColor = {
                    'grant': '#28a745',
                    'revoke': '#dc3545',
                    'model_change': '#ffc107',
                    'approve': '#17a2b8',
                    'reject': '#6c757d'
                  }[record.action] || '#000';

                  return (
                    <TableRow key={record.id} hover>
                      <TableCell>{(historyPage - 1) * historyRowsPerPage + index + 1}</TableCell>
                      <TableCell>{record.employee_number || '-'}</TableCell>
                      <TableCell>{record.full_name || '-'}</TableCell>
                      <TableCell>{record.department_name || '-'}</TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            color: actionColor,
                            fontWeight: 'bold'
                          }}
                        >
                          {actionText}
                        </Typography>
                      </TableCell>
                      <TableCell>{record.old_value || '-'}</TableCell>
                      <TableCell>{record.new_value || '-'}</TableCell>
                      <TableCell>{formatDateTime(record.changed_at)}</TableCell>
                      <TableCell>{record.admin_name || '-'}</TableCell>
                      <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {record.reason || '-'}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {history.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                      {isLoading ? '로딩 중...' : '권한 변경 이력이 없습니다.'}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* 페이지네이션 */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={Math.ceil(historyTotal / historyRowsPerPage)}
              page={historyPage}
              onChange={(e, value) => setHistoryPage(value)}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        </>
      )}

      {/* 알림 모달 */}
      <Dialog open={alertOpen} onClose={() => setAlertOpen(false)}>
        <DialogTitle>알림</DialogTitle>
        <DialogContent>
          <Typography>{alertMessage}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertOpen(false)}>확인</Button>
        </DialogActions>
      </Dialog>

      {/* 모델 선택 모달 */}
      <Dialog
        open={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        PaperProps={{
          sx: {
            width: '400px',
            maxWidth: '90vw'
          }
        }}
      >
        <DialogTitle>LLM 모델 할당</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 3, mt: 2 }}>
            선택한 {currentApprovalUser?.length || 0}명에게 할당할 LLM 모델을 선택하세요.
          </Typography>
          <Select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            fullWidth
            displayEmpty
          >
            <MenuItem value="" disabled>모델을 선택하세요</MenuItem>
            <MenuItem value="Qwen235B">Qwen235B (235B 파라미터)</MenuItem>
            <MenuItem value="Qwen32B">Qwen32B (32B 파라미터)</MenuItem>
            <MenuItem value="70B">70B (기존 모델)</MenuItem>
          </Select>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            ℹ️ 선택한 모델이 실제로 답변을 생성합니다. 부서별로 다른 모델을 지정할 수 있습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalModalOpen(false)}>취소</Button>
          <Button onClick={handleConfirmApproval} variant="contained" color="primary">
            할당
          </Button>
        </DialogActions>
      </Dialog>

      {/* 권한통계보기 모달 */}
      <Dialog
        open={statsOpen}
        onClose={() => setStatsOpen(false)}
        PaperProps={{
          sx: {
            width: '450px',
            maxWidth: '90vw'
          }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">부서별 ex-GPT 권한 통계</Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadStatsExcel}
              size="small"
            >
              엑셀 다운로드
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold', width: '60px' }}>번호</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', width: '240px' }}>팀</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', width: '80px', textAlign: 'right' }}>인원</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {departmentStats.map((stat, index) => (
                  <TableRow key={stat.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>{stat.team}</TableCell>
                    <TableCell sx={{ textAlign: 'right' }}>{stat.count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatsOpen(false)} variant="contained">
            확인
          </Button>
        </DialogActions>
      </Dialog>

      {/* 대량 작업 진행률 모달 */}
      <Dialog
        open={showBulkProgress}
        onClose={() => {}}
        disableEscapeKeyDown
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>대량 작업 진행 중</DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
              {bulkProgressMessage}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={bulkProgress}
              sx={{ mt: 2, height: 10, borderRadius: 5 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {bulkProgress}% 완료
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

/**
 * Mock 데이터 생성 (개발용) - 사용자
 */
function generateMockUsers(count) {
  const mockUsers = [];

  // 실제 도로공사 조직 구조 기반 데이터
  const headquarters = [
    '서울경기본부', 'AI디지털본부', '홍보처', '건설본부', '기술본부',
    '영업본부', '강원본부', '충청본부', '전라본부', '경상본부'
  ];

  const divisions = [
    '기술처', '디지털관리처', '홍보계획부', '언론홍보부', '시설관리처',
    '건설관리처', '안전관리처', '기획처', '재무처', '인사처'
  ];

  const teams = [
    '시설부', '경영시스템부', '홍보계획 총괄', '디지털 소통', '건설기획부',
    '도로유지부', '시설안전부', '전기통신부', '교통관리부', '재무관리부'
  ];

  const jobCategories = [
    '전기', '정보통신', '토목', '건축', '기계', '사무직', '기술직', '안전관리', '경영지원'
  ];

  const ranks = ['3급', '4급', '5급', '6급', '7급', '8급'];

  const positions = ['본부장', '처장', '차장', '부장', '대리', '주임', '사원'];

  const koreanNames = [
    '박지영', '김영복', '이민수', '최서연', '정동훈', '강미경', '조현우', '윤지혜',
    '임재현', '한소영', '송민호', '배수진', '오태양', '신예원', '권혁진', '홍지우',
    '장민석', '유하늘', '노승현', '문채원', '서준혁', '안다은', '황재민', '구민지',
    '남궁현', '선우진', '독고영', '황보람', '제갈량', '사공민', '석우성', '탁재훈',
    '진다혜', '표지민', '국하늘', '감우리', '변수아', '복예나', '목준서', '빈지원'
  ];

  const models = ['70B', 'Qwen235B', 'Qwen32B'];

  for (let i = 1; i <= count; i++) {
    const hq = headquarters[i % headquarters.length];
    const div = divisions[i % divisions.length];
    const fullDivision = `${hq} ${div}`;

    // 미접속 기간 설정 (일부는 90일 이상으로 설정)
    let daysAgo;
    if (i % 7 === 0) {
      // 약 14% 사용자는 90일 이상 미접속
      daysAgo = 90 + Math.floor(Math.random() * 100);
    } else if (i % 5 === 0) {
      // 약 20% 사용자는 30-89일 미접속
      daysAgo = 30 + Math.floor(Math.random() * 60);
    } else {
      // 나머지는 최근 접속
      daysAgo = Math.floor(Math.random() * 30);
    }

    // 권한 설정 (약 60%가 권한 보유)
    const hasAccess = i % 5 !== 0; // 80%가 권한 보유

    // 모델 설정 (권한이 있는 경우에만)
    let model = null;
    if (hasAccess) {
      model = models[i % models.length];
    }

    mockUsers.push({
      id: i,
      headquarters: hq,
      division: fullDivision,
      team: teams[i % teams.length],
      job_category: jobCategories[i % jobCategories.length],
      rank: ranks[i % ranks.length],
      position: positions[i % positions.length],
      employee_number: `${19000000 + Math.floor(Math.random() * 5000000)}`,
      full_name: koreanNames[i % koreanNames.length],
      last_login_at: new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000).toISOString(),
      gpt_access_granted: hasAccess,
      allowed_model: model,
    });
  }
  return mockUsers;
}

/**
 * Mock 데이터 생성 (개발용) - 접근 신청
 */
function generateMockAccessRequests(count) {
  const mockRequests = [];

  // 실제 도로공사 조직 구조 기반 데이터
  const headquarters = [
    '서울경기본부', 'AI디지털본부', '홍보처', '건설본부', '기술본부',
    '영업본부', '강원본부', '충청본부', '전라본부', '경상본부'
  ];

  const divisions = [
    '기술처', '디지털관리처', '홍보계획부', '언론홍보부', '시설관리처',
    '건설관리처', '안전관리처', '기획처', '재무처', '인사처'
  ];

  const teams = [
    '시설부', '경영시스템부', '홍보계획 총괄', '디지털 소통', '건설기획부',
    '도로유지부', '시설안전부', '전기통신부', '교통관리부', '재무관리부'
  ];

  const jobCategories = [
    '전기', '정보통신', '토목', '건축', '기계', '사무직', '기술직', '안전관리', '경영지원'
  ];

  const ranks = ['3급', '4급', '5급', '6급', '7급', '8급'];

  const positions = ['본부장', '처장', '차장', '부장', '대리', '주임', '사원'];

  const koreanNames = [
    '이준호', '박서준', '김민재', '정하늘', '최지훈', '강예린', '임수빈', '한지원',
    '오성민', '신소율', '윤재현', '배지연', '송우진', '문예지', '권태성', '홍나연',
    '장수현', '유민경', '노건우', '서다온', '안준영', '황시우', '구예슬', '탁도윤',
    '진서아', '표민재', '국지안', '감찬영', '변유진', '복서준', '목하은', '빈준혁'
  ];

  const statuses = ['pending', 'approved', 'rejected'];

  for (let i = 1; i <= count; i++) {
    const hq = headquarters[i % headquarters.length];
    const div = divisions[i % divisions.length];
    const fullDivision = `${hq} ${div}`;

    // 신청일 (최근 30일 이내)
    const daysAgo = Math.floor(Math.random() * 30);

    // 상태 분포: pending 60%, approved 30%, rejected 10%
    let status;
    if (i % 10 === 0) {
      status = 'rejected';
    } else if (i % 3 === 0) {
      status = 'approved';
    } else {
      status = 'pending';
    }

    mockRequests.push({
      id: i,
      headquarters: hq,
      division: fullDivision,
      team: teams[i % teams.length],
      job_category: jobCategories[i % jobCategories.length],
      rank: ranks[i % ranks.length],
      position: positions[i % positions.length],
      employee_number: `${20000000 + Math.floor(Math.random() * 5000000)}`,
      full_name: koreanNames[i % koreanNames.length],
      requested_at: new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000).toISOString(),
      status: status,
    });
  }
  return mockRequests;
}
