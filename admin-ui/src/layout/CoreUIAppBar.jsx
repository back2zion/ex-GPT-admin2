/**
 * CoreUI 스타일 AppBar (Header)
 * Dark background + Logo + User Menu + Notifications + Settings
 */
import {
    AppBar,
    Toolbar,
    Typography,
    IconButton,
    Box,
    Avatar,
    Menu,
    MenuItem,
    Badge,
    Divider,
    ListItemIcon,
    ListItemText,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Notifications as NotificationsIcon,
    Logout as LogoutIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Info as InfoIcon,
    Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { useSidebarState } from 'react-admin';
import { useNavigate } from 'react-router-dom';

const CoreUIAppBar = () => {
    const [open, setOpen] = useSidebarState();
    const navigate = useNavigate();

    // Menu states
    const [notificationAnchor, setNotificationAnchor] = useState(null);
    const [userAnchor, setUserAnchor] = useState(null);

    // Notifications
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    // User info
    const [userInfo, setUserInfo] = useState(() => {
        const saved = localStorage.getItem('user');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                return { name: '한국도로공사 감독관', email: 'hyeonbok@ex.co.kr', lastLogin: null };
            }
        }
        return { name: '한국도로공사 감독관', email: 'hyeonbok@ex.co.kr', lastLogin: null };
    });

    // 마지막 로그인 시간 포맷팅
    const formatLastLogin = (timestamp) => {
        if (!timestamp) {
            const saved = localStorage.getItem('lastLogin');
            if (!saved) return '정보 없음';
            timestamp = saved;
        }

        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);

            if (diffMins < 60) {
                return `${diffMins}분 전`;
            } else if (diffMins < 1440) {
                return `${Math.floor(diffMins / 60)}시간 전`;
            } else {
                const hours = date.getHours();
                const mins = date.getMinutes();
                const ampm = hours >= 12 ? '오후' : '오전';
                const hour12 = hours % 12 || 12;
                return `오늘 ${ampm} ${hour12}:${mins.toString().padStart(2, '0')}`;
            }
        } catch (e) {
            return '정보 없음';
        }
    };

    // Fetch notifications
    useEffect(() => {
        fetchNotifications();
        // Poll every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            // 테스트 환경: X-Test-Auth 사용
            const headers = {
                'X-Test-Auth': 'admin',
                'Accept': 'application/json',
            };

            // 미읽음 알림 개수 조회
            const countResponse = await fetch('/api/v1/admin/notifications/unread-count', {
                headers,
            });
            if (countResponse.ok) {
                const countData = await countResponse.json();
                setUnreadCount(countData.unread_count);
            }

            // 최근 알림 5개 조회
            const response = await fetch('/api/v1/admin/notifications?limit=5', {
                headers,
            });

            if (response.ok) {
                const data = await response.json();
                // API 데이터를 UI 포맷으로 변환
                const formattedNotifications = data.items.map(n => ({
                    id: n.id,
                    type: n.type,
                    title: n.title,
                    message: n.message,
                    time: formatNotificationTime(n.created_at),
                    read: n.is_read,
                    link: n.link,
                }));
                setNotifications(formattedNotifications);
            }
        } catch (error) {
            console.error('알림 가져오기 실패:', error);
        }
    };

    // 알림 시간 포맷팅
    const formatNotificationTime = (isoString) => {
        if (!isoString) return '';
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
            return '오늘';
        }
    };

    const handleNotificationOpen = (event) => {
        setNotificationAnchor(event.currentTarget);
    };

    const handleUserMenuOpen = (event) => {
        setUserAnchor(event.currentTarget);
    };

    const handleNotificationClose = () => {
        setNotificationAnchor(null);
    };

    const handleUserMenuClose = () => {
        setUserAnchor(null);
    };

    const handleLogout = () => {
        // Clear auth data
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('lastLogin');
        // Redirect to login page (react-admin hash routing)
        window.location.href = '/admin/#/login';
    };

    const handleMarkAllRead = () => {
        setNotifications(notifications.map(n => ({ ...n, read: true })));
        setUnreadCount(0);
    };

    const handleAllNotifications = () => {
        handleNotificationClose();
        navigate('/notifications');
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'success':
                return <CheckCircleIcon sx={{ color: '#10b981' }} />;
            case 'error':
                return <ErrorIcon sx={{ color: '#ef4444' }} />;
            case 'info':
            default:
                return <InfoIcon sx={{ color: '#3b82f6' }} />;
        }
    };

    return (
        <AppBar
            position="fixed"
            sx={{
                background: 'linear-gradient(135deg, #1e3a8a 0%, #3b5fc8 100%)',
                boxShadow: '0 4px 20px rgba(30, 58, 138, 0.15)',
                backdropFilter: 'blur(10px)',
                zIndex: (theme) => theme.zIndex.drawer + 1,
            }}
        >
            <Toolbar>
                {/* Sidebar Toggle */}
                <IconButton
                    edge="start"
                    color="inherit"
                    onClick={() => setOpen(!open)}
                    sx={{ mr: 2 }}
                >
                    <MenuIcon />
                </IconButton>

                {/* Logo & Title */}
                <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                    <img
                        src="/images/bg_logo_r.svg"
                        alt="한국도로공사"
                        style={{
                            height: '26px',
                            marginRight: '8px'
                        }}
                    />
                    <Typography
                        variant="h6"
                        component="div"
                        sx={{
                            fontWeight: 'bold',
                            background: 'linear-gradient(90deg, #ffffff 0%, #e0e7ff 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}
                    >
                        관리도구
                    </Typography>
                    <Box
                        sx={{
                            ml: 2,
                            px: 1.5,
                            py: 0.5,
                            backgroundColor: 'rgba(255, 255, 255, 0.1)',
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            fontWeight: 500,
                        }}
                    >
                        0.7
                    </Box>
                </Box>

                {/* Right Icons */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {/* Notifications */}
                    <IconButton color="inherit" onClick={handleNotificationOpen} title="알림">
                        <Badge badgeContent={unreadCount} color="error">
                            <NotificationsIcon />
                        </Badge>
                    </IconButton>

                    {/* Notifications Menu */}
                    <Menu
                        anchorEl={notificationAnchor}
                        open={Boolean(notificationAnchor)}
                        onClose={handleNotificationClose}
                        PaperProps={{
                            sx: {
                                mt: 1.5,
                                minWidth: 360,
                                maxWidth: 400,
                                maxHeight: 500,
                                borderRadius: 2,
                                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                            },
                        }}
                    >
                        <Box sx={{ px: 2, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="h6" sx={{ fontWeight: 600, color: '#0a2986' }}>
                                알림
                            </Typography>
                            {unreadCount > 0 && (
                                <Typography
                                    variant="caption"
                                    sx={{ color: '#3b82f6', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                                    onClick={handleMarkAllRead}
                                >
                                    모두 읽음
                                </Typography>
                            )}
                        </Box>
                        <Divider />
                        {notifications.length === 0 ? (
                            <MenuItem disabled>
                                <Typography variant="body2" color="text.secondary">
                                    새로운 알림이 없습니다
                                </Typography>
                            </MenuItem>
                        ) : (
                            notifications.map((notification) => (
                                <MenuItem
                                    key={notification.id}
                                    onClick={handleNotificationClose}
                                    sx={{
                                        py: 1.5,
                                        px: 2,
                                        backgroundColor: notification.read ? 'transparent' : 'rgba(59, 130, 246, 0.05)',
                                        '&:hover': {
                                            backgroundColor: notification.read ? 'rgba(0,0,0,0.04)' : 'rgba(59, 130, 246, 0.1)',
                                        },
                                    }}
                                >
                                    <ListItemIcon sx={{ minWidth: 40 }}>
                                        {getNotificationIcon(notification.type)}
                                    </ListItemIcon>
                                    <Box sx={{ flex: 1 }}>
                                        <Typography variant="body2" sx={{ fontWeight: notification.read ? 400 : 600 }}>
                                            {notification.title}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {notification.message}
                                        </Typography>
                                        <Typography variant="caption" sx={{ display: 'block', color: '#999', mt: 0.5 }}>
                                            {notification.time}
                                        </Typography>
                                    </Box>
                                </MenuItem>
                            ))
                        )}
                        <Divider />
                        <MenuItem
                            onClick={handleAllNotifications}
                            sx={{ justifyContent: 'center', color: '#0a2986', fontWeight: 600 }}
                        >
                            모두 보기
                        </MenuItem>
                    </Menu>

                    {/* User Menu */}
                    <IconButton
                        onClick={handleUserMenuOpen}
                        sx={{
                            ml: 1,
                            p: 0.5,
                            '&:hover': {
                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                            },
                        }}
                    >
                        <Avatar
                            sx={{
                                width: 36,
                                height: 36,
                                background: 'linear-gradient(135deg, #e64701 0%, #f97316 100%)',
                            }}
                        >
                            A
                        </Avatar>
                    </IconButton>

                    {/* User Menu */}
                    <Menu
                        anchorEl={userAnchor}
                        open={Boolean(userAnchor)}
                        onClose={handleUserMenuClose}
                        PaperProps={{
                            sx: {
                                mt: 1.5,
                                minWidth: 240,
                                borderRadius: 2,
                                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                            },
                        }}
                    >
                        <Box sx={{ px: 2, py: 1.5 }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {userInfo.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                {userInfo.email}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                <ScheduleIcon sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
                                마지막 로그인: {formatLastLogin(userInfo.lastLogin)}
                            </Typography>
                        </Box>
                        <Divider />

                        <MenuItem onClick={handleLogout} sx={{ color: '#f97316', '&:hover': { backgroundColor: '#fff7ed' } }}>
                            <ListItemIcon>
                                <LogoutIcon sx={{ color: '#f97316' }} />
                            </ListItemIcon>
                            <ListItemText primary="로그아웃" />
                        </MenuItem>
                    </Menu>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default CoreUIAppBar;
