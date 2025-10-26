/**
 * 대화내역 상세 페이지 (세션 기반 - 고도화)
 *
 * 기능:
 * - 세션 내 모든 대화를 시간순으로 표시
 * - 질문/답변/추론 내용 펼치기/접기
 * - 참조문서 펼치기/접기
 * - wisenut보다 나은 UX 제공
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import ThinkingIcon from '@mui/icons-material/Psychology';
import DocumentIcon from '@mui/icons-material/Description';
import TimeIcon from '@mui/icons-material/AccessTime';
import { getConversationDetail, getSessionConversations } from '../utils/api';

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
    second: '2-digit',
  });
}

/**
 * 응답시간을 사람이 읽기 쉬운 형태로 포맷
 */
function formatResponseTime(ms) {
  if (!ms) return '-';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}초`;
}

/**
 * 대화 카드 컴포넌트 (각 Q&A)
 */
function ConversationCard({ conversation, index }) {
  const [expanded, setExpanded] = useState(index === 0); // 첫 번째만 기본 펼침

  return (
    <Card elevation={2} sx={{ mb: 2, border: '1px solid #e0e0e0' }}>
      <CardContent>
        {/* 헤더: 질문 시간 + 응답시간 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <QuestionAnswerIcon color="primary" fontSize="small" />
            <Typography variant="body2" color="text.secondary">
              질문 #{index + 1}
            </Typography>
            <Chip
              label={formatDateTime(conversation.created_at)}
              size="small"
              variant="outlined"
            />
          </Box>
          {conversation.response_time && (
            <Chip
              icon={<TimeIcon />}
              label={formatResponseTime(conversation.response_time)}
              size="small"
              color="info"
            />
          )}
        </Box>

        {/* 질문 내용 */}
        <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 'bold',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: expanded ? 'normal' : 'nowrap',
              }}
            >
              {conversation.question}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* 추론 내용 (thinking) */}
              {conversation.thinking_content && (
                <Alert severity="info" icon={<ThinkingIcon />}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    🤔 AI 추론 과정
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      fontSize: '0.85rem',
                      fontFamily: 'monospace',
                      bgcolor: '#f5f5f5',
                      p: 1,
                      borderRadius: 1,
                      maxHeight: '200px',
                      overflow: 'auto',
                    }}
                  >
                    {conversation.thinking_content}
                  </Typography>
                </Alert>
              )}

              {/* 답변 내용 */}
              <Paper elevation={0} sx={{ bgcolor: '#f1f8e9', p: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: '#388e3c' }}>
                  💬 답변
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                  {conversation.answer || '답변 없음'}
                </Typography>
              </Paper>

              {/* 참조 문서 */}
              {conversation.referenced_documents && conversation.referenced_documents.length > 0 && (
                <Paper elevation={0} sx={{ bgcolor: '#e3f2fd', p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <DocumentIcon fontSize="small" color="primary" />
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1565c0' }}>
                      📚 참조 문서 ({conversation.referenced_documents.length}개)
                    </Typography>
                  </Box>
                  <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    {conversation.referenced_documents.map((doc, idx) => (
                      <Typography
                        key={idx}
                        component="li"
                        variant="body2"
                        sx={{ mb: 0.5, lineHeight: 1.6 }}
                      >
                        {doc}
                      </Typography>
                    ))}
                  </Box>
                </Paper>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      </CardContent>
    </Card>
  );
}

/**
 * 대화내역 상세 페이지 컴포넌트
 */
export default function ConversationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [firstConversation, setFirstConversation] = useState(null);
  const [sessionConversations, setSessionConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * 대화내역 로드 (단건 → 세션 전체)
   */
  useEffect(() => {
    const loadConversations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // 1. 먼저 ID로 단건 조회 (사용자 정보 등 메타데이터)
        const first = await getConversationDetail(id);
        setFirstConversation(first);

        // 2. session_id가 있으면 세션 전체 조회
        if (first.session_id) {
          const allConversations = await getSessionConversations(first.session_id);
          setSessionConversations(allConversations);
        } else {
          // session_id가 없으면 단건만 표시
          setSessionConversations([first]);
        }
      } catch (err) {
        console.error('[ConversationDetailPage] 조회 실패:', err);
        setError(err.response?.data?.detail || '대화내역을 불러올 수 없습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, [id]);

  /**
   * 목록으로 돌아가기
   */
  const handleBackToList = () => {
    navigate('/conversations');
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8d7da', color: '#721c24' }}>
          {error}
        </Paper>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handleBackToList}
          sx={{ mt: 3 }}
        >
          목록으로 돌아가기
        </Button>
      </Box>
    );
  }

  if (!firstConversation) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>대화내역을 찾을 수 없습니다.</Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handleBackToList}
          sx={{ mt: 3 }}
        >
          목록으로 돌아가기
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4, maxWidth: 1400, margin: '0 auto' }}>
      {/* 헤더 */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        💬 대화내역 상세
      </Typography>

      {/* 상세정보 (메타데이터) */}
      <Paper elevation={3} sx={{ p: 3, mb: 3, bgcolor: '#fafafa' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
          📋 상세 정보
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">사용자 ID</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.user_id}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">세션 ID</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold', fontSize: '0.85rem' }}>
              {firstConversation.session_id || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">대분류</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.main_category || '미분류'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">소분류</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.sub_category || '-'}
            </Typography>
          </Grid>
          {firstConversation.position && (
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">직급</Typography>
              <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                {firstConversation.position}
              </Typography>
            </Grid>
          )}
          {firstConversation.team && (
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">팀명</Typography>
              <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                {firstConversation.team}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* 대화 내역 (세션 내 모든 Q&A) */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            📝 대화 내역
          </Typography>
          <Chip
            label={`총 ${sessionConversations.length}개 대화`}
            color="primary"
            variant="outlined"
          />
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* 각 대화 카드 */}
        {sessionConversations.map((conv, index) => (
          <ConversationCard
            key={conv.id}
            conversation={conv}
            index={index}
          />
        ))}
      </Paper>

      {/* 목록으로 돌아가기 버튼 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<ArrowBackIcon />}
          onClick={handleBackToList}
          sx={{ minWidth: 200 }}
        >
          목록으로 돌아가기
        </Button>
      </Box>
    </Box>
  );
}
