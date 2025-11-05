/**
 * CoreUI 스타일 AppBar (Header)
 * Dark background + Logo + User Menu (Simplified)
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
    Divider,
    ListItemIcon,
    ListItemText,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Logout as LogoutIcon,
    Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { useSidebarState } from 'react-admin';

const CoreUIAppBar = () => {
    const [open, setOpen] = useSidebarState();

    // User menu state
    const [userAnchor, setUserAnchor] = useState(null);

    // User info
    const [userInfo] = useState(() => {
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

    const handleUserMenuOpen = (event) => {
        setUserAnchor(event.currentTarget);
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
