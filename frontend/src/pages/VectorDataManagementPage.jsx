/**
 * 학습데이터 관리 페이지 (완전 개편)
 * - 대상문서관리
 * - 카테고리별 통계, 문서 업로드, 테이블 관리
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  Checkbox,
  IconButton,
  Pagination,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CreateNewFolder as FolderIcon,
} from '@mui/icons-material';
import * as XLSX from 'xlsx';
import axios from '../axiosConfig';

const API_BASE = '/api/v1/admin';

// 카테고리 목록
const CATEGORIES = ['법령', '업무가이드', '업무기준', '지침', '사규', '노동조합', '일반사항', '참고자료'];

// 카테고리별 건수 (Mock 데이터)
const CATEGORY_COUNTS = {
  '전체': 2196,
  '법령': 1113,
  '업무가이드': 586,
  '업무기준': 240,
  '지침': 175,
  '사규': 70,
  '노동조합': 7,
  '일반사항': 3,
  '참고자료': 2,
};

// 경로 선택 옵션
const PATH_OPTIONS = {
  대분류: ['법령', '사규', '지침', 'genimages', '업무가이드', '업무기준', '노동조합'],
  중분류: {
    '법령': ['건설기준정보시스템', '국가건설기준센터', '국가법령정보센터', '국정원', '국토부', '국토안전관리원', '도로공사 계약관련 기준', '환경', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '별표'],
  },
  소분류: {
    '국가건설기준센터': ['230106 도로설계기준 및 표준시방서'],
    '국가법령정보센터': ['KCS 14 20 00(콘크리트공사 표준시방서) 개정전문', '건축공사 표준시방서 일부 개정', '소음진동공정시험기준 전문(221201)', '전문', '표준시방서'],
  },
};

export default function VectorDataManagementPage() {
  // 필터 상태
  const [categoryFilter, setCategoryFilter] = useState('전체');
  const [searchText, setSearchText] = useState('');

  // 테이블 상태
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selected, setSelected] = useState([]);

  // 모달 상태
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  // 카테고리 생성 모달 상태
  const [categoryName, setCategoryName] = useState('');
  const [parsingPatterns, setParsingPatterns] = useState([
    { regex: '', type: 'sub title' }
  ]);

  // 문서 업로드 모달 상태
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadPath, setUploadPath] = useState({
    대분류: '',
    중분류: '',
    소분류: '',
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);

  useEffect(() => {
    loadDocuments();
  }, [page, rowsPerPage, categoryFilter]);

  /**
   * 문서 목록 로드
   */
  const loadDocuments = async () => {
    try {
      // 실제 API 호출
      const skip = (page - 1) * rowsPerPage;
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: rowsPerPage.toString(),
      });

      // 카테고리 필터 적용
      if (categoryFilter && categoryFilter !== '전체') {
        params.append('category', categoryFilter);
      }

      const response = await axios.get(`${API_BASE}/documents?${params}`);
      const data = response.data;

      setDocuments(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('문서 목록 로딩 실패:', error);
      // 오류 발생 시 빈 목록 표시
      setDocuments([]);
      setTotal(0);
    }
  };

  /**
   * 검색
   */
  const handleSearch = () => {
    setPage(1);
    loadDocuments();
  };

  /**
   * 초기화
   */
  const handleReset = () => {
    setCategoryFilter('전체');
    setSearchText('');
    setPage(1);
    loadDocuments();
  };

  /**
   * 전체 선택/해제
   */
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(documents.map((doc) => doc.id));
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
   * 카테고리 생성 모달 - 패턴 추가
   */
  const handleAddPattern = () => {
    setParsingPatterns([...parsingPatterns, { regex: '', type: 'sub title' }]);
  };

  /**
   * 카테고리 생성 모달 - 패턴 변경
   */
  const handlePatternChange = (index, field, value) => {
    const newPatterns = [...parsingPatterns];
    newPatterns[index][field] = value;
    setParsingPatterns(newPatterns);
  };

  /**
   * 카테고리 생성 저장
   */
  const handleSaveCategory = () => {
    console.log('카테고리 생성:', { categoryName, parsingPatterns });
    // TODO: API 호출
    setCategoryModalOpen(false);
    setCategoryName('');
    setParsingPatterns([{ regex: '', type: 'sub title' }]);
  };

  /**
   * 파일 업로드 핸들러
   */
  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    setUploadedFiles(files);
  };

  /**
   * 문서 등록 저장
   */
  const handleSaveUpload = () => {
    console.log('문서 등록:', { uploadCategory, uploadPath, uploadedFiles });
    // TODO: API 호출
    setUploadModalOpen(false);
    setUploadCategory('');
    setUploadPath({ 대분류: '', 중분류: '', 소분류: '' });
    setUploadedFiles([]);
  };

  /**
   * 선택 삭제
   */
  const handleDeleteSelected = () => {
    if (selected.length === 0) {
      alert('삭제할 문서를 선택해주세요.');
      return;
    }
    if (window.confirm(`선택한 ${selected.length}개 문서를 삭제하시겠습니까?`)) {
      console.log('삭제:', selected);
      // TODO: API 호출
      setSelected([]);
      loadDocuments();
    }
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = () => {
    const ws = XLSX.utils.json_to_sheet(
      documents.map((doc, index) => ({
        번호: (page - 1) * rowsPerPage + index + 1,
        카테고리: doc.category_name || '-',
        제목: doc.title,
        문서타입: doc.document_type,
        상태: doc.status,
        청크수: doc.vector_info?.total_chunks || 0,
        등록일: doc.created_at,
      }))
    );
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '대상문서관리');
    XLSX.writeFile(wb, `대상문서관리_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  return (
    <Box sx={{ p: 4, width: '100%', boxSizing: 'border-box' }}>
      {/* 제목 */}
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 'bold' }}>
        학습데이터관리
      </Typography>
      <Typography variant="h5" sx={{ mb: 3, color: '#666' }}>
        대상문서관리
      </Typography>

      {/* 검색 필터 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* 수집대상 토글 */}
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            수집대상
          </Typography>
          <ToggleButtonGroup
            value={categoryFilter}
            exclusive
            onChange={(e, value) => value && setCategoryFilter(value)}
            size="small"
          >
            <ToggleButton value="전체">전체</ToggleButton>
            {CATEGORIES.map((cat) => (
              <ToggleButton key={cat} value={cat}>
                {cat}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>

          {/* 검색창 */}
          <TextField
            size="small"
            placeholder="검색어 입력"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            sx={{ minWidth: 200 }}
          />

          {/* 검색/초기화 버튼 */}
          <Button variant="contained" startIcon={<SearchIcon />} onClick={handleSearch}>
            검색
          </Button>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleReset}>
            초기화
          </Button>

          {/* 카테고리생성 버튼 (오른쪽 끝) */}
          <Box sx={{ ml: 'auto' }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCategoryModalOpen(true)}
              sx={{ bgcolor: '#28a745', '&:hover': { bgcolor: '#218838' } }}
            >
              카테고리생성
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* 카테고리 통계 박스 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(CATEGORY_COUNTS).map(([category, count]) => (
          <Grid item xs={12} sm={6} md={4} lg={1.33} key={category}>
            <Card
              elevation={3}
              sx={{
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: categoryFilter === category ? '2px solid #1976d2' : '2px solid transparent',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
              onClick={() => setCategoryFilter(category)}
            >
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {category}
                </Typography>
                <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                  {count.toLocaleString()}건
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

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
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadModalOpen(true)}
            sx={{ bgcolor: '#17a2b8', '&:hover': { bgcolor: '#138496' } }}
          >
            문서등록
          </Button>
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
      </Box>

      {/* 테이블 */}
      <TableContainer component={Paper} elevation={3}>
        <Table sx={{ width: '100%' }}>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={documents.length > 0 && selected.length === documents.length}
                  indeterminate={selected.length > 0 && selected.length < documents.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>카테고리</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>제목</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>문서타입</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>상태</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>청크수</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>삭제</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>등록일</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.map((doc, index) => (
              <TableRow key={doc.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.indexOf(doc.id) !== -1}
                    onChange={() => handleSelect(doc.id)}
                  />
                </TableCell>
                <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                <TableCell>{doc.category_name || '-'}</TableCell>
                <TableCell>{doc.title}</TableCell>
                <TableCell>{doc.document_type}</TableCell>
                <TableCell>{doc.status}</TableCell>
                <TableCell>{doc.vector_info?.total_chunks ? doc.vector_info.total_chunks.toLocaleString() : '-'}</TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => {
                      if (window.confirm('이 문서를 삭제하시겠습니까?')) {
                        console.log('삭제:', doc.id);
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
                <TableCell>{doc.created_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 삭제 버튼 */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
        <Button
          variant="contained"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={handleDeleteSelected}
          disabled={selected.length === 0}
        >
          삭제 ({selected.length})
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

      {/* 카테고리 생성 모달 */}
      <Dialog open={categoryModalOpen} onClose={() => setCategoryModalOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>카테고리 생성</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {/* 카테고리명 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="body1" sx={{ minWidth: 120 }}>
                카테고리명
              </Typography>
              <TextField
                fullWidth
                size="small"
                placeholder="카테고리명 입력"
                value={categoryName}
                onChange={(e) => setCategoryName(e.target.value)}
              />
            </Box>

            {/* 패시징 패턴 */}
            {parsingPatterns.map((pattern, index) => (
              <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Typography variant="body1" sx={{ minWidth: 120 }}>
                  패시징 패턴
                </Typography>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="정규식입력"
                  value={pattern.regex}
                  onChange={(e) => handlePatternChange(index, 'regex', e.target.value)}
                />
                <Select
                  size="small"
                  value={pattern.type}
                  onChange={(e) => handlePatternChange(index, 'type', e.target.value)}
                  sx={{ minWidth: 120 }}
                >
                  <MenuItem value="sub title">sub title</MenuItem>
                  <MenuItem value="third title">third title</MenuItem>
                  <MenuItem value="content">content</MenuItem>
                </Select>
                {index === parsingPatterns.length - 1 && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={handleAddPattern}
                  >
                    추가
                  </Button>
                )}
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCategoryModalOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSaveCategory}>
            저장
          </Button>
        </DialogActions>
      </Dialog>

      {/* 문서 등록 모달 */}
      <Dialog open={uploadModalOpen} onClose={() => setUploadModalOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>대상 문서 업로드</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              1. 먼저 카테고리를 선택하세요.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              2. 폴더 생성 버튼을 클릭하여 새로운 경로를 추가할 수 있습니다.
            </Typography>

            {/* 카테고리 선택 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="body1" sx={{ minWidth: 100 }}>
                카테고리 선택
              </Typography>
              <Select
                fullWidth
                size="small"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                displayEmpty
              >
                <MenuItem value="">선택하세요</MenuItem>
                {CATEGORIES.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat}
                  </MenuItem>
                ))}
              </Select>
            </Box>

            {/* 경로 선택 */}
            <Typography variant="h6" sx={{ mb: 2 }}>
              경로
            </Typography>

            {/* 대분류 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="body1" sx={{ minWidth: 100 }}>
                대분류
              </Typography>
              <Select
                fullWidth
                size="small"
                value={uploadPath.대분류}
                onChange={(e) => setUploadPath({ ...uploadPath, 대분류: e.target.value, 중분류: '', 소분류: '' })}
                displayEmpty
              >
                <MenuItem value="">선택하세요</MenuItem>
                {PATH_OPTIONS.대분류.map((item) => (
                  <MenuItem key={item} value={item}>
                    {item}
                  </MenuItem>
                ))}
              </Select>
              <Button variant="outlined" size="small" startIcon={<FolderIcon />}>
                폴더생성
              </Button>
            </Box>

            {/* 중분류 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="body1" sx={{ minWidth: 100 }}>
                중분류
              </Typography>
              <Select
                fullWidth
                size="small"
                value={uploadPath.중분류}
                onChange={(e) => setUploadPath({ ...uploadPath, 중분류: e.target.value, 소분류: '' })}
                displayEmpty
                disabled={!uploadPath.대분류}
              >
                <MenuItem value="">선택하세요</MenuItem>
                {uploadPath.대분류 === '법령' &&
                  PATH_OPTIONS.중분류['법령'].map((item) => (
                    <MenuItem key={item} value={item}>
                      {item}
                    </MenuItem>
                  ))}
              </Select>
              <Button variant="outlined" size="small" startIcon={<FolderIcon />}>
                폴더생성
              </Button>
            </Box>

            {/* 소분류 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="body1" sx={{ minWidth: 100 }}>
                소분류
              </Typography>
              <Select
                fullWidth
                size="small"
                value={uploadPath.소분류}
                onChange={(e) => setUploadPath({ ...uploadPath, 소분류: e.target.value })}
                displayEmpty
                disabled={!uploadPath.중분류}
              >
                <MenuItem value="">선택하세요</MenuItem>
                {PATH_OPTIONS.소분류[uploadPath.중분류]?.map((item) => (
                  <MenuItem key={item} value={item}>
                    {item}
                  </MenuItem>
                ))}
              </Select>
              <Button variant="outlined" size="small" startIcon={<FolderIcon />}>
                폴더생성
              </Button>
            </Box>

            {/* 파일 업로드 */}
            <Button
              variant="contained"
              component="label"
              startIcon={<UploadIcon />}
              fullWidth
              sx={{ mb: 2 }}
            >
              파일 업로드
              <input type="file" hidden multiple onChange={handleFileUpload} />
            </Button>

            {/* 파일명 목록 */}
            <Box
              sx={{
                border: '1px solid #ddd',
                borderRadius: 1,
                p: 2,
                minHeight: 100,
                maxHeight: 200,
                overflowY: 'auto',
                bgcolor: '#f9f9f9',
              }}
            >
              {uploadedFiles.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  업로드된 파일이 없습니다.
                </Typography>
              ) : (
                uploadedFiles.map((file, index) => (
                  <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                    {file.name}
                  </Typography>
                ))
              )}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadModalOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSaveUpload}>
            저장
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
