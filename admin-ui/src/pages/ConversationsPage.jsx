/**
 * 대화내역 조회 페이지 (완전 개편)
 * - 대분류/소분류 필터링
 * - 사용자 정보 포함 테이블
 * - 엑셀 다운로드
 * - 상세 페이지 연동
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Pagination,
  Typography,
  IconButton,
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
import * as XLSX from 'xlsx';
import { getConversations } from '../utils/api';

// dayjs 한국어 설정
dayjs.locale('ko');

/**
 * 대분류/소분류 매핑
 */
const CATEGORY_MAP = {
  '전체': {
    subcategories: ['전체']
  },
  '경영분야': {
    subcategories: ['전체', '기획/감사', '관리/홍보', '영업/디지털', '복리후생', '기타']
  },
  '기술분야': {
    subcategories: ['전체', '도로/안전', '교통', '건설', '신사업', '기타']
  },
  '경영/기술 외': {
    subcategories: ['전체', '기타']
  },
  '미분류': {
    subcategories: ['전체']
  }
};

/**
 * 날짜를 YYYY-MM-DD 형식으로 변환
 */
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * ISO datetime을 한국 시간으로 포맷
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
 * 기본 날짜 범위 (최근 7일)
 */
function getDefaultDateRange() {
  return {
    start: formatDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)),
    end: formatDate(new Date()),
  };
}

/**
 * 대화내역 조회 페이지 컴포넌트
 */
