/**
 * 벡터 데이터 관리 페이지
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  InputAdornment,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Menu,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import axios from '../axiosConfig';

const API_BASE = '/api/v1/admin';

export default function VectorDataManagementPageSimple() {
  // 상태 관리
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total: 0, by_doctype: {} });
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);

  // 카테고리 생성 모달
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [newCategoryCode, setNewCategoryCode] = useState('');
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');

  // 카테고리 카드 3점 메뉴
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    loadCategories();
    loadStats();
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [page, rowsPerPage, categoryFilter, searchText]);

  // 카테고리 통계 로딩
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/vector-documents/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('통계 로딩 실패:', error);
      setStats({ total: 0, by_doctype: {} });
    }
  };

  // 카테고리 목록 로딩
  const loadCategories = async () => {
    try {
      const response = await axios.get(`${API_BASE}/vector-categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('카테고리 로딩 실패:', error);
    }
  };

  // 문서 목록 로딩
  const loadDocuments = async () => {
    try {
      setLoading(true);
      const skip = (page - 1) * rowsPerPage;
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: rowsPerPage.toString(),
      });

      if (categoryFilter) {
        params.append('doctype', categoryFilter);
      }

      if (searchText) {
        params.append('search', searchText);
      }

      const response = await axios.get(`${API_BASE}/vector-documents?${params}`);
      setDocuments(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('문서 목록 로딩 실패:', error);
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // 검색 실행
  const handleSearch = () => {
    setPage(1);
    loadDocuments();
  };

  // 초기화
  const handleReset = () => {
    setCategoryFilter('');
    setSearchText('');
    setPage(1);
  };

  // 카테고리 생성 모달 열기
  const handleOpenCategoryModal = async () => {
    try {
      // 다음 사용 가능한 코드 가져오기
      const response = await axios.get(`${API_BASE}/vector-categories/next-code`);
      setNewCategoryCode(response.data.next_code);
      setNewCategoryName('');
      setNewCategoryDesc('');
      setCategoryModalOpen(true);
    } catch (error) {
      console.error('다음 코드 조회 실패:', error);
      setNewCategoryCode('');
      setNewCategoryName('');
      setNewCategoryDesc('');
      setCategoryModalOpen(true);
    }
  };

  // 카테고리 생성 제출
  const handleCategorySubmit = async () => {
    if (!newCategoryCode || !newCategoryName) {
      alert('코드와 이름을 입력해주세요.');
      return;
    }

    try {
      await axios.post(`${API_BASE}/vector-categories`, {
        code: newCategoryCode,
        name: newCategoryName,
        description: newCategoryDesc,
      });

      alert('카테고리가 생성되었습니다.');
      setCategoryModalOpen(false);
      loadCategories();
      loadStats();
    } catch (error) {
      console.error('카테고리 생성 실패:', error);
      alert(error.response?.data?.detail || '카테고리 생성에 실패했습니다.');
    }
  };

  // 카테고리 삭제 (2단계 확인)
  const handleCategoryDelete = async (categoryCode, categoryName, documentCount) => {
    // 1차 확인
    if (documentCount > 0) {
      if (!window.confirm(`"${categoryName}" 카테고리에 ${documentCount}건의 문서가 있습니다.\n삭제하시겠습니까?`)) {
        return;
      }
    } else {
      if (!window.confirm(`"${categoryName}" 카테고리를 삭제하시겠습니까?`)) {
        return;
      }
    }

    // 2차 확인
    if (!window.confirm(`정말로 "${categoryName}" 카테고리를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/vector-categories/${categoryCode}`);
      alert('카테고리가 삭제되었습니다.');
      loadCategories();
      loadStats();
    } catch (error) {
      console.error('카테고리 삭제 실패:', error);
      alert(error.response?.data?.detail || '카테고리 삭제에 실패했습니다.');
    }
  };

  // 선택된 문서 삭제
  const handleDocumentDelete = async () => {
    if (selectedItems.length === 0) {
      alert('삭제할 문서를 선택해주세요.');
      return;
    }

    if (!window.confirm(`선택한 ${selectedItems.length}건의 문서를 정말 삭제하시겠습니까?`)) {
      return;
    }

    try {
      // 다중 문서 삭제 API 호출 (완전 삭제)
      await axios.post(`${API_BASE}/vector-documents/batch-delete`, selectedItems, {
        params: { hard_delete: true }  // 완전 삭제 (EDB, MinIO, Qdrant)
      });

      alert(`${selectedItems.length}건의 문서가 완전히 삭제되었습니다.`);
      setSelectedItems([]);
      loadDocuments();
      loadStats();
    } catch (error) {
      console.error('문서 삭제 실패:', error);
      alert(error.response?.data?.detail || '문서 삭제에 실패했습니다.');
    }
  };

  // 전체 선택/해제
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedItems(documents.map((doc) => doc.id));
    } else {
      setSelectedItems([]);
    }
  };

  // 개별 선택/해제
  const handleSelectOne = (id) => {
    setSelectedItems((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // 엑셀 다운로드
  const handleExcelDownload = async () => {
    try {
      let documentsToExport = [];

      // 선택한 항목이 있으면 선택 항목만, 없으면 전체
      if (selectedItems.length > 0) {
        // 선택한 항목만 필터링
        documentsToExport = documents.filter((doc) => selectedItems.includes(doc.id));
      } else {
        // 전체 데이터 가져오기
        const skip = 0;
        const limit = total;
        const params = new URLSearchParams({
          skip: skip.toString(),
          limit: limit.toString(),
        });

        if (categoryFilter) {
          params.append('doctype', categoryFilter);
        }

        if (searchText) {
          params.append('search', searchText);
        }

        const response = await axios.get(`${API_BASE}/vector-documents?${params}`);
        documentsToExport = response.data.items || [];
      }

      // CSV 형식으로 변환
      const headers = ['번호', '분류', '파일명', '등록일'];
      const rows = documentsToExport.map((doc, index) => [
        index + 1,
        doc.doctype_name || doc.doctype || '-',
        doc.title,
        doc.created_at ? new Date(doc.created_at).toLocaleDateString('ko-KR') : '-',
      ]);

      // CSV 생성
      const csvContent = [
        headers.join(','),
        ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
      ].join('\n');

      // UTF-8 BOM 추가 (엑셀에서 한글 깨짐 방지)
      const bom = '\uFEFF';
      const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });

      // 다운로드
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      const filename = selectedItems.length > 0
        ? `벡터문서목록_선택${selectedItems.length}건_${new Date().toISOString().slice(0, 10)}.csv`
        : `벡터문서목록_${new Date().toISOString().slice(0, 10)}.csv`;
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('엑셀 다운로드 실패:', error);
      alert('엑셀 다운로드에 실패했습니다.');
    }
  };

  // 문서 등록 모달
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleUploadDocument = () => {
    setUploadModalOpen(true);
    setUploadFile(null);
    // 현재 선택된 카테고리를 기본값으로 설정
    setUploadCategory(categoryFilter || '');
    setUploadTitle('');
    setUploadDescription('');
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile) {
      alert('파일을 선택해주세요.');
      return;
    }
    if (!uploadCategory) {
      alert('카테고리를 선택해주세요.');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('category_code', uploadCategory);
      if (uploadTitle) formData.append('title', uploadTitle);
      if (uploadDescription) formData.append('description', uploadDescription);

      await axios.post(`${API_BASE}/vector-documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      alert('문서가 등록되었습니다.');
      setUploadModalOpen(false);
      setUploadFile(null);
      setUploadCategory('');
      setUploadTitle('');
      setUploadDescription('');
      loadStats();
      loadDocuments();
    } catch (error) {
      console.error('문서 등록 실패:', error);
      alert(error.response?.data?.detail || '문서 등록에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 제목 */}
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
        학습 데이터 관리
      </Typography>

      {/* 소제목 */}
      <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3, color: '#666' }}>
        대상문서관리
      </Typography>

      {/* 검색 영역 */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', flex: 1 }}>
            {/* 수집대상 */}
            <Typography variant="body1" sx={{ fontWeight: 'bold', minWidth: 80 }}>
              수집대상
            </Typography>

            {/* 카테고리 선택 */}
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>카테고리</InputLabel>
              <Select
                value={categoryFilter}
                label="카테고리"
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setPage(1);
                }}
                renderValue={(selected) => {
                  if (selected === '') {
                    return `전체 (${stats.total.toLocaleString()}건)`;
                  }
                  const category = categories.find(cat => cat.code === selected);
                  const count = stats.by_doctype[selected]?.count || 0;
                  return `${category?.name || selected} (${count.toLocaleString()}건)`;
                }}
              >
                <MenuItem value="">전체 ({stats.total.toLocaleString()}건)</MenuItem>
                {categories.map((cat) => {
                  const count = stats.by_doctype[cat.code]?.count || 0;
                  return (
                    <MenuItem key={cat.code} value={cat.code}>
                      {cat.name} ({count.toLocaleString()}건)
                    </MenuItem>
                  );
                })}
              </Select>
            </FormControl>

            {/* 검색어 입력 */}
            <TextField
              size="small"
              placeholder="검색어를 입력하세요"
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

            {/* 검색 버튼 */}
            <Button variant="contained" onClick={handleSearch} startIcon={<SearchIcon />}>
              검색
            </Button>

            {/* 초기화 버튼 */}
            <Button variant="outlined" onClick={handleReset} startIcon={<RefreshIcon />}>
              초기화
            </Button>
          </Box>

          {/* 카테고리 생성 버튼 */}
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCategoryModal}>
            카테고리 생성
          </Button>
        </Box>
      </Paper>

      {/* 카테고리 통계 카드 */}
      <Grid container spacing={2} sx={{ marginBottom: '100px' }}>
        {/* 전체 카드 */}
        <Grid item xs={12} sm={6} md={4} lg={3}>
          <Card
            elevation={3}
            sx={{
              cursor: 'pointer',
              transition: 'all 0.2s',
              border: categoryFilter === '' ? '3px solid #00a651' : '2px solid transparent',
              background: categoryFilter === '' ? 'linear-gradient(135deg, #00a651 0%, #00c573 100%)' : 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 6,
              },
            }}
            onClick={(e) => {
              e.stopPropagation();
              setCategoryFilter('');
              setPage(1);
            }}
          >
            <CardContent sx={{ textAlign: 'center', py: 2, pointerEvents: 'none' }}>
              <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: categoryFilter === '' ? '#fff' : '#333' }}>
                전체
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: categoryFilter === '' ? '#fff' : '#00a651' }}>
                {stats.total.toLocaleString()}건
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* doctype별 카드 */}
        {categories.map((cat, index) => {
          const doctype = cat.code;
          const data = stats.by_doctype[cat.code] || { name: cat.name, count: 0 };

          // 도로공사 컬러 팔레트 (녹색/청록/파란색 계열)
          const colors = [
            { bg: 'linear-gradient(135deg, #00a651 0%, #00c573 100%)', text: '#fff', border: '#00a651' },
            { bg: 'linear-gradient(135deg, #0099cc 0%, #00bbdd 100%)', text: '#fff', border: '#0099cc' },
            { bg: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)', text: '#fff', border: '#1976d2' },
            { bg: 'linear-gradient(135deg, #0288d1 0%, #03a9f4 100%)', text: '#fff', border: '#0288d1' },
            { bg: 'linear-gradient(135deg, #00796b 0%, #009688 100%)', text: '#fff', border: '#00796b' },
            { bg: 'linear-gradient(135deg, #00897b 0%, #26a69a 100%)', text: '#fff', border: '#00897b' },
          ];
          const colorSet = colors[index % colors.length];
          const isSelected = categoryFilter === doctype;

          return (
            <Grid item xs={12} sm={6} md={4} lg={3} key={doctype}>
              <Card
                elevation={3}
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  border: isSelected ? `3px solid ${colorSet.border}` : '2px solid transparent',
                  background: isSelected ? colorSet.bg : 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)',
                  position: 'relative',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6,
                    '& .menu-icon-btn': {
                      opacity: 1,
                    },
                  },
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setCategoryFilter(doctype);
                  setPage(1);
                }}
              >
                <CardContent sx={{ textAlign: 'center', py: 2, px: 3 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: isSelected ? colorSet.text : '#333', pr: 3 }}>
                    {data.name || `카테고리 ${doctype}`}
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: isSelected ? colorSet.text : colorSet.border }}>
                    {data.count.toLocaleString()}건
                  </Typography>
                </CardContent>

                {/* 호버 시 우측 상단 3점 메뉴 */}
                <IconButton
                  className="menu-icon-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuAnchorEl(e.currentTarget);
                    setSelectedCategory({ doctype, name: data.name, count: data.count });
                  }}
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    opacity: 0,
                    transition: 'opacity 0.2s',
                    zIndex: 10,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 1)',
                    },
                  }}
                >
                  <MoreVertIcon sx={{ fontSize: 20, color: isSelected ? colorSet.text : '#666' }} />
                </IconButton>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* 카테고리 3점 메뉴 */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={() => {
          setMenuAnchorEl(null);
          setSelectedCategory(null);
        }}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem
          onClick={() => {
            if (selectedCategory) {
              handleCategoryDelete(
                selectedCategory.doctype,
                selectedCategory.name,
                selectedCategory.count
              );
            }
            setMenuAnchorEl(null);
            setSelectedCategory(null);
          }}
          sx={{
            color: '#ef4444',
            '&:hover': {
              backgroundColor: '#fee2e2',
            },
          }}
        >
          <DeleteIcon sx={{ fontSize: 18, mr: 1 }} />
          삭제
        </MenuItem>
      </Menu>

      {/* 통계 및 액션 영역 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, mt: 8 }}>
        {/* 왼쪽: 총 건수 및 보기 메뉴 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body1">
            총 <strong>{total.toLocaleString()}</strong>건
          </Typography>

          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>보기</InputLabel>
            <Select
              value={rowsPerPage}
              label="보기"
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
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* 오른쪽: 문서등록, 엑셀 다운로드 */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" startIcon={<UploadIcon />} onClick={handleUploadDocument}>
            문서등록
          </Button>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExcelDownload}>
            엑셀 다운로드
          </Button>
        </Box>
      </Box>

      {/* 테이블 */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper} elevation={2}>
            <Table sx={{ tableLayout: 'fixed' }}>
              <colgroup>
                <col style={{ width: '60px' }} />
                <col style={{ width: '80px' }} />
                <col style={{ width: '150px' }} />
                <col style={{ width: 'auto' }} />
                <col style={{ width: '120px' }} />
              </colgroup>
              <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                <TableRow>
                  <TableCell padding="checkbox">
                    <input
                      type="checkbox"
                      id="checkbox-select-all"
                      name="select-all"
                      checked={documents.length > 0 && selectedItems.length === documents.length}
                      onChange={handleSelectAll}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                      aria-label="Select all rows"
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>분류</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>파일명</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>등록일</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      데이터가 없습니다.
                    </TableCell>
                  </TableRow>
                ) : (
                  documents.map((doc, index) => {
                    const isSelected = selectedItems.includes(doc.id);
                    return (
                    <TableRow
                      key={doc.id}
                      sx={{
                        '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' },
                        bgcolor: isSelected ? 'rgba(0, 166, 81, 0.08)' : 'inherit'
                      }}
                    >
                      <TableCell padding="checkbox">
                        <input
                          type="checkbox"
                          id={`checkbox-${doc.id}`}
                          name={`select-doc-${doc.id}`}
                          checked={selectedItems.includes(doc.id)}
                          onChange={() => handleSelectOne(doc.id)}
                          style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                          aria-label={`Select row ${index + 1}`}
                        />
                      </TableCell>
                      <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                      <TableCell>{doc.doctype_name || doc.doctype || '-'}</TableCell>
                      <TableCell>{doc.title}</TableCell>
                      <TableCell>
                        {doc.created_at ? new Date(doc.created_at).toLocaleDateString('ko-KR') : '-'}
                      </TableCell>
                    </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* 선택된 항목 삭제 버튼 */}
          {selectedItems.length > 0 && (
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={handleDocumentDelete}
              >
                선택한 {selectedItems.length}건 삭제
              </Button>
            </Box>
          )}

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

      {/* 카테고리 생성 모달 */}
      <Dialog
        open={categoryModalOpen}
        onClose={() => setCategoryModalOpen(false)}
        PaperProps={{ sx: { width: 500 } }}
      >
        <DialogTitle>카테고리 생성</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="코드"
              value={newCategoryCode}
              onChange={(e) => setNewCategoryCode(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="이름"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              required
              fullWidth
            />
            <TextField
              label="설명"
              value={newCategoryDesc}
              onChange={(e) => setNewCategoryDesc(e.target.value)}
              multiline
              rows={3}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCategoryModalOpen(false)}>취소</Button>
          <Button onClick={handleCategorySubmit} variant="contained">
            생성
          </Button>
        </DialogActions>
      </Dialog>

      {/* 문서 업로드 모달 */}
      <Dialog
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        PaperProps={{ sx: { width: 600, maxWidth: '90vw' } }}
      >
        <DialogTitle>대상문서 업로드</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            {/* 안내 문구 */}
            <Box sx={{
              backgroundColor: '#f5f5f5',
              p: 2,
              borderRadius: 1,
              borderLeft: '4px solid #00a651'
            }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>
                1. 카테고리를 선택하세요.
              </Typography>
              <Typography variant="body2">
                2. 파일을 선택하고 저장 버튼을 클릭하세요.
              </Typography>
            </Box>

            {/* 카테고리 선택 */}
            <FormControl fullWidth required>
              <InputLabel>카테고리 선택</InputLabel>
              <Select
                value={uploadCategory}
                label="카테고리 선택"
                onChange={(e) => setUploadCategory(e.target.value)}
              >
                {categories.filter(cat => cat.use_yn === 'Y').map((cat) => (
                  <MenuItem key={cat.code} value={cat.code}>
                    {cat.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* 파일 업로드 */}
            <Box>
              <Button
                variant="outlined"
                component="label"
                fullWidth
                sx={{
                  py: 1.5,
                  justifyContent: 'flex-start',
                  textAlign: 'left'
                }}
              >
                {uploadFile ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <UploadIcon />
                    <Typography variant="body2">{uploadFile.name}</Typography>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <UploadIcon />
                    <Typography variant="body2">파일 업로드</Typography>
                  </Box>
                )}
                <input
                  type="file"
                  hidden
                  accept=".pdf,.txt,.doc,.docx,.hwp,.ppt,.pptx,.xls,.xlsx,.md,.rtf,.odt"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                />
              </Button>
              {uploadFile && (
                <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
                  선택된 파일: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(2)} KB)
                </Typography>
              )}
            </Box>

            {/* 제목 (선택) */}
            <TextField
              label="제목 (선택)"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              fullWidth
              placeholder="제목을 입력하지 않으면 파일명이 사용됩니다"
            />

            {/* 설명 (선택) */}
            <TextField
              label="설명 (선택)"
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              multiline
              rows={3}
              fullWidth
              placeholder="문서에 대한 설명을 입력하세요"
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setUploadModalOpen(false)}
            variant="outlined"
            disabled={uploading}
          >
            취소
          </Button>
          <Button
            onClick={handleUploadSubmit}
            variant="contained"
            color="primary"
            disabled={uploading}
            startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : null}
            sx={{ minWidth: 120 }}
          >
            {uploading ? '업로드 중...' : '저장'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
