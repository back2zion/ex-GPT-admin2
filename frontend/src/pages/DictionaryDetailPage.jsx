/**
 * 사전 상세 페이지 - 용어 관리
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  InputAdornment,
  Chip,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  Upload as UploadIcon,
  ArrowBack as ArrowBackIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material';
import axios from '../axiosConfig';

const API_BASE = '/api/v1/admin';

export default function DictionaryDetailPage() {
  const { dictId } = useParams();
  const navigate = useNavigate();

  // 사전 정보
  const [dictionary, setDictionary] = useState(null);

  // 용어 목록 상태
  const [terms, setTerms] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(20);
  const [selected, setSelected] = useState([]);
  const [searchText, setSearchText] = useState('');

  // 모달 상태
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  // 용어 폼 데이터
  const [termForm, setTermForm] = useState({
    term_id: null,
    main_term: '',
    main_alias: '',
    alias_1: '',
    alias_2: '',
    alias_3: '',
    english_name: '',
    english_alias: '',
    category: '',
    definition: '',
    use_yn: true,
  });

  // CSV 업로드
  const [csvFile, setCsvFile] = useState(null);

  useEffect(() => {
    loadDictionary();
    loadTerms();
  }, [dictId, page, searchText]);

  /**
   * 사전 정보 로드
   */
  const loadDictionary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/dictionaries/${dictId}`);
      setDictionary(response.data);
    } catch (error) {
      console.error('사전 로딩 실패:', error);
      alert('사전을 찾을 수 없습니다.');
      navigate('/vector-data/dictionaries');
    }
  };

  /**
   * 용어 목록 로드
   */
  const loadTerms = async () => {
    try {
      const skip = (page - 1) * rowsPerPage;
      const params = new URLSearchParams({
        dict_id: dictId,
        skip: skip.toString(),
        limit: rowsPerPage.toString(),
      });

      if (searchText) {
        params.append('search', searchText);
      }

      const response = await axios.get(`${API_BASE}/dictionaries/terms/list?${params}`);
      setTerms(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('용어 목록 로딩 실패:', error);
      setTerms([]);
      setTotal(0);
    }
  };

  /**
   * 전체 선택/해제
   */
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(terms.map((term) => term.term_id));
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
      newSelected = [...selected, id];
    } else {
      newSelected = selected.filter((termId) => termId !== id);
    }

    setSelected(newSelected);
  };

  /**
   * 용어 추가 다이얼로그 열기
   */
  const handleOpenAddDialog = () => {
    setTermForm({
      term_id: null,
      main_term: '',
      main_alias: '',
      alias_1: '',
      alias_2: '',
      alias_3: '',
      english_name: '',
      english_alias: '',
      category: '',
      definition: '',
      use_yn: true,
    });
    setAddDialogOpen(true);
  };

  /**
   * 용어 수정 다이얼로그 열기
   */
  const handleOpenEditDialog = (term) => {
    setTermForm({
      term_id: term.term_id,
      main_term: term.main_term,
      main_alias: term.main_alias || '',
      alias_1: term.alias_1 || '',
      alias_2: term.alias_2 || '',
      alias_3: term.alias_3 || '',
      english_name: term.english_name || '',
      english_alias: term.english_alias || '',
      category: term.category || '',
      definition: term.definition || '',
      use_yn: term.use_yn,
    });
    setEditDialogOpen(true);
  };

  /**
   * 용어 추가
   */
  const handleAddTerm = async () => {
    if (!termForm.main_term.trim()) {
      alert('정식명칭을 입력해주세요.');
      return;
    }

    try {
      await axios.post(`${API_BASE}/dictionaries/terms`, {
        dict_id: parseInt(dictId),
        main_term: termForm.main_term.trim(),
        main_alias: termForm.main_alias.trim() || null,
        alias_1: termForm.alias_1.trim() || null,
        alias_2: termForm.alias_2.trim() || null,
        alias_3: termForm.alias_3.trim() || null,
        english_name: termForm.english_name.trim() || null,
        english_alias: termForm.english_alias.trim() || null,
        category: termForm.category.trim() || null,
        definition: termForm.definition.trim() || null,
        use_yn: termForm.use_yn,
      });

      alert('용어가 추가되었습니다.');
      setAddDialogOpen(false);
      loadTerms();
      loadDictionary(); // 단어수 업데이트
    } catch (error) {
      console.error('용어 추가 실패:', error);
      alert('용어 추가에 실패했습니다.');
    }
  };

  /**
   * 용어 수정
   */
  const handleUpdateTerm = async () => {
    if (!termForm.main_term.trim()) {
      alert('정식명칭을 입력해주세요.');
      return;
    }

    try {
      await axios.put(`${API_BASE}/dictionaries/terms/${termForm.term_id}`, {
        main_term: termForm.main_term.trim(),
        main_alias: termForm.main_alias.trim() || null,
        alias_1: termForm.alias_1.trim() || null,
        alias_2: termForm.alias_2.trim() || null,
        alias_3: termForm.alias_3.trim() || null,
        english_name: termForm.english_name.trim() || null,
        english_alias: termForm.english_alias.trim() || null,
        category: termForm.category.trim() || null,
        definition: termForm.definition.trim() || null,
        use_yn: termForm.use_yn,
      });

      alert('용어가 수정되었습니다.');
      setEditDialogOpen(false);
      loadTerms();
    } catch (error) {
      console.error('용어 수정 실패:', error);
      alert('용어 수정에 실패했습니다.');
    }
  };

  /**
   * 용어 삭제
   */
  const handleDeleteTerm = async (termId) => {
    if (window.confirm('이 용어를 삭제하시겠습니까?')) {
      try {
        await axios.delete(`${API_BASE}/dictionaries/terms/${termId}`);
        alert('용어가 삭제되었습니다.');
        loadTerms();
        loadDictionary(); // 단어수 업데이트
      } catch (error) {
        console.error('용어 삭제 실패:', error);
        alert('용어 삭제에 실패했습니다.');
      }
    }
  };

  /**
   * 선택 삭제
   */
  const handleDeleteSelected = async () => {
    if (selected.length === 0) {
      alert('삭제할 용어를 선택해주세요.');
      return;
    }
    if (window.confirm(`선택한 ${selected.length}개 용어를 삭제하시겠습니까?`)) {
      try {
        await axios.delete(`${API_BASE}/dictionaries/terms/batch`, {
          data: { term_ids: selected },
        });
        alert('선택한 용어가 삭제되었습니다.');
        setSelected([]);
        loadTerms();
        loadDictionary(); // 단어수 업데이트
      } catch (error) {
        console.error('삭제 실패:', error);
        alert('삭제에 실패했습니다.');
      }
    }
  };

  /**
   * CSV 업로드 처리
   */
  const handleCSVUpload = async () => {
    if (!csvFile) {
      alert('CSV 파일을 선택해주세요.');
      return;
    }

    try {
      const text = await csvFile.text();
      const lines = text.split('\n').filter((line) => line.trim());
      const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));

      // CSV 검증
      const expectedHeaders = [
        '정식명칭',
        '주요약칭',
        '추가약칭1',
        '추가약칭2',
        '추가약칭3',
        '영문명',
        '영문약칭',
        '분류',
      ];

      const isValidFormat = expectedHeaders.every((h) => headers.includes(h));
      if (!isValidFormat) {
        alert('CSV 형식이 올바르지 않습니다. 올바른 헤더: ' + expectedHeaders.join(', '));
        return;
      }

      // 데이터 파싱 및 업로드
      const rows = lines.slice(1);
      let successCount = 0;

      for (const row of rows) {
        const values = row.split(',').map((v) => v.trim().replace(/^"|"$/g, ''));
        const [
          main_term,
          main_alias,
          alias_1,
          alias_2,
          alias_3,
          english_name,
          english_alias,
          category,
        ] = values;

        if (!main_term) continue;

        try {
          await axios.post(`${API_BASE}/dictionaries/terms`, {
            dict_id: parseInt(dictId),
            main_term: main_term,
            main_alias: main_alias || null,
            alias_1: alias_1 || null,
            alias_2: alias_2 || null,
            alias_3: alias_3 || null,
            english_name: english_name || null,
            english_alias: english_alias || null,
            category: category || null,
            use_yn: true,
          });
          successCount++;
        } catch (error) {
          console.error('용어 추가 실패:', main_term, error);
        }
      }

      alert(`${successCount}개 용어가 추가되었습니다.`);
      setUploadDialogOpen(false);
      setCsvFile(null);
      loadTerms();
      loadDictionary(); // 단어수 업데이트
    } catch (error) {
      console.error('CSV 업로드 실패:', error);
      alert('CSV 업로드에 실패했습니다.');
    }
  };

  /**
   * CSV 다운로드 (템플릿)
   */
  const handleDownloadTemplate = () => {
    const headers = [
      '정식명칭',
      '주요약칭',
      '추가약칭1',
      '추가약칭2',
      '추가약칭3',
      '영문명',
      '영문약칭',
      '분류',
    ];
    const sampleRow = [
      '한국도로공사',
      '도로공사',
      '도공',
      '',
      '',
      'Korea Expressway Corporation',
      'KEC',
      '공기업',
    ];

    const csvContent = [headers.join(','), sampleRow.join(',')].join('\n');
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'dictionary_template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Breadcrumb */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          underline="hover"
          color="inherit"
          href="#/vector-data/dictionaries"
          sx={{ cursor: 'pointer' }}
        >
          사전 목록
        </Link>
        <Typography color="text.primary">
          {dictionary?.dict_name || '사전 상세'}
        </Typography>
      </Breadcrumbs>

      {/* 제목 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/vector-data/dictionaries')}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
            {dictionary?.dict_name || '사전'}
          </Typography>
          <Chip
            label={dictionary?.dict_type === 'synonym' ? '동의어사전' : '사용자사전'}
            color="primary"
            size="small"
          />
          <Chip label={`${total}개 용어`} size="small" />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* CSV 업로드 */}
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            CSV 업로드
          </Button>

          {/* 용어 추가 */}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenAddDialog}
            sx={{ bgcolor: '#17a2b8', '&:hover': { bgcolor: '#138496' } }}
          >
            용어 추가
          </Button>

          {/* 삭제 */}
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeleteSelected}
            disabled={selected.length === 0}
          >
            삭제
          </Button>
        </Box>
      </Box>

      {/* 검색 영역 */}
      <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2">
            총 <strong>{total.toLocaleString()}</strong>개
          </Typography>

          <TextField
            size="small"
            placeholder="용어 검색..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
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
      </Paper>

      {/* 테이블 */}
      <TableContainer component={Paper} elevation={3}>
        <Table sx={{ minWidth: 1200 }}>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={terms.length > 0 && selected.length === terms.length}
                  indeterminate={selected.length > 0 && selected.length < terms.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>정식명칭</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>주요약칭</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>추가약칭</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>영문명</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>영문약칭</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>분류</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사용</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>수정</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>삭제</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {terms.map((term) => (
              <TableRow key={term.term_id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.indexOf(term.term_id) !== -1}
                    onChange={() => handleSelect(term.term_id)}
                  />
                </TableCell>
                <TableCell>{term.main_term}</TableCell>
                <TableCell>{term.main_alias || '-'}</TableCell>
                <TableCell>
                  {[term.alias_1, term.alias_2, term.alias_3]
                    .filter(Boolean)
                    .join(', ') || '-'}
                </TableCell>
                <TableCell>{term.english_name || '-'}</TableCell>
                <TableCell>{term.english_alias || '-'}</TableCell>
                <TableCell>{term.category || '-'}</TableCell>
                <TableCell>{term.use_yn ? 'Y' : 'N'}</TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleOpenEditDialog(term)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleDeleteTerm(term.term_id)}>
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

      {/* 용어 추가 다이얼로그 */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        PaperProps={{
          sx: { width: '600px', maxWidth: '90vw' }
        }}
      >
        <DialogTitle>용어 추가</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="정식명칭 *"
              value={termForm.main_term}
              onChange={(e) => setTermForm({ ...termForm, main_term: e.target.value })}
              fullWidth
            />
            <TextField
              label="주요약칭"
              value={termForm.main_alias}
              onChange={(e) => setTermForm({ ...termForm, main_alias: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭1"
              value={termForm.alias_1}
              onChange={(e) => setTermForm({ ...termForm, alias_1: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭2"
              value={termForm.alias_2}
              onChange={(e) => setTermForm({ ...termForm, alias_2: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭3"
              value={termForm.alias_3}
              onChange={(e) => setTermForm({ ...termForm, alias_3: e.target.value })}
              fullWidth
            />
            <TextField
              label="영문명"
              value={termForm.english_name}
              onChange={(e) => setTermForm({ ...termForm, english_name: e.target.value })}
              fullWidth
            />
            <TextField
              label="영문약칭"
              value={termForm.english_alias}
              onChange={(e) => setTermForm({ ...termForm, english_alias: e.target.value })}
              fullWidth
            />
            <TextField
              label="분류"
              value={termForm.category}
              onChange={(e) => setTermForm({ ...termForm, category: e.target.value })}
              fullWidth
            />
          </Box>
          <TextField
            label="정의/설명"
            value={termForm.definition}
            onChange={(e) => setTermForm({ ...termForm, definition: e.target.value })}
            fullWidth
            multiline
            rows={3}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleAddTerm} autoFocus>
            추가
          </Button>
        </DialogActions>
      </Dialog>

      {/* 용어 수정 다이얼로그 */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        PaperProps={{
          sx: { width: '600px', maxWidth: '90vw' }
        }}
      >
        <DialogTitle>용어 수정</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="정식명칭 *"
              value={termForm.main_term}
              onChange={(e) => setTermForm({ ...termForm, main_term: e.target.value })}
              fullWidth
            />
            <TextField
              label="주요약칭"
              value={termForm.main_alias}
              onChange={(e) => setTermForm({ ...termForm, main_alias: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭1"
              value={termForm.alias_1}
              onChange={(e) => setTermForm({ ...termForm, alias_1: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭2"
              value={termForm.alias_2}
              onChange={(e) => setTermForm({ ...termForm, alias_2: e.target.value })}
              fullWidth
            />
            <TextField
              label="추가약칭3"
              value={termForm.alias_3}
              onChange={(e) => setTermForm({ ...termForm, alias_3: e.target.value })}
              fullWidth
            />
            <TextField
              label="영문명"
              value={termForm.english_name}
              onChange={(e) => setTermForm({ ...termForm, english_name: e.target.value })}
              fullWidth
            />
            <TextField
              label="영문약칭"
              value={termForm.english_alias}
              onChange={(e) => setTermForm({ ...termForm, english_alias: e.target.value })}
              fullWidth
            />
            <TextField
              label="분류"
              value={termForm.category}
              onChange={(e) => setTermForm({ ...termForm, category: e.target.value })}
              fullWidth
            />
          </Box>
          <TextField
            label="정의/설명"
            value={termForm.definition}
            onChange={(e) => setTermForm({ ...termForm, definition: e.target.value })}
            fullWidth
            multiline
            rows={3}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleUpdateTerm} autoFocus>
            수정
          </Button>
        </DialogActions>
      </Dialog>

      {/* CSV 업로드 다이얼로그 */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        PaperProps={{
          sx: { width: '500px', maxWidth: '90vw' }
        }}
      >
        <DialogTitle>CSV 파일 업로드</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Typography variant="body2" sx={{ mb: 2 }}>
            CSV 파일을 업로드하여 용어를 일괄 추가할 수 있습니다.
          </Typography>

          <Button
            variant="outlined"
            startIcon={<FileDownloadIcon />}
            onClick={handleDownloadTemplate}
            fullWidth
            sx={{ mb: 2 }}
          >
            CSV 템플릿 다운로드
          </Button>

          <input
            type="file"
            accept=".csv"
            onChange={(e) => setCsvFile(e.target.files[0])}
            style={{ width: '100%' }}
          />

          {csvFile && (
            <Typography variant="body2" sx={{ mt: 2, color: 'success.main' }}>
              선택된 파일: {csvFile.name}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleCSVUpload} autoFocus>
            업로드
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
