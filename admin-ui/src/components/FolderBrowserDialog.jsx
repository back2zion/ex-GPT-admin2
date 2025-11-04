/**
 * 폴더 브라우저 대화상자
 * 서버 파일 시스템 탐색 기능
 */
import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Breadcrumbs,
    Link,
    Typography,
    CircularProgress,
    Alert,
    Box,
    Chip,
} from '@mui/material';
import {
    Folder as FolderIcon,
    AudioFile as AudioFileIcon,
    ArrowUpward as UpIcon,
    Home as HomeIcon,
} from '@mui/icons-material';

/**
 * 폴더 브라우저 대화상자 컴포넌트
 */
export default function FolderBrowserDialog({ open, onClose, onSelect, initialPath }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [roots, setRoots] = useState([]);
    const [currentPath, setCurrentPath] = useState(null);
    const [parentPath, setParentPath] = useState(null);
    const [entries, setEntries] = useState([]);

    // 루트 디렉토리 목록 로드
    useEffect(() => {
        if (open && !currentPath) {
            loadRootDirectories();
        }
    }, [open]);

    // 루트 디렉토리 목록 조회
    const loadRootDirectories = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/admin/file-browser/roots');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            setRoots(data);
            setCurrentPath(null);
            setEntries([]);
        } catch (err) {
            setError(`루트 디렉토리 로드 실패: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 디렉토리 내용 로드
    const loadDirectory = async (path) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(
                `/api/v1/admin/file-browser/list?path=${encodeURIComponent(path)}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            setCurrentPath(data.current_path);
            setParentPath(data.parent_path);
            setEntries(data.entries);
        } catch (err) {
            setError(`디렉토리 로드 실패: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // 폴더 클릭 핸들러
    const handleFolderClick = (entry) => {
        if (entry.is_directory) {
            loadDirectory(entry.path);
        }
    };

    // 상위 폴더 이동
    const handleGoUp = () => {
        if (parentPath) {
            loadDirectory(parentPath);
        } else {
            loadRootDirectories();
        }
    };

    // 경로 선택
    const handleSelect = () => {
        if (currentPath) {
            onSelect(currentPath);
            onClose();
        }
    };

    // 경로를 Breadcrumb으로 변환
    const getBreadcrumbs = () => {
        if (!currentPath) return [];

        const separator = currentPath.includes('\\') ? '\\' : '/';
        const parts = currentPath.split(separator).filter(p => p);

        return parts;
    };

    // 파일 크기 포맷
    const formatSize = (bytes) => {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="md"
            fullWidth
            PaperProps={{
                sx: { height: '80vh' }
            }}
        >
            <DialogTitle sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                pb: 2
            }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <FolderIcon />
                    <Typography variant="h6">폴더 선택</Typography>
                </Box>
            </DialogTitle>

            <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column' }}>
                {/* 현재 경로 표시 */}
                <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', backgroundColor: '#f5f5f5' }}>
                    {currentPath ? (
                        <Breadcrumbs maxItems={4} aria-label="breadcrumb">
                            <Chip
                                icon={<HomeIcon />}
                                label="루트"
                                onClick={loadRootDirectories}
                                size="small"
                                sx={{ cursor: 'pointer' }}
                            />
                            {getBreadcrumbs().map((part, index) => (
                                <Chip
                                    key={index}
                                    label={part}
                                    size="small"
                                />
                            ))}
                        </Breadcrumbs>
                    ) : (
                        <Typography variant="body2" color="text.secondary">
                            📁 서버의 루트 디렉토리를 선택하세요
                        </Typography>
                    )}
                </Box>

                {/* 에러 표시 */}
                {error && (
                    <Alert severity="error" sx={{ m: 2 }}>
                        {error}
                    </Alert>
                )}

                {/* 로딩 표시 */}
                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress />
                    </Box>
                )}

                {/* 폴더/파일 목록 */}
                {!loading && (
                    <List sx={{ flex: 1, overflow: 'auto', p: 0 }}>
                        {/* 상위 폴더 이동 버튼 */}
                        {(currentPath && parentPath) && (
                            <ListItem disablePadding>
                                <ListItemButton onClick={handleGoUp}>
                                    <ListItemIcon>
                                        <UpIcon color="action" />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary="상위 폴더"
                                        secondary=".."
                                        primaryTypographyProps={{ fontWeight: 'bold' }}
                                    />
                                </ListItemButton>
                            </ListItem>
                        )}

                        {/* 루트 디렉토리 목록 (currentPath가 없을 때) */}
                        {!currentPath && roots.map((root, index) => (
                            <ListItem key={index} disablePadding>
                                <ListItemButton
                                    onClick={() => loadDirectory(root.path)}
                                    disabled={!root.exists}
                                >
                                    <ListItemIcon>
                                        <FolderIcon color={root.exists ? 'primary' : 'disabled'} />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={root.name}
                                        secondary={root.exists ? root.path : `${root.path} (존재하지 않음)`}
                                    />
                                </ListItemButton>
                            </ListItem>
                        ))}

                        {/* 디렉토리 항목 */}
                        {currentPath && entries.map((entry, index) => (
                            <ListItem
                                key={index}
                                disablePadding
                                sx={{
                                    borderBottom: '1px solid #f0f0f0',
                                    '&:hover': {
                                        backgroundColor: '#f5f5f5'
                                    }
                                }}
                            >
                                <ListItemButton
                                    onClick={() => handleFolderClick(entry)}
                                    disabled={!entry.is_directory}
                                >
                                    <ListItemIcon>
                                        {entry.is_directory ? (
                                            <FolderIcon color="primary" />
                                        ) : (
                                            <AudioFileIcon color="action" />
                                        )}
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={entry.name}
                                        secondary={entry.is_directory ? '폴더' : formatSize(entry.size)}
                                        primaryTypographyProps={{
                                            fontWeight: entry.is_directory ? 'bold' : 'normal'
                                        }}
                                    />
                                </ListItemButton>
                            </ListItem>
                        ))}

                        {/* 빈 폴더 */}
                        {currentPath && entries.length === 0 && !loading && (
                            <Box sx={{ p: 4, textAlign: 'center' }}>
                                <Typography variant="body2" color="text.secondary">
                                    📭 이 폴더는 비어있거나 음성 파일이 없습니다
                                </Typography>
                            </Box>
                        )}
                    </List>
                )}
            </DialogContent>

            <DialogActions sx={{ p: 2, borderTop: '1px solid #e0e0e0' }}>
                <Button onClick={onClose} color="inherit">
                    취소
                </Button>
                <Button
                    onClick={handleSelect}
                    variant="contained"
                    disabled={!currentPath}
                    startIcon={<FolderIcon />}
                >
                    이 폴더 선택
                </Button>
            </DialogActions>
        </Dialog>
    );
}
