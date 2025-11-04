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
  ToggleButton,
  ToggleButtonGroup,
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
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import * as XLSX from 'xlsx';
import axios from '../axiosConfig';

// dayjs 한국어 설정
dayjs.locale('ko');

// API Base
const API_BASE = '/api/v1/admin';

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
 * 미접속 시간 계산
 */
function calculateInactiveDays(lastLogin) {
  if (!lastLogin) return '접속 이력 없음';
  const now = new Date();
  const last = new Date(lastLogin);
  const days = Math.floor((now - last) / (1000 * 60 * 60 * 24));
  return `${days}일`;
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

  // 접근승인관리 탭 상태
  const [accessRequests, setAccessRequests] = useState([]);
  const [requestsTotal, setRequestsTotal] = useState(0);
  const [requestsPage, setRequestsPage] = useState(1);
  const [requestsRowsPerPage, setRequestsRowsPerPage] = useState(10);
  const [requestsOrderBy, setRequestsOrderBy] = useState('id');
  const [requestsOrder, setRequestsOrder] = useState('desc');
  const [selectedRequests, setSelectedRequests] = useState([]);

  // 접근승인관리 필터 상태 (dayjs 객체로 관리)
  const [requestsStartDate, setRequestsStartDate] = useState(null);
  const [requestsEndDate, setRequestsEndDate] = useState(null);
  const [requestsSearchType, setRequestsSearchType] = useState('전체');
  const [requestsSearchText, setRequestsSearchText] = useState('');
  const [requestsStatusFilter, setRequestsStatusFilter] = useState('전체');

  // 로딩 상태
  const [isLoading, setIsLoading] = useState(false);

  /**
   * 사용자 목록 로드
   */
  const loadUsers = async () => {
    setIsLoading(true);
    try {
      // TODO: 실제 API 엔드포인트로 교체 필요
      const params = {
        page,
        limit: rowsPerPage,
        order_by: orderBy,
        order,
      };

      if (searchText && searchType !== '전체') {
        params.search_type = searchType;
        params.search = searchText;
      }

      if (accessFilter !== '전체') {
        params.gpt_access = accessFilter === 'Y';
      }

      if (modelFilter !== '전체') {
        params.model = modelFilter;
      }

      if (longInactive) {
        params.inactive_days = 90;
      }

      // Mock data for now
      const mockUsers = generateMockUsers(20);
      setUsers(mockUsers);
      setTotal(100);
    } catch (error) {
      console.error('사용자 목록 로드 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (tabValue === 0) {
      loadUsers();
    } else if (tabValue === 1) {
      loadAccessRequests();
    }
  }, [tabValue, page, rowsPerPage, orderBy, order, requestsPage, requestsRowsPerPage, requestsOrderBy, requestsOrder]);

  /**
   * 접근 신청 목록 로드
   */
  const loadAccessRequests = async () => {
    setIsLoading(true);
    try {
      // TODO: 실제 API 엔드포인트로 교체 필요
      // Mock data for now
      const mockRequests = generateMockAccessRequests(30);
      setAccessRequests(mockRequests);
      setRequestsTotal(150);
    } catch (error) {
      console.error('접근 신청 목록 로드 실패:', error);
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
   * 접근승인관리 검색
   */
  const handleRequestsSearch = () => {
    setRequestsPage(1);
    loadAccessRequests();
  };

  /**
   * 접근승인관리 초기화
   */
  const handleRequestsReset = () => {
    setRequestsStartDate(null);
    setRequestsEndDate(null);
    setRequestsSearchType('전체');
    setRequestsSearchText('');
    setRequestsStatusFilter('전체');
    setRequestsPage(1);
    loadAccessRequests();
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
      // TODO: API 호출
      console.log('권한 토글:', userId, !currentAccess);
      loadUsers();
    } catch (error) {
      console.error('권한 변경 실패:', error);
    }
  };

  /**
   * 모델 변경
   */
  const handleModelChange = async (userId, model) => {
    try {
      // TODO: API 호출
      console.log('모델 변경:', userId, model);
      loadUsers();
    } catch (error) {
      console.error('모델 변경 실패:', error);
    }
  };

  /**
   * 권한 회수
   */
  const handleRevokeAccess = () => {
    if (selected.length === 0) {
      setAlertMessage('선택 후 버튼을 클릭해주세요');
      setAlertOpen(true);
      return;
    }
    // TODO: 실제 권한 회수 로직
    console.log('권한 회수:', selected);
    setSelected([]);
    loadUsers();
  };

  /**
   * 권한 부여
   */
  const handleGrantAccess = () => {
    if (selected.length === 0) {
      setAlertMessage('선택 후 버튼을 클릭해주세요');
      setAlertOpen(true);
      return;
    }
    // TODO: 실제 권한 부여 로직
    console.log('권한 부여:', selected);
    setSelected([]);
    loadUsers();
  };

  /**
   * 권한통계보기
   */
  const handleShowStats = async () => {
    try {
      // TODO: API 호출
      const mockStats = [
        { id: 1, team: '경영본부', count: 15 },
        { id: 2, team: '기술본부', count: 23 },
        { id: 3, team: '영업본부', count: 18 },
        { id: 4, team: '관리팀', count: 8 },
      ];
      setDepartmentStats(mockStats);
      setStatsOpen(true);
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = () => {
    const excelData = users.map((user, index) => ({
      번호: (page - 1) * rowsPerPage + index + 1,
      본부: user.headquarters || '-',
      '부/처': user.division || '-',
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
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '사용자목록');
    XLSX.writeFile(wb, `사용자목록_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  /**
   * 접근 신청 소트
   */
  const handleRequestsSort = (column) => {
    const isAsc = requestsOrderBy === column && requestsOrder === 'asc';
    setRequestsOrder(isAsc ? 'desc' : 'asc');
    setRequestsOrderBy(column);
  };

  /**
   * 접근 신청 전체 선택/해제
   */
  const handleSelectAllRequests = (event) => {
    if (event.target.checked) {
      setSelectedRequests(accessRequests.map((req) => req.id));
    } else {
      setSelectedRequests([]);
    }
  };

  /**
   * 접근 신청 개별 선택/해제
   */
  const handleSelectRequest = (id) => {
    const selectedIndex = selectedRequests.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selectedRequests, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selectedRequests.slice(1));
    } else if (selectedIndex === selectedRequests.length - 1) {
      newSelected = newSelected.concat(selectedRequests.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selectedRequests.slice(0, selectedIndex),
        selectedRequests.slice(selectedIndex + 1)
      );
    }

    setSelectedRequests(newSelected);
  };

  /**
   * 개별 승인 버튼 클릭
   */
  const handleApprovalClick = (request) => {
    setCurrentApprovalUser([request.id]);
    setSelectedModel('');
    setApprovalModalOpen(true);
  };

  /**
   * 일괄 승인 버튼 클릭
   */
  const handleBulkApproval = () => {
    if (selectedRequests.length === 0) {
      setAlertMessage('선택 후 버튼을 클릭해주세요');
      setAlertOpen(true);
      return;
    }
    setCurrentApprovalUser(selectedRequests);
    setSelectedModel('');
    setApprovalModalOpen(true);
  };

  /**
   * 승인 확인
   */
  const handleConfirmApproval = async () => {
    if (!selectedModel) {
      alert('모델을 선택해주세요');
      return;
    }

    try {
      // TODO: 실제 API 호출
      console.log('승인:', currentApprovalUser, '모델:', selectedModel);
      setApprovalModalOpen(false);
      setSelectedRequests([]);
      setCurrentApprovalUser(null);
      setSelectedModel('');
      loadAccessRequests();
    } catch (error) {
      console.error('승인 실패:', error);
    }
  };

  /**
   * 접근 신청 엑셀 다운로드
   */
  const handleDownloadRequestsExcel = () => {
    const excelData = accessRequests.map((req, index) => ({
      번호: (requestsPage - 1) * requestsRowsPerPage + index + 1,
      본부: req.headquarters || '-',
      '부/처': req.division || '-',
      팀: req.team || '-',
      직종: req.job_category || '-',
      직급: req.position || '-',
      직위: req.rank || '-',
      사번: req.employee_number || '-',
      이름: req.full_name || '-',
      승인신청일: formatDateTime(req.requested_at),
      승인요청상태: req.status === 'pending' ? '대기' : req.status === 'approved' ? '승인' : '거부',
    }));

    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '접근신청목록');
    XLSX.writeFile(wb, `접근신청목록_${new Date().toISOString().slice(0, 10)}.xlsx`);
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
          <Tab label="접근승인관리" />
        </Tabs>
      </Paper>

      {/* 탭 1: 사용자 관리 */}
      {tabValue === 0 && (
        <>
          {/* 검색 필터 */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              {/* 검색 유형 */}
              <ToggleButtonGroup
                value={searchType}
                exclusive
                onChange={(e, value) => value && setSearchType(value)}
                size="small"
              >
                <ToggleButton value="전체">전체</ToggleButton>
                <ToggleButton value="사번">사번</ToggleButton>
                <ToggleButton value="이름">이름</ToggleButton>
                <ToggleButton value="본부">본부</ToggleButton>
                <ToggleButton value="부/처">부/처</ToggleButton>
                <ToggleButton value="팀">팀</ToggleButton>
              </ToggleButtonGroup>

              {/* 검색어 */}
              <TextField
                size="small"
                placeholder="검색어 입력"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                sx={{ minWidth: 200 }}
              />

              {/* 권한 필터 */}
              <ToggleButtonGroup
                value={accessFilter}
                exclusive
                onChange={(e, value) => value && setAccessFilter(value)}
                size="small"
              >
                <ToggleButton value="전체">전체</ToggleButton>
                <ToggleButton value="Y">Y</ToggleButton>
                <ToggleButton value="N">N</ToggleButton>
              </ToggleButtonGroup>

              {/* 모델 필터 */}
              <ToggleButtonGroup
                value={modelFilter}
                exclusive
                onChange={(e, value) => value && setModelFilter(value)}
                size="small"
              >
                <ToggleButton value="전체">전체</ToggleButton>
                <ToggleButton value="Qwen235B">Qwen235B</ToggleButton>
                <ToggleButton value="Qwen32B">Qwen32B</ToggleButton>
              </ToggleButtonGroup>

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
            </Box>
            <IconButton
              onClick={handleDownloadExcel}
              sx={{
                backgroundColor: '#28a745',
                color: 'white',
                '&:hover': { backgroundColor: '#218838' },
              }}
            >
              <DownloadIcon />
            </IconButton>
          </Box>

          {/* 테이블 */}
          <TableContainer component={Paper} elevation={3}>
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
                    >
                      번호
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'headquarters'}
                      direction={orderBy === 'headquarters' ? order : 'asc'}
                      onClick={() => handleSort('headquarters')}
                    >
                      본부
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'division'}
                      direction={orderBy === 'division' ? order : 'asc'}
                      onClick={() => handleSort('division')}
                    >
                      부/처
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'team'}
                      direction={orderBy === 'team' ? order : 'asc'}
                      onClick={() => handleSort('team')}
                    >
                      팀
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'job_category'}
                      direction={orderBy === 'job_category' ? order : 'asc'}
                      onClick={() => handleSort('job_category')}
                    >
                      직종
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'position'}
                      direction={orderBy === 'position' ? order : 'asc'}
                      onClick={() => handleSort('position')}
                    >
                      직급
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'rank'}
                      direction={orderBy === 'rank' ? order : 'asc'}
                      onClick={() => handleSort('rank')}
                    >
                      직위
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'employee_number'}
                      direction={orderBy === 'employee_number' ? order : 'asc'}
                      onClick={() => handleSort('employee_number')}
                    >
                      사번
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'full_name'}
                      direction={orderBy === 'full_name' ? order : 'asc'}
                      onClick={() => handleSort('full_name')}
                    >
                      이름
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={orderBy === 'last_login_at'}
                      direction={orderBy === 'last_login_at' ? order : 'asc'}
                      onClick={() => handleSort('last_login_at')}
                    >
                      최종접속일
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>미접속시간</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>권한</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>모델선택</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user, index) => {
                  const isSelected = selected.indexOf(user.id) !== -1;
                  return (
                    <TableRow key={user.id} hover selected={isSelected}>
                      <TableCell padding="checkbox">
                        <Checkbox checked={isSelected} onChange={() => handleSelect(user.id)} />
                      </TableCell>
                      <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                      <TableCell>{user.headquarters || '-'}</TableCell>
                      <TableCell>{user.division || '-'}</TableCell>
                      <TableCell>{user.team || '-'}</TableCell>
                      <TableCell>{user.job_category || '-'}</TableCell>
                      <TableCell>{user.position || '-'}</TableCell>
                      <TableCell>{user.rank || '-'}</TableCell>
                      <TableCell>{user.employee_number || '-'}</TableCell>
                      <TableCell>{user.full_name || '-'}</TableCell>
                      <TableCell>{formatDateTime(user.last_login_at)}</TableCell>
                      <TableCell>{calculateInactiveDays(user.last_login_at)}</TableCell>
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

          {/* 테이블 하단 버튼 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="contained" color="error" onClick={handleRevokeAccess}>
                권한 회수
              </Button>
              <Button variant="contained" color="primary" onClick={handleGrantAccess}>
                권한 부여
              </Button>
            </Box>
            <Button variant="outlined" onClick={handleShowStats}>
              권한통계보기
            </Button>
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

      {/* 탭 2: 접근승인관리 */}
      {tabValue === 1 && (
        <>
          {/* 검색 필터 */}
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              {/* 기간 선택 */}
              <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
                <DatePicker
                  label="시작일"
                  value={requestsStartDate}
                  onChange={(newValue) => setRequestsStartDate(newValue)}
                  slotProps={{
                    textField: {
                      size: 'small',
                      sx: { minWidth: 160 }
                    }
                  }}
                />
                <DatePicker
                  label="종료일"
                  value={requestsEndDate}
                  onChange={(newValue) => setRequestsEndDate(newValue)}
                  slotProps={{
                    textField: {
                      size: 'small',
                      sx: { minWidth: 160 }
                    }
                  }}
                />
              </LocalizationProvider>

              {/* 검색 유형 */}
              <ToggleButtonGroup
                value={requestsSearchType}
                exclusive
                onChange={(e, value) => value && setRequestsSearchType(value)}
                size="small"
              >
                <ToggleButton value="전체">전체</ToggleButton>
                <ToggleButton value="사번">사번</ToggleButton>
                <ToggleButton value="이름">이름</ToggleButton>
              </ToggleButtonGroup>

              {/* 검색어 */}
              <TextField
                size="small"
                placeholder="검색어 입력"
                value={requestsSearchText}
                onChange={(e) => setRequestsSearchText(e.target.value)}
                sx={{ minWidth: 200 }}
              />

              {/* 승인신청상태 라벨 */}
              <Typography variant="body2" sx={{ fontWeight: 'bold', ml: 1 }}>
                승인신청상태
              </Typography>

              {/* 승인신청상태 필터 */}
              <Select
                size="small"
                value={requestsStatusFilter}
                onChange={(e) => setRequestsStatusFilter(e.target.value)}
                sx={{ minWidth: 120 }}
              >
                <MenuItem value="전체">전체</MenuItem>
                <MenuItem value="신청">신청</MenuItem>
                <MenuItem value="거부">거부</MenuItem>
                <MenuItem value="미신청">미신청</MenuItem>
              </Select>

              {/* 검색/초기화 */}
              <Button variant="contained" startIcon={<SearchIcon />} onClick={handleRequestsSearch}>
                검색
              </Button>
              <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRequestsReset}>
                초기화
              </Button>
            </Box>
          </Paper>

          {/* 테이블 상단 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Typography variant="body2">
                총 <strong>{requestsTotal.toLocaleString()}</strong>건
              </Typography>
              <Select
                size="small"
                value={requestsRowsPerPage}
                onChange={(e) => {
                  setRequestsRowsPerPage(e.target.value);
                  setRequestsPage(1);
                }}
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={30}>30</MenuItem>
                <MenuItem value={40}>40</MenuItem>
                <MenuItem value={50}>50</MenuItem>
              </Select>
            </Box>
            <IconButton
              onClick={handleDownloadRequestsExcel}
              sx={{
                backgroundColor: '#28a745',
                color: 'white',
                '&:hover': { backgroundColor: '#218838' },
              }}
            >
              <DownloadIcon />
            </IconButton>
          </Box>

          {/* 테이블 */}
          <TableContainer component={Paper} elevation={3}>
            <Table sx={{ minWidth: 1400 }}>
              <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={accessRequests.length > 0 && selectedRequests.length === accessRequests.length}
                      indeterminate={selectedRequests.length > 0 && selectedRequests.length < accessRequests.length}
                      onChange={handleSelectAllRequests}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'id'}
                      direction={requestsOrderBy === 'id' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('id')}
                    >
                      번호
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'headquarters'}
                      direction={requestsOrderBy === 'headquarters' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('headquarters')}
                    >
                      본부
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'division'}
                      direction={requestsOrderBy === 'division' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('division')}
                    >
                      부/처
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'team'}
                      direction={requestsOrderBy === 'team' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('team')}
                    >
                      팀
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'job_category'}
                      direction={requestsOrderBy === 'job_category' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('job_category')}
                    >
                      직종
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'position'}
                      direction={requestsOrderBy === 'position' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('position')}
                    >
                      직급
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'rank'}
                      direction={requestsOrderBy === 'rank' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('rank')}
                    >
                      직위
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'employee_number'}
                      direction={requestsOrderBy === 'employee_number' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('employee_number')}
                    >
                      사번
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'full_name'}
                      direction={requestsOrderBy === 'full_name' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('full_name')}
                    >
                      이름
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'requested_at'}
                      direction={requestsOrderBy === 'requested_at' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('requested_at')}
                    >
                      승인신청일
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    <TableSortLabel
                      active={requestsOrderBy === 'status'}
                      direction={requestsOrderBy === 'status' ? requestsOrder : 'asc'}
                      onClick={() => handleRequestsSort('status')}
                    >
                      승인요청상태
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>승인</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accessRequests.map((request, index) => {
                  const isSelected = selectedRequests.indexOf(request.id) !== -1;
                  return (
                    <TableRow key={request.id} hover selected={isSelected}>
                      <TableCell padding="checkbox">
                        <Checkbox checked={isSelected} onChange={() => handleSelectRequest(request.id)} />
                      </TableCell>
                      <TableCell>{(requestsPage - 1) * requestsRowsPerPage + index + 1}</TableCell>
                      <TableCell>{request.headquarters || '-'}</TableCell>
                      <TableCell>{request.division || '-'}</TableCell>
                      <TableCell>{request.team || '-'}</TableCell>
                      <TableCell>{request.job_category || '-'}</TableCell>
                      <TableCell>{request.position || '-'}</TableCell>
                      <TableCell>{request.rank || '-'}</TableCell>
                      <TableCell>{request.employee_number || '-'}</TableCell>
                      <TableCell>{request.full_name || '-'}</TableCell>
                      <TableCell>{formatDateTime(request.requested_at)}</TableCell>
                      <TableCell>
                        {request.status === 'pending' ? '대기' : request.status === 'approved' ? '승인' : '거부'}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="contained"
                          size="small"
                          disabled={request.status !== 'pending'}
                          onClick={() => handleApprovalClick(request)}
                        >
                          승인
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {accessRequests.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={13} align="center" sx={{ py: 4 }}>
                      데이터가 없습니다.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* 테이블 하단 버튼 */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mt: 3 }}>
            <Button variant="contained" color="primary" onClick={handleBulkApproval}>
              승인
            </Button>
          </Box>

          {/* 페이지네이션 */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={Math.ceil(requestsTotal / requestsRowsPerPage)}
              page={requestsPage}
              onChange={(e, value) => setRequestsPage(value)}
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

      {/* 승인 모달 */}
      <Dialog open={approvalModalOpen} onClose={() => setApprovalModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>접근 권한 부여</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 3 }}>
            선택한 사용자에 대해 일괄적으로 접근권한을 부여합니다.
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
              모델 선택 *
            </Typography>
            <ToggleButtonGroup
              value={selectedModel}
              exclusive
              onChange={(e, value) => value && setSelectedModel(value)}
              fullWidth
            >
              <ToggleButton value="Qwen235B">Qwen235B</ToggleButton>
              <ToggleButton value="Qwen32B">Qwen32B</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApprovalModalOpen(false)}>취소</Button>
          <Button onClick={handleConfirmApproval} variant="contained" color="primary">
            확인
          </Button>
        </DialogActions>
      </Dialog>

      {/* 권한통계보기 모달 */}
      <Dialog open={statsOpen} onClose={() => setStatsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">부서별 사용자 통계</Typography>
            <IconButton
              onClick={handleDownloadStatsExcel}
              sx={{
                backgroundColor: '#28a745',
                color: 'white',
                '&:hover': { backgroundColor: '#218838' },
              }}
              size="small"
            >
              <DownloadIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>팀</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>인원</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {departmentStats.map((stat, index) => (
                  <TableRow key={stat.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>{stat.team}</TableCell>
                    <TableCell>{stat.count}</TableCell>
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
    </Box>
  );
}

/**
 * Mock 데이터 생성 (개발용) - 사용자
 */
function generateMockUsers(count) {
  const mockUsers = [];
  for (let i = 1; i <= count; i++) {
    mockUsers.push({
      id: i,
      headquarters: ['경영본부', '기술본부', '영업본부'][i % 3],
      division: ['기획처', '관리처', '건설처', '안전처'][i % 4],
      team: ['팀A', '팀B', '팀C', '팀D'][i % 4],
      job_category: ['사무', '기술', '관리'][i % 3],
      position: ['사원', '대리', '과장', '차장', '부장'][i % 5],
      rank: ['팀원', '팀장', '본부장'][i % 3],
      employee_number: `EMP${String(i).padStart(5, '0')}`,
      full_name: `사용자${i}`,
      last_login_at: new Date(Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000).toISOString(),
      gpt_access_granted: i % 2 === 0,
      allowed_model: i % 3 === 0 ? 'Qwen235B' : i % 3 === 1 ? 'Qwen32B' : null,
    });
  }
  return mockUsers;
}

/**
 * Mock 데이터 생성 (개발용) - 접근 신청
 */
function generateMockAccessRequests(count) {
  const mockRequests = [];
  for (let i = 1; i <= count; i++) {
    mockRequests.push({
      id: i,
      headquarters: ['경영본부', '기술본부', '영업본부'][i % 3],
      division: ['기획처', '관리처', '건설처', '안전처'][i % 4],
      team: ['팀A', '팀B', '팀C', '팀D'][i % 4],
      job_category: ['사무', '기술', '관리'][i % 3],
      position: ['사원', '대리', '과장', '차장', '부장'][i % 5],
      rank: ['팀원', '팀장', '본부장'][i % 3],
      employee_number: `EMP${String(i + 100).padStart(5, '0')}`,
      full_name: `신청자${i}`,
      requested_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      status: i % 5 === 0 ? 'approved' : i % 7 === 0 ? 'rejected' : 'pending',
    });
  }
  return mockRequests;
}
