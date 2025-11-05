/**
 * 알림 전체보기 페이지
 * PRD FUN-002: 제·개정 문서 알림
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
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
  Chip,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  MarkEmailRead as MarkReadIcon,
} from '@mui/icons-material';
import axios from 'axios';

/**
 * 알림 카테고리 매핑
 */
const CATEGORY_MAP = {
  all: '전체',
  document_update: '문서 업데이트',
  system: '시스템',
  deployment: '배포',
  stt_batch: 'STT 배치',
};

/**
 * 알림 아이콘 반환
 */
const getNotificationIcon = (type) => {
  switch (type) {
    case 'success':
      return <CheckCircleIcon sx={{ color: '#10b981', fontSize: 20 }} />;
    case 'error':
      return <ErrorIcon sx={{ color: '#ef4444', fontSize: 20 }} />;
    case 'warning':
      return <WarningIcon sx={{ color: '#f59e0b', fontSize: 20 }} />;
    case 'info':
    default:
      return <InfoIcon sx={{ color: '#3b82f6', fontSize: 20 }} />;
  }
};

/**
 * 알림 타입 Chip 색상
 */
const getTypeColor = (type) => {
  switch (type) {
    case 'success':
      return 'success';
    case 'error':
      return 'error';
    case 'warning':
      return 'warning';
    case 'info':
    default:
      return 'info';
  }
};

/**
 * 날짜 포맷팅
 */
function formatDateTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 60) {
    return `${diffMins}분 전`;
  } else if (diffMins < 1440) {
    return `${Math.floor(diffMins / 60)}시간 전`;
  } else if (diffMins < 10080) {
    return `${Math.floor(diffMins / 1440)}일 전`;
  } else {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  }
}

/**
 * 알림 전체보기 페이지 컴포넌트
 */
export default function NotificationsPage() {
  const navigate = useNavigate();

  // 필터
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [readFilter, setReadFilter] = useState('all'); // all, read, unread

  // 페이지네이션
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);

  // 데이터 상태
  const [notifications, setNotifications] = useState([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // 로딩 상태
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * 알림 목록 로드
   */
  const loadNotifications = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = {
        skip: (page - 1) * limit,
        limit,
      };

      // 카테고리 필터
      if (categoryFilter !== 'all') {
        params.category = categoryFilter;
      }

      // 읽음 필터
      if (readFilter === 'read') {
        params.is_read = true;
      } else if (readFilter === 'unread') {
        params.is_read = false;
      }

      const token = localStorage.getItem('authToken');
      const response = await axios.get('/api/v1/admin/notifications', {
        params,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setNotifications(response.data.items);
      setTotal(response.data.total);
      setUnreadCount(response.data.unread_count);
      setTotalPages(Math.ceil(response.data.total / limit));
    } catch (error) {
      console.error('알림 로드 실패:', error);
      setError(error.response?.data?.detail || '알림을 불러오는 데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 알림을 읽음으로 표시
   */
  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('authToken');
      await axios.patch(
        `/api/v1/admin/notifications/${notificationId}/read`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // 목록 갱신
      loadNotifications();
    } catch (error) {
      console.error('읽음 처리 실패:', error);
    }
  };

  /**
   * 모두 읽음으로 표시
   */
  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('authToken');
      await axios.post(
        '/api/v1/admin/notifications/mark-all-read',
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // 목록 갱신
      loadNotifications();
    } catch (error) {
      console.error('전체 읽음 처리 실패:', error);
    }
  };

  /**
   * 알림 클릭 시 처리
   */
  const handleNotificationClick = (notification) => {
    // 읽지 않은 알림이면 읽음으로 표시
    if (!notification.is_read) {
      markAsRead(notification.id);
    }

    // 링크가 있으면 이동
    if (notification.link) {
      navigate(notification.link);
    }
  };

  // 초기 로드 및 필터 변경 시 로드
  useEffect(() => {
    loadNotifications();
  }, [page, categoryFilter, readFilter]);

  return (
    <Box sx={{ p: 3 }}>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#0a2986' }}>
            📢 알림
          </Typography>
          <Typography variant="body2" color="text.secondary">
            시스템 알림 및 제·개정 문서 알림
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {unreadCount > 0 && (
            <Button
              variant="outlined"
              startIcon={<MarkReadIcon />}
              onClick={markAllAsRead}
              size="small"
            >
              모두 읽음
            </Button>
          )}
          <IconButton onClick={loadNotifications} size="small" title="새로고침">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* 통계 */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="body2" color="text.secondary">
            전체 알림
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#0a2986' }}>
            {total}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="body2" color="text.secondary">
            미읽음 알림
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#ef4444' }}>
            {unreadCount}
          </Typography>
        </Paper>
      </Box>

      {/* 필터 */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>카테고리</InputLabel>
          <Select
            value={categoryFilter}
            label="카테고리"
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="all">전체</MenuItem>
            <MenuItem value="document_update">문서 업데이트</MenuItem>
            <MenuItem value="system">시스템</MenuItem>
            <MenuItem value="deployment">배포</MenuItem>
            <MenuItem value="stt_batch">STT 배치</MenuItem>
          </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>읽음 상태</InputLabel>
          <Select
            value={readFilter}
            label="읽음 상태"
            onChange={(e) => {
              setReadFilter(e.target.value);
              setPage(1);
            }}
          >
            <MenuItem value="all">전체</MenuItem>
            <MenuItem value="unread">미읽음</MenuItem>
            <MenuItem value="read">읽음</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* 에러 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* 알림 테이블 */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f8f9fa' }}>
              <TableCell width="50px">상태</TableCell>
              <TableCell width="80px">유형</TableCell>
              <TableCell width="120px">카테고리</TableCell>
              <TableCell>제목</TableCell>
              <TableCell>메시지</TableCell>
              <TableCell width="150px">시간</TableCell>
              <TableCell width="100px">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 5 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : notifications.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 5 }}>
                  <Typography variant="body2" color="text.secondary">
                    알림이 없습니다
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              notifications.map((notification) => (
                <TableRow
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  sx={{
                    cursor: notification.link ? 'pointer' : 'default',
                    backgroundColor: notification.is_read ? 'transparent' : 'rgba(59, 130, 246, 0.05)',
                    '&:hover': {
                      backgroundColor: notification.is_read
                        ? 'rgba(0, 0, 0, 0.04)'
                        : 'rgba(59, 130, 246, 0.1)',
                    },
                  }}
                >
                  <TableCell>{getNotificationIcon(notification.type)}</TableCell>
                  <TableCell>
                    <Chip
                      label={notification.type}
                      color={getTypeColor(notification.type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {CATEGORY_MAP[notification.category] || notification.category}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{ fontWeight: notification.is_read ? 400 : 600 }}
                    >
                      {notification.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {notification.message}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {formatDateTime(notification.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {!notification.is_read && (
                      <Button
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          markAsRead(notification.id);
                        }}
                      >
                        읽음
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(e, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
}
