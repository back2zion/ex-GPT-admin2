/**
 * 한국도로공사 컬러 테마
 * Material-UI 테마 커스터마이징
 * 라이트 모드 & 다크 모드 지원
 */

import { defaultTheme } from 'react-admin';
import { createTheme } from '@mui/material/styles';

// 라이트 테마
export const lightTheme = createTheme({
    ...defaultTheme,
    palette: {
        mode: 'light',
        // 한국도로공사 Primary 컬러: 네이비 블루 (더 밝고 현대적)
        primary: {
            main: '#1e3a8a', // 약간 더 밝은 네이비
            light: '#3b5fc8',
            dark: '#0a2472',
            contrastText: '#ffffff',
        },
        // 한국도로공사 Secondary 컬러: 오렌지 (더 생동감)
        secondary: {
            main: '#f97316',
            light: '#fb923c',
            dark: '#ea580c',
            contrastText: '#ffffff',
        },
        // 배경 컬러 (더 부드러운 그레이)
        background: {
            default: '#f5f7fa',
            paper: '#ffffff',
        },
        // 텍스트 컬러
        text: {
            primary: '#1f2937',
            secondary: '#6b7280',
        },
        // 상태 컬러 (더 생동감 있게)
        success: {
            main: '#22c55e',
            light: '#4ade80',
            dark: '#16a34a',
        },
        warning: {
            main: '#f59e0b',
            light: '#fbbf24',
            dark: '#d97706',
        },
        error: {
            main: '#ef4444',
            light: '#f87171',
            dark: '#dc2626',
        },
        info: {
            main: '#3b82f6',
            light: '#60a5fa',
            dark: '#2563eb',
        },
    },
    typography: {
        fontFamily: [
            '-apple-system',
            'BlinkMacSystemFont',
            '"Segoe UI"',
            'Roboto',
            '"Noto Sans KR"',
            '"Helvetica Neue"',
            'Arial',
            'sans-serif',
        ].join(','),
    },
    components: {
        // AppBar 스타일 (더 현대적인 그라데이션)
        MuiAppBar: {
            styleOverrides: {
                root: {
                    background: 'linear-gradient(135deg, #1e3a8a 0%, #3b5fc8 100%)',
                    boxShadow: '0 4px 20px rgba(30, 58, 138, 0.15)',
                },
            },
        },
        // 버튼 스타일 (더 세련된 효과)
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    textTransform: 'none',
                    fontWeight: 600,
                    padding: '8px 20px',
                    transition: 'all 0.3s ease',
                },
                contained: {
                    boxShadow: '0 2px 8px rgba(30, 58, 138, 0.15)',
                    '&:hover': {
                        boxShadow: '0 6px 20px rgba(30, 58, 138, 0.25)',
                        transform: 'translateY(-2px)',
                    },
                },
                containedSecondary: {
                    boxShadow: '0 2px 8px rgba(249, 115, 22, 0.15)',
                    '&:hover': {
                        boxShadow: '0 6px 20px rgba(249, 115, 22, 0.25)',
                        transform: 'translateY(-2px)',
                    },
                },
            },
        },
        // Card 스타일 (더 부드러운 그림자)
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06)',
                    border: '1px solid #e5e7eb',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
                        transform: 'translateY(-4px)',
                    },
                },
            },
        },
        // Table 스타일 (더 세련된 헤더)
        MuiTableHead: {
            styleOverrides: {
                root: {
                    '& .MuiTableCell-head': {
                        background: 'linear-gradient(135deg, #1e3a8a 0%, #3b5fc8 100%)',
                        color: '#ffffff',
                        fontWeight: 700,
                        fontSize: '0.95rem',
                        letterSpacing: '0.5px',
                        padding: '16px',
                    },
                },
            },
        },
        MuiTableRow: {
            styleOverrides: {
                root: {
                    transition: 'background-color 0.2s ease',
                    '&:hover': {
                        backgroundColor: '#f0f4ff',
                    },
                    '&:nth-of-type(odd)': {
                        backgroundColor: '#fafbfc',
                    },
                },
            },
        },
        MuiTableCell: {
            styleOverrides: {
                root: {
                    padding: '14px 16px',
                    fontSize: '0.9rem',
                },
            },
        },
        // 입력 필드 스타일 (더 부드러운 transition)
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 8,
                        transition: 'all 0.3s ease',
                        '&:hover fieldset': {
                            borderColor: '#3b5fc8',
                            borderWidth: '2px',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: '#1e3a8a',
                            borderWidth: '2px',
                            boxShadow: '0 0 0 3px rgba(30, 58, 138, 0.1)',
                        },
                    },
                },
            },
        },
        // Chip 스타일 (뱃지용)
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    fontWeight: 600,
                },
                colorPrimary: {
                    background: 'linear-gradient(135deg, #1e3a8a 0%, #3b5fc8 100%)',
                },
                colorSecondary: {
                    background: 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)',
                },
            },
        },
        // Container 전체 너비 사용
        MuiContainer: {
            defaultProps: {
                maxWidth: false,
                disableGutters: true,
            },
            styleOverrides: {
                root: {
                    maxWidth: 'none !important',
                    width: '100% !important',
                    paddingLeft: '0 !important',
                    paddingRight: '0 !important',
                },
            },
        },
    },
});

