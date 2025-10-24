/**
 * 오류신고관리 페이지
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  Select,
  MenuItem,
  IconButton,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import * as XLSX from 'xlsx';
import axios from '../axiosConfig';

// dayjs 한국어 설정
dayjs.locale('ko');

const API_BASE = '/api/v1/admin';

export default function ErrorReportManagementPage() {
  // 필터 상태 (dayjs 객체로 관리)
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [searchType, setSearchType] = useState('전체');
  const [searchText, setSearchText] = useState('');

  // 테이블 상태
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    loadReports();
  }, [page, rowsPerPage]);

  /**
   * 오류신고 목록 로드
   */
  const loadReports = async () => {
    try {
      // 실제 API 호출
      const skip = (page - 1) * rowsPerPage;
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: rowsPerPage.toString(),
      });

      const response = await axios.get(`${API_BASE}/error-reports?${params}`);
      const data = response.data;

      setReports(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('오류신고 목록 로딩 실패:', error);
      // 오류 발생 시 빈 목록 표시
      setReports([]);
      setTotal(0);
    }
  };

  /**
   * 검색
   */
  const handleSearch = () => {
    setPage(1);
    loadReports();
  };

  /**
   * 초기화
   */
  const handleReset = () => {
    setStartDate(null);
    setEndDate(null);
    setSearchType('전체');
    setSearchText('');
    setPage(1);
    loadReports();
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = () => {
    const ws = XLSX.utils.json_to_sheet(
      reports.map((report, index) => ({
        번호: (page - 1) * rowsPerPage + index + 1,
        메뉴명: report.menu,
        신고내용: report.content,
        이름: report.author,
        일자: report.created_at,
      }))
    );
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '오류신고관리');
    XLSX.writeFile(wb, `오류신고관리_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 검색 필터 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* 기간 선택 */}
          <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
            <DatePicker
              label="시작일"
              value={startDate}
              onChange={(newValue) => setStartDate(newValue)}
              slotProps={{
                textField: {
                  size: 'small',
                  sx: { minWidth: 160 }
                }
              }}
            />
            <DatePicker
              label="종료일"
              value={endDate}
              onChange={(newValue) => setEndDate(newValue)}
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
            value={searchType}
            exclusive
            onChange={(e, value) => value && setSearchType(value)}
            size="small"
          >
            <ToggleButton value="전체">전체</ToggleButton>
            <ToggleButton value="작성자">작성자</ToggleButton>
            <ToggleButton value="신고내용">신고내용</ToggleButton>
          </ToggleButtonGroup>

          {/* 검색창 */}
          <TextField
            size="small"
            placeholder="검색어를 입력해주세요."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ minWidth: 200 }}
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
        <Table sx={{ minWidth: 800 }}>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>오류 유형</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>오류 메시지</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사용자 ID</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>심각도</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>해결 여부</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>일자</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reports.map((report, index) => (
              <TableRow key={report.id} hover>
                <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                <TableCell>{report.error_type}</TableCell>
                <TableCell>{report.error_message}</TableCell>
                <TableCell>{report.user_id}</TableCell>
                <TableCell>{report.severity}</TableCell>
                <TableCell>{report.is_resolved ? '해결됨' : '미해결'}</TableCell>
                <TableCell>{report.created_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

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
    </Box>
  );
}
