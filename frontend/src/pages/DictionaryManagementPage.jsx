/**
 * 사전관리 페이지
 * - 동의어사전, 사용자사전 관리
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  IconButton,
  Pagination,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Select,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import axios from '../axiosConfig';

const API_BASE = '/api/v1/admin';

export default function DictionaryManagementPage() {
  // 필터 상태
  const [searchType, setSearchType] = useState('전체');
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState({
    동의어사전: true,
    사용자사전: true,
  });

  // 테이블 상태
  const [dictionaries, setDictionaries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [selected, setSelected] = useState([]);

  // 메뉴 상태
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [typeFilterAnchorEl, setTypeFilterAnchorEl] = useState(null);

  // 모달 상태
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);

  useEffect(() => {
    loadDictionaries();
  }, [page, typeFilter]);

  /**
   * 사전 목록 로드
   */
  const loadDictionaries = async () => {
    try {
      // 실제 API 호출
      const skip = (page - 1) * rowsPerPage;
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: rowsPerPage.toString(),
      });

      const response = await axios.get(`${API_BASE}/dictionaries?${params}`);
      const data = response.data;

      setDictionaries(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('사전 목록 로딩 실패:', error);
      // 오류 발생 시 빈 목록 표시
      setDictionaries([]);
      setTotal(0);
    }
  };

  /**
   * 검색
   */
  const handleSearch = () => {
    setPage(1);
    loadDictionaries();
  };

  /**
   * 전체 선택/해제
   */
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(dictionaries.map((dict) => dict.id));
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
   * 사전 종류 필터 변경
   */
  const handleTypeFilterChange = (type) => {
    setTypeFilter({
      ...typeFilter,
      [type]: !typeFilter[type],
    });
    setPage(1);
  };

  /**
   * 선택 삭제
   */
  const handleDeleteSelected = () => {
    if (selected.length === 0) {
      alert('삭제할 사전을 선택해주세요.');
      return;
    }
    if (window.confirm(`선택한 ${selected.length}개 사전을 삭제하시겠습니까?`)) {
      console.log('삭제:', selected);
      // TODO: API 호출
      setSelected([]);
      loadDictionaries();
    }
  };

  /**
   * 동기화
   */
  const handleSync = () => {
    console.log('동기화 실행');
    // TODO: API 호출
    setSyncDialogOpen(false);
    setMenuAnchorEl(null);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 제목 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          사전 목록
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* 사전추가 버튼 */}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            sx={{ bgcolor: '#17a2b8', '&:hover': { bgcolor: '#138496' } }}
          >
            사전추가
          </Button>

          {/* 삭제 버튼 */}
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteSelected}
            disabled={selected.length === 0}
          >
            삭제
          </Button>

          {/* ∙∙∙ 메뉴 */}
          <IconButton
            onClick={(e) => setMenuAnchorEl(e.currentTarget)}
            sx={{
              border: '1px solid #ddd',
              borderRadius: 1,
            }}
          >
            <MoreVertIcon />
          </IconButton>
          <Menu
            anchorEl={menuAnchorEl}
            open={Boolean(menuAnchorEl)}
            onClose={() => setMenuAnchorEl(null)}
          >
            <MenuItem
              onClick={() => {
                setSyncDialogOpen(true);
                setMenuAnchorEl(null);
              }}
            >
              <SyncIcon sx={{ mr: 1 }} fontSize="small" />
              동기화
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* 검색 영역 */}
      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {/* 총 건수 */}
          <Typography variant="body2">
            총 <strong>{total.toLocaleString()}</strong>건
          </Typography>

          {/* 검색 영역 */}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {/* 검색 타입 선택 */}
            <Select
              size="small"
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="전체">전체</MenuItem>
              <MenuItem value="사전명">사전명</MenuItem>
              <MenuItem value="사전 설명">사전 설명</MenuItem>
            </Select>

            {/* 검색창 */}
            <TextField
              size="small"
              placeholder="검색어를 입력해주세요"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ minWidth: 300 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Box>
      </Paper>

      {/* 테이블 */}
      <TableContainer component={Paper} elevation={3}>
        <Table sx={{ minWidth: 1000 }}>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={dictionaries.length > 0 && selected.length === dictionaries.length}
                  indeterminate={selected.length > 0 && selected.length < dictionaries.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  사전종류
                  <IconButton
                    size="small"
                    onClick={(e) => setTypeFilterAnchorEl(e.currentTarget)}
                  >
                    <SearchIcon fontSize="small" />
                  </IconButton>
                </Box>
                <Menu
                  anchorEl={typeFilterAnchorEl}
                  open={Boolean(typeFilterAnchorEl)}
                  onClose={() => setTypeFilterAnchorEl(null)}
                >
                  <MenuItem>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={typeFilter.동의어사전}
                          onChange={() => handleTypeFilterChange('동의어사전')}
                        />
                      }
                      label="동의어사전"
                    />
                  </MenuItem>
                  <MenuItem>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={typeFilter.사용자사전}
                          onChange={() => handleTypeFilterChange('사용자사전')}
                        />
                      }
                      label="사용자사전"
                    />
                  </MenuItem>
                </Menu>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>카테고리</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>용어</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>정의</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>동의어</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사용</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>생성일</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>수정</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>삭제</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dictionaries.map((dict) => (
              <TableRow key={dict.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.indexOf(dict.id) !== -1}
                    onChange={() => handleSelect(dict.id)}
                  />
                </TableCell>
                <TableCell>{dict.category}</TableCell>
                <TableCell>{dict.term}</TableCell>
                <TableCell>{dict.definition}</TableCell>
                <TableCell>{dict.synonyms}</TableCell>
                <TableCell>{dict.is_active ? 'Y' : 'N'}</TableCell>
                <TableCell>{dict.created_at}</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => {
                      console.log('수정:', dict.id);
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => {
                      if (window.confirm('이 사전을 삭제하시겠습니까?')) {
                        console.log('삭제:', dict.id);
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
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

      {/* 동기화 다이얼로그 */}
      <Dialog open={syncDialogOpen} onClose={() => setSyncDialogOpen(false)}>
        <DialogTitle>동기화</DialogTitle>
        <DialogContent>
          <Typography>사전 데이터를 동기화하시겠습니까?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSyncDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSync}>
            확인
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
