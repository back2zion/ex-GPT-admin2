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
  const [addDialogOpen, setAddDialogOpen] = useState(false);

  // 사전 추가 폼 데이터
  const [newDict, setNewDict] = useState({
    dict_type: 'synonym',
    dict_name: '',
    dict_desc: '',
    case_sensitive: false,
    word_boundary: false,
  });

  useEffect(() => {
    loadDictionaries();
  }, [page, typeFilter]);

  /**
   * 사전 목록 로드
   */
  const loadDictionaries = async () => {
    try {
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
      setSelected(dictionaries.map((dict) => dict.dict_id));
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
   * 사전 추가 다이얼로그 열기
   */
  const handleOpenAddDialog = () => {
    setNewDict({
      dict_type: 'synonym',
      dict_name: '',
      dict_desc: '',
      case_sensitive: false,
      word_boundary: false,
    });
    setAddDialogOpen(true);
  };

  /**
   * 사전 다운로드 (CSV)
   */
  const handleDownloadDictionary = async (dictId) => {
    try {
      const response = await axios.get(`${API_BASE}/dictionaries/terms/list?dict_id=${dictId}&limit=10000`);
      const terms = response.data.items;

      // CSV 생성
      const headers = ['정식명칭', '주요약칭', '추가약칭1', '추가약칭2', '추가약칭3', '영문명', '영문약칭', '분류'];
      const rows = terms.map(term => [
        term.main_term,
        term.main_alias || '',
        term.alias_1 || '',
        term.alias_2 || '',
        term.alias_3 || '',
        term.english_name || '',
        term.english_alias || '',
        term.category || ''
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      // BOM 추가 (엑셀 한글 깨짐 방지)
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dictionary_${dictId}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('다운로드 실패:', error);
      alert('사전 다운로드에 실패했습니다.');
    }
  };

  /**
   * 사전 추가
   */
  const handleAddDictionary = async () => {
    if (!newDict.dict_name.trim()) {
      alert('사전명을 입력해주세요.');
      return;
    }

    try {
      await axios.post(`${API_BASE}/dictionaries`, {
        dict_type: newDict.dict_type,
        dict_name: newDict.dict_name.trim(),
        dict_desc: newDict.dict_desc.trim() || null,
        case_sensitive: newDict.case_sensitive,
        word_boundary: newDict.word_boundary,
        use_yn: true,
      });

      alert('사전이 추가되었습니다.');
      setAddDialogOpen(false);
      loadDictionaries();
    } catch (error) {
      console.error('사전 추가 실패:', error);
      alert('사전 추가에 실패했습니다.');
    }
  };

  /**
   * 선택 삭제
   */
  const handleDeleteSelected = async () => {
    if (selected.length === 0) {
      alert('삭제할 사전을 선택해주세요.');
      return;
    }
    if (window.confirm(`선택한 ${selected.length}개 사전을 삭제하시겠습니까?`)) {
      try {
        // 각 사전에 대해 삭제 API 호출
        await Promise.all(
          selected.map((id) => axios.delete(`${API_BASE}/dictionaries/${id}`))
        );
        alert('선택한 사전이 삭제되었습니다.');
        setSelected([]);
        loadDictionaries();
      } catch (error) {
        console.error('삭제 실패:', error);
        alert('삭제에 실패했습니다.');
      }
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

  /**
   * 사전 종류 한글 변환
   */
  const getDictTypeLabel = (dictType) => {
    return dictType === 'synonym' ? '동의어사전' : '사용자사전';
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
            onClick={handleOpenAddDialog}
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
            {selected.length === 1 && (
              <MenuItem
                onClick={() => {
                  handleDownloadDictionary(selected[0]);
                  setMenuAnchorEl(null);
                }}
              >
                <SearchIcon sx={{ mr: 1 }} fontSize="small" />
                선택한 사전 다운로드
              </MenuItem>
            )}
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
              <TableCell sx={{ fontWeight: 'bold' }}>사전명</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사전 설명</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>대소문자 구분</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>단어수</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>생성일</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>수정</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>삭제</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dictionaries.map((dict) => (
              <TableRow key={dict.dict_id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.indexOf(dict.dict_id) !== -1}
                    onChange={() => handleSelect(dict.dict_id)}
                  />
                </TableCell>
                <TableCell>{getDictTypeLabel(dict.dict_type)}</TableCell>
                <TableCell>
                  <Button
                    variant="text"
                    onClick={() => window.location.href = `#/vector-data/dictionaries/${dict.dict_id}`}
                    sx={{ textTransform: 'none' }}
                  >
                    {dict.dict_name}
                  </Button>
                </TableCell>
                <TableCell>{dict.dict_desc || '-'}</TableCell>
                <TableCell>{dict.case_sensitive ? 'Y' : 'N'}</TableCell>
                <TableCell>{dict.word_count || 0}</TableCell>
                <TableCell>
                  {dict.created_at ? new Date(dict.created_at).toLocaleDateString('ko-KR') : '-'}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => {
                      console.log('수정:', dict.dict_id);
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={async () => {
                      if (window.confirm('이 사전을 삭제하시겠습니까?')) {
                        try {
                          await axios.delete(`${API_BASE}/dictionaries/${dict.dict_id}`);
                          alert('사전이 삭제되었습니다.');
                          loadDictionaries();
                        } catch (error) {
                          console.error('삭제 실패:', error);
                          alert('삭제에 실패했습니다.');
                        }
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

      {/* 사전 추가 다이얼로그 */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        disableRestoreFocus
        PaperProps={{
          sx: { width: '400px', maxWidth: '90vw' }
        }}
      >
        <DialogTitle>사전 추가</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 'bold' }}>
            사전 종류
          </Typography>
          <Select
            fullWidth
            value={newDict.dict_type}
            onChange={(e) => setNewDict({ ...newDict, dict_type: e.target.value })}
            sx={{ mb: 2 }}
          >
            <MenuItem value="synonym">동의어 사전</MenuItem>
            <MenuItem value="user">사용자 사전</MenuItem>
          </Select>

          <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 'bold' }}>
            사전명
          </Typography>
          <TextField
            fullWidth
            placeholder="사전명을 입력해주세요"
            value={newDict.dict_name}
            onChange={(e) => setNewDict({ ...newDict, dict_name: e.target.value })}
            sx={{ mb: 2 }}
          />

          <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 'bold' }}>
            사전 설명
          </Typography>
          <TextField
            fullWidth
            placeholder="사전 설명을 입력해주세요"
            value={newDict.dict_desc}
            onChange={(e) => setNewDict({ ...newDict, dict_desc: e.target.value })}
            multiline
            rows={3}
            sx={{ mb: 2 }}
          />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={newDict.case_sensitive}
                  onChange={(e) => setNewDict({ ...newDict, case_sensitive: e.target.checked })}
                />
              }
              label="대소문자 구분"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={newDict.word_boundary}
                  onChange={(e) => setNewDict({ ...newDict, word_boundary: e.target.checked })}
                />
              }
              label="띄어쓰기 구분 (단어 경계 인식)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleAddDictionary} autoFocus>
            추가
          </Button>
        </DialogActions>
      </Dialog>

      {/* 동기화 다이얼로그 */}
      <Dialog
        open={syncDialogOpen}
        onClose={() => setSyncDialogOpen(false)}
        disableRestoreFocus
      >
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
