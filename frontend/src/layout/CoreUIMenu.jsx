/**
 * CoreUI 스타일 메뉴
 * Icon + Text + Nested Menu + Active State
 */
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import {
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Collapse,
    Box,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    QuestionAnswer as ConversationsIcon,
    Campaign as NoticesIcon,
    Star as SatisfactionIcon,
    Mic as STTIcon,
    ExpandLess,
    ExpandMore,
    Storage as StorageIcon,
    School as VectorDataIcon,
    Security as SecurityIcon,
    Lock as DocumentPermissionIcon,
    AccountTree as ApprovalLineIcon,
    People as UsersIcon,
    MiscellaneousServices as ServicesIcon,
    Rocket as DeploymentIcon,
} from '@mui/icons-material';
import { useSidebarState } from 'react-admin';

const CoreUIMenu = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [open] = useSidebarState();
    const [expandedMenus, setExpandedMenus] = useState({
        permissions: false,
        learningData: false,
        services: false,
        deployment: false,
    });
    const [systemHealth, setSystemHealth] = useState({
        tomcat: { status: 'loading', label: '확인 중...' },
        database: { status: 'loading', label: '확인 중...' }
    });

    const handleMenuClick = (path) => {
        navigate(path);
    };

    const handleExpandClick = (menuKey) => {
        setExpandedMenus((prev) => ({
            ...prev,
            [menuKey]: !prev[menuKey],
        }));
    };

    const isActive = (path) => {
        return location.pathname === path;
    };

    // Health Check
    const checkSystemHealth = async () => {
        try {
            // Call health/ready endpoint which checks Tomcat and database
            const response = await axios.get('/api/v1/admin/health/ready');

            if (response.data.status === 'ready') {
                setSystemHealth({
                    tomcat: {
                        status: response.data.checks.tomcat === 'ok' ? 'healthy' : 'unhealthy',
                        label: response.data.checks.tomcat === 'ok' ? '정상' : '오류'
                    },
                    database: {
                        status: response.data.checks.database === 'ok' ? 'healthy' : 'unhealthy',
                        label: response.data.checks.database === 'ok' ? '정상' : '오류'
                    }
                });
            }
        } catch (error) {
            // If API call fails, try to parse error response
            if (error.response?.data?.checks) {
                setSystemHealth({
                    tomcat: {
                        status: error.response.data.checks.tomcat === 'ok' ? 'healthy' : 'unhealthy',
                        label: error.response.data.checks.tomcat === 'ok' ? '정상' : '오류'
                    },
                    database: {
                        status: error.response.data.checks.database === 'ok' ? 'healthy' : 'unhealthy',
                        label: error.response.data.checks.database === 'ok' ? '정상' : '오류'
                    }
                });
            } else {
                // Complete failure
                setSystemHealth({
                    tomcat: { status: 'unhealthy', label: '오류' },
                    database: { status: 'unknown', label: '알 수 없음' }
                });
            }
        }
    };

    useEffect(() => {
        // Check health immediately on mount
        checkSystemHealth();

        // Set up interval to check every 10 seconds
        const interval = setInterval(checkSystemHealth, 10000);

        // Cleanup interval on unmount
        return () => clearInterval(interval);
    }, []);

    const menuItemStyle = (active) => ({
        px: 2,
        py: 1.5,
        mb: 0.5,
        borderRadius: 0,
        borderLeft: active ? '4px solid #e64701' : '4px solid transparent',
        backgroundColor: active ? 'rgba(230, 71, 1, 0.15)' : 'transparent',
        color: active ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
        transition: 'all 0.2s',
        '&:hover': {
            backgroundColor: active ? 'rgba(230, 71, 1, 0.2)' : 'rgba(255, 255, 255, 0.05)',
            color: '#ffffff',
            borderLeftColor: active ? '#e64701' : 'rgba(255, 255, 255, 0.3)',
        },
    });

    const iconStyle = (active) => ({
        color: active ? '#e64701' : 'rgba(255, 255, 255, 0.6)',
        minWidth: 40,
    });

    return (
        <List
            sx={{
                flex: 1,
                py: 1,
                overflowY: 'auto',
            }}
        >
            {/* Dashboard */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleMenuClick('/')}
                    sx={menuItemStyle(isActive('/'))}
                >
                    <ListItemIcon sx={iconStyle(isActive('/'))}>
                        <DashboardIcon />
                    </ListItemIcon>
                    {open && <ListItemText primary="대시보드" />}
                </ListItemButton>
            </ListItem>

            {/* 대화내역 */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleMenuClick('/conversations')}
                    sx={menuItemStyle(isActive('/conversations'))}
                >
                    <ListItemIcon sx={iconStyle(isActive('/conversations'))}>
                        <ConversationsIcon />
                    </ListItemIcon>
                    {open && <ListItemText primary="대화내역" />}
                </ListItemButton>
            </ListItem>

            {/* 학습데이터 관리 (Expandable) */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleExpandClick('learningData')}
                    sx={{
                        ...menuItemStyle(false),
                        borderLeft: '4px solid transparent',
                    }}
                >
                    <ListItemIcon sx={iconStyle(false)}>
                        <VectorDataIcon />
                    </ListItemIcon>
                    {open && (
                        <>
                            <ListItemText primary="학습데이터 관리" />
                            {expandedMenus.learningData ? <ExpandLess /> : <ExpandMore />}
                        </>
                    )}
                </ListItemButton>
            </ListItem>

            {/* Nested Learning Data Menu */}
            <Collapse in={expandedMenus.learningData && open} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/vector-data/documents')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/vector-data/documents')}
                    >
                        <ListItemText
                            primary="대상 문서관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/vector-data/dictionaries')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/vector-data/dictionaries')}
                    >
                        <ListItemText
                            primary="사전관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>
                </List>
            </Collapse>

            {/* 권한 관리 (Expandable) - PRD P0 */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleExpandClick('permissions')}
                    sx={{
                        ...menuItemStyle(false),
                        borderLeft: '4px solid transparent',
                    }}
                >
                    <ListItemIcon sx={iconStyle(false)}>
                        <SecurityIcon />
                    </ListItemIcon>
                    {open && (
                        <>
                            <ListItemText primary="권한 관리" />
                            {expandedMenus.permissions ? <ExpandLess /> : <ExpandMore />}
                        </>
                    )}
                </ListItemButton>
            </ListItem>

            {/* Nested Permission Menu */}
            <Collapse in={expandedMenus.permissions && open} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/users')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/users')}
                    >
                        <ListItemIcon sx={{ ...iconStyle(isActive('/users')), minWidth: 30 }}>
                            <UsersIcon sx={{ fontSize: 18 }} />
                        </ListItemIcon>
                        <ListItemText
                            primary="사용자 관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/document-permissions')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/document-permissions')}
                    >
                        <ListItemIcon sx={{ ...iconStyle(isActive('/document-permissions')), minWidth: 30 }}>
                            <DocumentPermissionIcon sx={{ fontSize: 18 }} />
                        </ListItemIcon>
                        <ListItemText
                            primary="문서 권한"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/approval-lines')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/approval-lines')}
                    >
                        <ListItemIcon sx={{ ...iconStyle(isActive('/approval-lines')), minWidth: 30 }}>
                            <ApprovalLineIcon sx={{ fontSize: 18 }} />
                        </ListItemIcon>
                        <ListItemText
                            primary="결재라인"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>
                </List>
            </Collapse>

            {/* 부가서비스 관리 (Expandable) */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleExpandClick('services')}
                    sx={{
                        ...menuItemStyle(false),
                        borderLeft: '4px solid transparent',
                    }}
                >
                    <ListItemIcon sx={iconStyle(false)}>
                        <ServicesIcon />
                    </ListItemIcon>
                    {open && (
                        <>
                            <ListItemText primary="부가서비스 관리" />
                            {expandedMenus.services ? <ExpandLess /> : <ExpandMore />}
                        </>
                    )}
                </ListItemButton>
            </ListItem>

            {/* Nested Services Menu */}
            <Collapse in={expandedMenus.services && open} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/services/version')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/services/version')}
                    >
                        <ListItemText
                            primary="버전관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/notices')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/notices')}
                    >
                        <ListItemText
                            primary="공지사항"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/services/error-reports')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/services/error-reports')}
                    >
                        <ListItemText
                            primary="오류신고관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/services/recommended-questions')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/services/recommended-questions')}
                    >
                        <ListItemText
                            primary="추천질문관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/satisfaction')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/satisfaction')}
                    >
                        <ListItemText
                            primary="만족도조사"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>
                </List>
            </Collapse>

            {/* 배포관리 (Expandable) */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleExpandClick('deployment')}
                    sx={{
                        ...menuItemStyle(false),
                        borderLeft: '4px solid transparent',
                    }}
                >
                    <ListItemIcon sx={iconStyle(false)}>
                        <DeploymentIcon />
                    </ListItemIcon>
                    {open && (
                        <>
                            <ListItemText primary="배포관리" />
                            {expandedMenus.deployment ? <ExpandLess /> : <ExpandMore />}
                        </>
                    )}
                </ListItemButton>
            </ListItem>

            {/* Nested Deployment Menu */}
            <Collapse in={expandedMenus.deployment && open} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/deployment/models')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/deployment/models')}
                    >
                        <ListItemText
                            primary="모델 레지스트리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/deployment/services')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/deployment/services')}
                    >
                        <ListItemText
                            primary="모델 서비스 관리"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>

                    <ListItemButton
                        sx={{
                            ...menuItemStyle(isActive('/deployment/status')),
                            pl: 6,
                        }}
                        onClick={() => handleMenuClick('/deployment/status')}
                    >
                        <ListItemText
                            primary="시스템 배포 현황"
                            primaryTypographyProps={{
                                sx: { fontSize: '0.875rem' },
                            }}
                        />
                    </ListItemButton>
                </List>
            </Collapse>

            {/* STT 음성 전사 */}
            <ListItem disablePadding>
                <ListItemButton
                    onClick={() => handleMenuClick('/stt-batches')}
                    sx={menuItemStyle(isActive('/stt-batches'))}
                >
                    <ListItemIcon sx={iconStyle(isActive('/stt-batches'))}>
                        <STTIcon />
                    </ListItemIcon>
                    {open && <ListItemText primary="STT 음성 전사" />}
                </ListItemButton>
            </ListItem>

            {/* System Info */}
            {open && (
                <Box
                    sx={{
                        mt: 2,
                        mx: 2,
                        p: 2,
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: 2,
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                >
                    <Box
                        sx={{
                            display: 'flex',
                            alignItems: 'center',
                            mb: 1,
                        }}
                    >
                        <StorageIcon
                            sx={{
                                fontSize: 20,
                                mr: 1,
                                color: 'rgba(255, 255, 255, 0.5)',
                            }}
                        />
                        <Box
                            sx={{
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                color: 'rgba(255, 255, 255, 0.5)',
                            }}
                        >
                            시스템 상태
                        </Box>
                    </Box>
                    <Box
                        sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '0.7rem',
                            color: 'rgba(255, 255, 255, 0.7)',
                            mb: 0.5,
                        }}
                    >
                        <span>사용자 서버:</span>
                        <Box
                            component="span"
                            sx={{
                                color: systemHealth.tomcat.status === 'healthy' ? '#10b981' :
                                       systemHealth.tomcat.status === 'unhealthy' ? '#ef4444' : '#94a3b8',
                                fontWeight: 600,
                            }}
                        >
                            ● {systemHealth.tomcat.label}
                        </Box>
                    </Box>
                    <Box
                        sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '0.7rem',
                            color: 'rgba(255, 255, 255, 0.7)',
                        }}
                    >
                        <span>데이터베이스:</span>
                        <Box
                            component="span"
                            sx={{
                                color: systemHealth.database.status === 'healthy' ? '#10b981' :
                                       systemHealth.database.status === 'unhealthy' ? '#ef4444' : '#94a3b8',
                                fontWeight: 600,
                            }}
                        >
                            ● {systemHealth.database.label}
                        </Box>
                    </Box>
                </Box>
            )}
        </List>
    );
};

export default CoreUIMenu;