// 다크 테마
export const darkTheme = createTheme({
    ...defaultTheme,
    palette: {
        mode: 'dark',
        // 한국도로공사 Primary 컬러: 네이비 블루 (다크 모드용)
        primary: {
            main: '#5b7bdb',
            light: '#7d96e3',
            dark: '#3d4fa3',
            contrastText: '#ffffff',
        },
        // 한국도로공사 Secondary 컬러: 오렌지 (다크 모드용)
        secondary: {
            main: '#ff6b35',
            light: '#ff8c61',
            dark: '#e64701',
            contrastText: '#ffffff',
        },
        // 배경 컬러 (다크)
        background: {
            default: '#1a1a1a',
            paper: '#2d2d2d',
        },
        // 텍스트 컬러 (다크)
        text: {
            primary: '#ffffff',
            secondary: '#b0b0b0',
        },
        // 상태 컬러
        success: {
            main: '#10b981',
        },
        warning: {
            main: '#f59e0b',
        },
        error: {
            main: '#ef4444',
        },
        info: {
            main: '#3b82f6',
        },
    },
    typography: {
        fontFamily: [
            '-apple-system',
            'BlinkMacSystemFont',
            '"Segoe UI"',
            'Roboto',
            '"Noto Sans KR"',
            '"Helvetica Neue"',
            'Arial',
            'sans-serif',
        ].join(','),
    },
    components: {
        // AppBar 스타일
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#1a1a1a',
                },
            },
        },
        // 버튼 스타일
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 4,
                    textTransform: 'none',
                    fontWeight: 500,
                },
                contained: {
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: '0 2px 4px rgba(91, 123, 219, 0.3)',
                    },
                },
            },
        },
        // Card 스타일
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                    border: '1px solid #404040',
                },
            },
        },
        // Table 스타일
        MuiTableHead: {
            styleOverrides: {
                root: {
                    '& .MuiTableCell-head': {
                        backgroundColor: '#2d2d2d',
                        color: '#ffffff',
                        fontWeight: 600,
                    },
                },
            },
        },
        MuiTableRow: {
            styleOverrides: {
                root: {
                    '&:hover': {
                        backgroundColor: '#353535',
                    },
                },
            },
        },
        // 입력 필드 스타일
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        '&:hover fieldset': {
                            borderColor: '#5b7bdb',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: '#5b7bdb',
                        },
                    },
                },
            },
        },
        // Container 전체 너비 사용
        MuiContainer: {
            defaultProps: {
                maxWidth: false,
                disableGutters: true,
            },
            styleOverrides: {
                root: {
                    maxWidth: 'none !important',
                    width: '100% !important',
                    paddingLeft: '0 !important',
                    paddingRight: '0 !important',
                },
            },
        },
    },
});

// 기본 export는 라이트 테마
export default lightTheme;
