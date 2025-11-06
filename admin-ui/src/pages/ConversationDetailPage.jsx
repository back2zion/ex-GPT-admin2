/**
 * 대화내역 상세 페이지
 * - 사용자 정보, 질문/답변/추론 내용 표시
 * - 목록으로 돌아가기 버튼
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
  Tabs,
  Tab,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getConversationDetail } from '../utils/api';

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
 * 대화내역 상세 페이지 컴포넌트
 */
export default function ConversationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [sessionData, setSessionData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);

  /**
   * 대화내역 상세 로드
   */
  useEffect(() => {
    const loadDetail = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getConversationDetail(id);
        setSessionData(data);
      } catch (err) {
        console.error('[ConversationDetailPage] 상세 조회 실패:', err);
        setError(err.response?.data?.detail || '대화내역을 불러올 수 없습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    loadDetail();
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

  if (!sessionData || !sessionData.conversations || sessionData.conversations.length === 0) {
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

  const firstConversation = sessionData.conversations[0];

  return (
    <Box sx={{ p: 4, maxWidth: 1400, margin: '0 auto' }}>
      {/* 헤더 */}
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold' }}>
        💬 대화내역 상세 (세션 ID: {sessionData.session_id})
      </Typography>

      {/* 사용자 정보 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
          📋 사용자 정보
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">사용자 ID</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.user_id}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">직급</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.position || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">직위</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.rank || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">팀명</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.team || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">입사년도</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.join_year || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">부처</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {firstConversation.department || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="body2" color="text.secondary">대화 개수</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {sessionData.conversations.length}개
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* 대화 탭 */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={(e, newValue) => setSelectedTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {sessionData.conversations.map((conversation, index) => (
            <Tab
              key={conversation.id}
              label={`대화 #${index + 1}`}
              id={`conversation-tab-${index}`}
            />
          ))}
        </Tabs>

        {/* 선택된 대화 내용 */}
        {sessionData.conversations.map((conversation, index) => (
          <Box
            key={conversation.id}
            role="tabpanel"
            hidden={selectedTab !== index}
            id={`conversation-tabpanel-${index}`}
            sx={{ p: 3 }}
          >
            {selectedTab === index && (
              <>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                  🔹 대화 #{index + 1} (ID: {conversation.id})
                </Typography>

                {/* 대화 분류 및 시간 정보 */}
                <Paper elevation={2} sx={{ p: 2, mb: 2, bgcolor: '#fafafa' }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={3}>
                      <Typography variant="body2" color="text.secondary">대분류</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {conversation.main_category || '미분류'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <Typography variant="body2" color="text.secondary">소분류</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {conversation.sub_category || '-'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="body2" color="text.secondary">질문 시간</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {formatDateTime(conversation.created_at)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={2}>
                      <Typography variant="body2" color="text.secondary">응답 시간</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {conversation.response_time ? `${conversation.response_time}ms` : '-'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>

                {/* 질문 내용 */}
                <Card elevation={3} sx={{ mb: 2, bgcolor: '#f0f8ff' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                      ❓ 질문 내용
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                      {conversation.question}
                    </Typography>
                  </CardContent>
                </Card>

                {/* 추론 내용 */}
                {conversation.thinking_content && (
                  <Card elevation={3} sx={{ mb: 2, bgcolor: '#fff8e1' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#f57c00' }}>
                        🤔 추론 내용
                      </Typography>
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                        {conversation.thinking_content}
                      </Typography>
                    </CardContent>
                  </Card>
                )}

                {/* 답변 내용 */}
                <Card elevation={3} sx={{ mb: 2, bgcolor: '#f1f8e9' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#388e3c' }}>
                      💬 답변 내용
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                      {conversation.answer || '답변 없음'}
                    </Typography>
                  </CardContent>
                </Card>

                {/* 참조 문서 */}
                {conversation.referenced_documents && conversation.referenced_documents.length > 0 && (
                  <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold', color: 'primary.main' }}>
                      📚 참조 문서
                    </Typography>
                    <ul>
                      {conversation.referenced_documents.map((doc, docIndex) => (
                        <li key={docIndex}>
                          <Typography variant="body2">{doc}</Typography>
                        </li>
                      ))}
                    </ul>
                  </Paper>
                )}
              </>
            )}
          </Box>
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
