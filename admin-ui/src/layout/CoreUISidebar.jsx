/**
 * CoreUI 스타일 Sidebar
 * Collapsible + Dark Theme + Icon Menu
 */
import { Sidebar, useSidebarState } from 'react-admin';
import { Box } from '@mui/material';
import CoreUIMenu from './CoreUIMenu';

const CoreUISidebar = () => {
    const [open] = useSidebarState();

    return (
        <Sidebar
            sx={{
                '& .RaSidebar-fixed': {
                    marginTop: '0px',
                    paddingTop: '56px',
                    height: '100vh',
                    background: 'linear-gradient(180deg, #2c3e50 0%, #34495e 100%)',
                    boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    overflowX: 'hidden',
                    overflowY: 'auto',
                    width: open ? '240px' : '0px',
                    '&::-webkit-scrollbar': {
                        width: '6px',
                    },
                    '&::-webkit-scrollbar-track': {
                        background: 'rgba(255, 255, 255, 0.05)',
                    },
                    '&::-webkit-scrollbar-thumb': {
                        background: 'rgba(255, 255, 255, 0.2)',
                        borderRadius: '3px',
                        '&:hover': {
                            background: 'rgba(255, 255, 255, 0.3)',
                        },
                    },
                },
                '& .RaSidebar-docked': {
                    borderRight: 'none',
                },
                '& .MuiDrawer-paper': {
                    transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    width: open ? '240px' : '0px',
                    overflowX: 'hidden',
                },
            }}
        >
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                }}
            >
                {/* Navigation Title */}
                <Box
                    sx={{
                        px: 2,
                        py: 2,
                        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                >
                    <Box
                        sx={{
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: 'rgba(255, 255, 255, 0.5)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                        }}
                    >
                        NAVIGATION
                    </Box>
                </Box>

                {/* Menu */}
                <CoreUIMenu />

                {/* Footer */}
                {open && (
                    <Box
                        sx={{
                            mt: 'auto',
                            p: 2,
                            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                        }}
                    >
                        <img
                            src="/images/bg_logo_r.svg"
                            alt="한국도로공사"
                            style={{
                                maxWidth: '96px',
                                height: 'auto',
                                opacity: 0.7
                            }}
                        />
                    </Box>
                )}
            </Box>
        </Sidebar>
    );
};

export default CoreUISidebar;
