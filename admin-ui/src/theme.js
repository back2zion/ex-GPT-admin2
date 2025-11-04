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
        // 한국도로공사 Primary 컬러: 네이비 블루
        primary: {
            main: '#0a2986',
            light: '#3d4fa3',
            dark: '#061b5f',
            contrastText: '#ffffff',
        },
        // 한국도로공사 Secondary 컬러: 오렌지
        secondary: {
            main: '#e64701',
            light: '#eb6b34',
            dark: '#a13200',
            contrastText: '#ffffff',
        },
        // 배경 컬러
        background: {
            default: '#f8f8f8',
            paper: '#ffffff',
        },
        // 텍스트 컬러
        text: {
            primary: '#333333',
            secondary: '#7b7b7b',
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
                    backgroundColor: '#0a2986',
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
                        boxShadow: '0 2px 4px rgba(10, 41, 134, 0.2)',
                    },
                },
            },
        },
        // Card 스타일
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    boxShadow: '0 2px 4px rgba(10, 41, 134, 0.1)',
                    border: '1px solid #e4e4e4',
                },
            },
        },
        // Table 스타일
        MuiTableHead: {
            styleOverrides: {
                root: {
                    '& .MuiTableCell-head': {
                        backgroundColor: '#0a2986',
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
                        backgroundColor: '#f8f8f8',
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
                            borderColor: '#0a2986',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: '#0a2986',
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
