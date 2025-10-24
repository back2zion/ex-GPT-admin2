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
    Settings as SettingsIcon,
    Person as PersonIcon,
    Logout as LogoutIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    Info as InfoIcon,
    Brightness4 as DarkModeIcon,
    Language as LanguageIcon,
    Refresh as RefreshIcon,
    Email as EmailIcon,
    Assessment as ActivityIcon,
    Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useState, useEffect, useContext } from 'react';
import { useSidebarState, useLocaleState } from 'react-admin';
import { useNavigate } from 'react-router-dom';
import { ThemeContext } from '../App';

const CoreUIAppBar = () => {
    const [open, setOpen] = useSidebarState();
    const navigate = useNavigate();
    const { darkMode, toggleDarkMode } = useContext(ThemeContext);
    const [locale, setLocale] = useLocaleState();

    // Menu states
    const [notificationAnchor, setNotificationAnchor] = useState(null);
    const [settingsAnchor, setSettingsAnchor] = useState(null);
    const [userAnchor, setUserAnchor] = useState(null);

    // Notifications
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    // Settings
    const [emailNotifications, setEmailNotifications] = useState(() => {
        const saved = localStorage.getItem('emailNotifications');
        return saved === null ? true : saved === 'true';
    });

    // User info
    const [userInfo, setUserInfo] = useState(() => {
        const saved = localStorage.getItem('user');
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                return { name: '관리자', email: 'admin@example.com', lastLogin: null };
            }
        }
        return { name: '관리자', email: 'admin@example.com', lastLogin: null };
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
            // Mock notifications - 실제로는 API에서 가져옴
            const mockNotifications = [
                {
                    id: 1,
                    type: 'success',
                    title: 'vLLM 모델 서버 배포 완료',
                    message: 'GPU:0에 성공적으로 배포되었습니다',
                    time: '5분 전',
                    read: false,
                },
                {
                    id: 2,
                    type: 'error',
                    title: 'STT 배치 처리 실패',
                    message: '배치 #1234 처리 중 오류 발생',
                    time: '1시간 전',
                    read: false,
                },
                {
                    id: 3,
                    type: 'info',
                    title: '문서 벡터화 완료',
                    message: '500개 문서 벡터화 완료',
                    time: '2시간 전',
                    read: true,
                },
                {
                    id: 4,
                    type: 'info',
                    title: '신규 사용자 등록',
                    message: '10명의 신규 사용자가 등록되었습니다',
                    time: '오늘',
                    read: true,
                },
            ];

            setNotifications(mockNotifications);
            setUnreadCount(mockNotifications.filter(n => !n.read).length);
        } catch (error) {
            console.error('알림 가져오기 실패:', error);
        }
    };

    const handleNotificationOpen = (event) => {
        setNotificationAnchor(event.currentTarget);
    };

    const handleSettingsOpen = (event) => {
        setSettingsAnchor(event.currentTarget);
    };

    const handleUserMenuOpen = (event) => {
        setUserAnchor(event.currentTarget);
    };

    const handleNotificationClose = () => {
        setNotificationAnchor(null);
    };

    const handleSettingsClose = () => {
        setSettingsAnchor(null);
    };

    const handleUserMenuClose = () => {
        setUserAnchor(null);
    };

    const handleLogout = () => {
        // Clear auth data
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('lastLogin');
        // Redirect to login
        window.location.href = '/login';
    };

    const handleMarkAllRead = () => {
        setNotifications(notifications.map(n => ({ ...n, read: true })));
        setUnreadCount(0);
    };

    const handleLanguageChange = () => {
        const newLang = locale === 'ko' ? 'en' : 'ko';
        setLocale(newLang);
        localStorage.setItem('language', newLang);
    };

    const handleEmailNotificationToggle = (checked) => {
        setEmailNotifications(checked);
        localStorage.setItem('emailNotifications', checked);
    };

    const handleProfileClick = () => {
        handleUserMenuClose();
        // TODO: 프로필 페이지 구현 후 navigate('/profile');
        alert('프로필 페이지는 구현 예정입니다.');
    };

    const handleActivityClick = () => {
        handleUserMenuClose();
        // TODO: 활동 기록 페이지 구현 후 navigate('/activity');
        alert('활동 기록 페이지는 구현 예정입니다.');
    };

    const handleSettingsClick = () => {
        handleUserMenuClose();
        // TODO: 설정 페이지 구현 후 navigate('/settings');
        alert('설정 페이지는 구현 예정입니다.');
    };

    const handleAllNotifications = () => {
        handleNotificationClose();
        // TODO: 알림 페이지 구현 후 navigate('/notifications');
        alert('알림 전체 보기 페이지는 구현 예정입니다.');
    };

    const handleAllSettings = () => {
        handleSettingsClose();
        // TODO: 전체 설정 페이지 구현 후 navigate('/settings');
        alert('전체 설정 페이지는 구현 예정입니다.');
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
                background: 'linear-gradient(135deg, #0a2986 0%, #1e3a8a 100%)',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
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
                    <IconButton color="inherit" onClick={handleNotificationOpen}>
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

                    {/* Settings */}
                    <IconButton color="inherit" onClick={handleSettingsOpen}>
                        <SettingsIcon />
                    </IconButton>

                    {/* Settings Menu */}
                    <Menu
                        anchorEl={settingsAnchor}
                        open={Boolean(settingsAnchor)}
                        onClose={handleSettingsClose}
                        PaperProps={{
                            sx: {
                                mt: 1.5,
                                minWidth: 280,
                                borderRadius: 2,
                                boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                            },
                        }}
                    >
                        <Box sx={{ px: 2, py: 1.5 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600, color: '#0a2986' }}>
                                빠른 설정
                            </Typography>
                        </Box>
                        <Divider />

                        <MenuItem sx={{ py: 1.5 }}>
                            <ListItemIcon>
                                <DarkModeIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText primary="다크 모드" />
                            <Switch
                                checked={darkMode}
                                onChange={toggleDarkMode}
                                size="small"
                            />
                        </MenuItem>

                        <MenuItem sx={{ py: 1.5 }} onClick={handleLanguageChange}>
                            <ListItemIcon>
                                <LanguageIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText
                                primary={locale === 'ko' ? '언어' : 'Language'}
                                secondary={locale === 'ko' ? '한국어' : 'English'}
                            />
                        </MenuItem>

                        <MenuItem sx={{ py: 1.5 }}>
                            <ListItemIcon>
                                <RefreshIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText
                                primary="데이터 갱신"
                                secondary="30초마다"
                            />
                        </MenuItem>

                        <MenuItem sx={{ py: 1.5 }}>
                            <ListItemIcon>
                                <EmailIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText primary="이메일 알림" />
                            <Switch
                                checked={emailNotifications}
                                onChange={(e) => handleEmailNotificationToggle(e.target.checked)}
                                size="small"
                            />
                        </MenuItem>

                        <Divider />
                        <MenuItem
                            onClick={handleAllSettings}
                            sx={{ justifyContent: 'center', color: '#0a2986', fontWeight: 600 }}
                        >
                            전체 설정
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
                        </Box>
                        <Divider />

                        <MenuItem onClick={handleProfileClick}>
                            <ListItemIcon>
                                <PersonIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText primary="내 프로필" />
                        </MenuItem>

                        <MenuItem onClick={handleActivityClick}>
                            <ListItemIcon>
                                <ActivityIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText primary="활동 기록" />
                        </MenuItem>

                        <MenuItem onClick={handleSettingsClick}>
                            <ListItemIcon>
                                <SettingsIcon sx={{ color: '#0a2986' }} />
                            </ListItemIcon>
                            <ListItemText primary="설정" />
                        </MenuItem>

                        <Divider />
                        <Box sx={{ px: 2, py: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                                <ScheduleIcon sx={{ fontSize: 12, verticalAlign: 'middle', mr: 0.5 }} />
                                마지막 로그인: {formatLastLogin(userInfo.lastLogin)}
                            </Typography>
                        </Box>
                        <Divider />

                        <MenuItem onClick={handleLogout} sx={{ color: '#e64701' }}>
                            <ListItemIcon>
                                <LogoutIcon sx={{ color: '#e64701' }} />
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