export default function ConversationsPage() {
  const navigate = useNavigate();

  // 날짜 범위 (dayjs 객체로 관리)
  const defaultRange = getDefaultDateRange();
  const [tempStartDate, setTempStartDate] = useState(dayjs(defaultRange.start));
  const [tempEndDate, setTempEndDate] = useState(dayjs(defaultRange.end));
  const [dateRange, setDateRange] = useState(defaultRange);

  // 대분류/소분류
  const [mainCategory, setMainCategory] = useState('전체');
  const [subCategory, setSubCategory] = useState('전체');

  // 페이지네이션
  const [page, setPage] = useState(1);
  const limit = 50;

  // 데이터 상태
  const [conversations, setConversations] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // 로딩 상태
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 대화내역 목록 로드
   */
  const loadConversations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = {
        start: dateRange.start,
        end: dateRange.end,
        page,
        limit,
      };

      // 대분류 필터 (전체가 아닐 경우만 추가)
      if (mainCategory !== '전체') {
        params.main_category = mainCategory;
      }

      // 소분류 필터 (전체가 아닐 경우만 추가)
      if (subCategory !== '전체') {
        params.sub_category = subCategory;
      }

      const data = await getConversations(params);
      setConversations(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('[ConversationsPage] 대화내역 로드 실패:', err);
      setError(err.response?.data?.detail || '대화내역을 불러올 수 없습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 데이터 로드
  useEffect(() => {
    loadConversations();
  }, [dateRange, mainCategory, subCategory, page]);

  /**
   * 검색 버튼 클릭
   */
  const handleSearch = () => {
    setDateRange({
      start: tempStartDate.format('YYYY-MM-DD'),
      end: tempEndDate.format('YYYY-MM-DD'),
    });
    setPage(1); // 검색 시 첫 페이지로
  };

  /**
   * 초기화 버튼 클릭
   */
  const handleReset = () => {
    const defaultRange = getDefaultDateRange();
    setTempStartDate(dayjs(defaultRange.start));
    setTempEndDate(dayjs(defaultRange.end));
    setDateRange(defaultRange);
    setMainCategory('전체');
    setSubCategory('전체');
    setPage(1);
  };

  /**
   * 대분류 변경
   */
  const handleMainCategoryChange = (event) => {
    const newValue = event.target.value;
    setMainCategory(newValue);
    setSubCategory('전체'); // 대분류 변경시 소분류 초기화
    setPage(1);
  };

  /**
   * 소분류 변경
   */
  const handleSubCategoryChange = (event) => {
    const newValue = event.target.value;
    setSubCategory(newValue);
    setPage(1);
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = async () => {
    try {
      // 전체 데이터 가져오기 (limit=10000)
      const params = {
        start: dateRange.start,
        end: dateRange.end,
        page: 1,
        limit: 10000,
      };

      if (mainCategory !== '전체') {
        params.main_category = mainCategory;
      }
      if (subCategory !== '전체') {
        params.sub_category = subCategory;
      }

      const data = await getConversations(params);

      // 엑셀 데이터 변환
      const excelData = data.items.map((item, index) => ({
        번호: index + 1,
        직급: item.position || '-',
        직위: item.rank || '-',
        팀명: item.team || '-',
        입사년도: item.join_year || '-',
        질문: item.question || '-',
        답변: item.answer ? (item.answer.length > 100 ? item.answer.substring(0, 100) + '...' : item.answer) : '-',
        대분류: item.main_category || '미분류',
        소분류: item.sub_category || '-',
        일자: formatDateTime(item.created_at),
      }));

      // 엑셀 파일 생성 및 다운로드
      const ws = XLSX.utils.json_to_sheet(excelData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '대화내역');
      XLSX.writeFile(wb, `대화내역_${formatDate(new Date())}.xlsx`);
    } catch (err) {
      console.error('[ConversationsPage] 엑셀 다운로드 실패:', err);
      alert('엑셀 다운로드에 실패했습니다.');
    }
  };

  /**
   * 행 클릭 - 상세 페이지로 이동
   */
  const handleRowClick = (id) => {
    navigate(`/conversations/${id}`);
  };

  /**
   * 페이지 변경
   */
  const handlePageChange = (event, value) => {
    setPage(value);
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* 헤더 */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        💬 대화내역 조회
      </Typography>

      {/* 필터 영역 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        {/* 날짜 범위 */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
            <DatePicker
              label="시작 날짜"
              value={tempStartDate}
              onChange={(newValue) => setTempStartDate(newValue)}
              slotProps={{
                textField: {
                  size: 'small',
                  sx: { minWidth: 160 }
                }
              }}
            />
            <DatePicker
              label="종료 날짜"
              value={tempEndDate}
              onChange={(newValue) => setTempEndDate(newValue)}
              slotProps={{
                textField: {
                  size: 'small',
                  sx: { minWidth: 160 }
                }
              }}
            />
          </LocalizationProvider>

          {/* 대분류 선택 */}
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="main-category-label">대분류</InputLabel>
            <Select
              labelId="main-category-label"
              value={mainCategory}
              onChange={handleMainCategoryChange}
              label="대분류"
            >
              {Object.keys(CATEGORY_MAP).map((cat) => (
                <MenuItem key={cat} value={cat}>
                  {cat}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* 소분류 선택 */}
          {mainCategory && CATEGORY_MAP[mainCategory] && (
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="sub-category-label">소분류</InputLabel>
              <Select
                labelId="sub-category-label"
                value={subCategory}
                onChange={handleSubCategoryChange}
                label="소분류"
              >
                {CATEGORY_MAP[mainCategory].subcategories.map((sub) => (
                  <MenuItem key={sub} value={sub}>
                    {sub}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {/* 검색/초기화 버튼 */}
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            sx={{ minWidth: 100 }}
          >
            조회
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleReset}
            sx={{ minWidth: 100 }}
          >
            초기화
          </Button>
        </Box>

        {/* 총 개수 */}
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          총 <strong>{total.toLocaleString()}</strong>건
        </Typography>
      </Paper>

      {/* 테이블 헤더 (엑셀 다운로드 버튼) */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
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

      {/* 로딩 상태 */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* 에러 상태 */}
      {error && (
        <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8d7da', color: '#721c24' }}>
          {error}
        </Paper>
      )}

      {/* 대화내역 테이블 */}
      {!isLoading && !error && (
        <TableContainer component={Paper} elevation={3}>
          <Table sx={{ minWidth: 1200 }}>
            <TableHead sx={{ bgcolor: '#f5f5f5' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', width: '60px' }}>번호</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '80px' }}>직급</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '80px' }}>직위</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '120px' }}>팀명</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '80px' }}>입사년도</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>질문</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>답변</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '100px' }}>대분류</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '100px' }}>소분류</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '140px' }}>일자</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {conversations.length > 0 ? (
                conversations.map((conv, index) => (
                  <TableRow
                    key={conv.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleRowClick(conv.id)}
                  >
                    <TableCell>{(page - 1) * limit + index + 1}</TableCell>
                    <TableCell>{conv.position || '-'}</TableCell>
                    <TableCell>{conv.rank || '-'}</TableCell>
                    <TableCell>{conv.team || '-'}</TableCell>
                    <TableCell>{conv.join_year || '-'}</TableCell>
                    <TableCell>
                      {conv.question.length > 50 ? conv.question.substring(0, 50) + '...' : conv.question}
                    </TableCell>
                    <TableCell>
                      {conv.answer
                        ? (conv.answer.length > 50 ? conv.answer.substring(0, 50) + '...' : conv.answer)
                        : '-'}
                    </TableCell>
                    <TableCell>{conv.main_category || '미분류'}</TableCell>
                    <TableCell>{conv.sub_category || '-'}</TableCell>
                    <TableCell>{formatDateTime(conv.created_at)}</TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    대화내역이 없습니다.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            size="large"
            showFirstButton
            showLastButton
          />
        </Box>
      )}
    </Box>
  );
}
