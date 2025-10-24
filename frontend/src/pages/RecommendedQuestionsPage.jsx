/**
 * 추천질문관리 페이지
 */
import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Pagination,
  Select,
  MenuItem,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import * as XLSX from 'xlsx';
import axios from '../axiosConfig';

const API_BASE = '/api/v1/admin';

/**
 * Mock 데이터 생성
 */
function generateMockQuestions(count) {
  const mockQuestions = [];

  for (let i = 1; i <= count; i++) {
    mockQuestions.push({
      id: i,
      title: `추천질문 ${i}`,
      is_active: i % 3 !== 0,
      created_at: new Date(2024, 0, i).toISOString().split('T')[0],
    });
  }
  return mockQuestions;
}

export default function RecommendedQuestionsPage() {
  // 테이블 상태
  const [questions, setQuestions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selected, setSelected] = useState([]);

  // 모달 상태
  const [registerModalOpen, setRegisterModalOpen] = useState(false);
  const [questionText, setQuestionText] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    loadQuestions();
  }, [page, rowsPerPage]);

  /**
   * 추천질문 목록 로드
   */
  const loadQuestions = () => {
    // TODO: 실제 API 연동
    const mockQuestions = generateMockQuestions(50);

    // 페이지네이션
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    setQuestions(mockQuestions.slice(start, end));
    setTotal(mockQuestions.length);
  };

  /**
   * 전체 선택/해제
   */
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(questions.map((q) => q.id));
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
   * 등록
   */
  const handleRegister = () => {
    console.log('추천질문 등록:', { questionText, isActive });
    // TODO: API 호출
    setRegisterModalOpen(false);
    setQuestionText('');
    setIsActive(true);
    loadQuestions();
  };

  /**
   * 선택 삭제
   */
  const handleDeleteSelected = () => {
    if (selected.length === 0) {
      alert('삭제할 추천질문을 선택해주세요.');
      return;
    }
    if (window.confirm(`선택한 ${selected.length}개 추천질문을 삭제하시겠습니까?`)) {
      console.log('삭제:', selected);
      // TODO: API 호출
      setSelected([]);
      loadQuestions();
    }
  };

  /**
   * 엑셀 다운로드
   */
  const handleDownloadExcel = () => {
    const ws = XLSX.utils.json_to_sheet(
      questions.map((q, index) => ({
        번호: (page - 1) * rowsPerPage + index + 1,
        제목: q.title,
        사용: q.is_active ? 'Y' : 'N',
        일자: q.created_at,
      }))
    );
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '추천질문관리');
    XLSX.writeFile(wb, `추천질문관리_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  return (
    <Box sx={{ p: 3 }}>
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
            startIcon={<AddIcon />}
            onClick={() => setRegisterModalOpen(true)}
            sx={{ bgcolor: '#17a2b8', '&:hover': { bgcolor: '#138496' } }}
          >
            등록
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
        <Table sx={{ minWidth: 800 }}>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={questions.length > 0 && selected.length === questions.length}
                  indeterminate={selected.length > 0 && selected.length < questions.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>번호</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>제목</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사용</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>일자</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {questions.map((question, index) => (
              <TableRow key={question.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selected.indexOf(question.id) !== -1}
                    onChange={() => handleSelect(question.id)}
                  />
                </TableCell>
                <TableCell>{(page - 1) * rowsPerPage + index + 1}</TableCell>
                <TableCell>{question.title}</TableCell>
                <TableCell>{question.is_active ? 'Y' : 'N'}</TableCell>
                <TableCell>{question.created_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 삭제 버튼 */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
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

      {/* 등록 모달 */}
      <Dialog open={registerModalOpen} onClose={() => setRegisterModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>추천질문 등록</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              * ex-GPT에 등록할 추천 질문을 입력합니다.
            </Typography>

            <TextField
              fullWidth
              multiline
              rows={4}
              placeholder="추천 질문을 입력하세요"
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                />
              }
              label="체크 해제 시 추천질문에 노출 되지 않습니다"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRegisterModalOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleRegister}>
            확인
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
