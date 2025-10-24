/**
 * 폴더 업로드 대화상자
 * Windows 탐색기에서 폴더 선택 → 서버로 자동 업로드
 */
import React, { useState, useRef } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    LinearProgress,
    List,
    ListItem,
    ListItemText,
    Alert,
    TextField,
    Chip,
} from '@mui/material';
import {
    FolderOpen as FolderIcon,
    CloudUpload as UploadIcon,
    CheckCircle as SuccessIcon,
    Error as ErrorIcon,
} from '@mui/icons-material';

/**
 * 폴더 업로드 대화상자 컴포넌트
 */
export default function FolderUploadDialog({ open, onClose, onUploadComplete }) {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [targetFolder, setTargetFolder] = useState('');
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploadResult, setUploadResult] = useState(null);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    // 파일 확장자 필터
    const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'];

    // 폴더 선택 버튼 클릭
    const handleSelectFolder = () => {
        fileInputRef.current?.click();
    };

    // 폴더 선택됨
    const handleFolderSelected = (event) => {
        const files = Array.from(event.target.files);

        // 음성 파일만 필터링
        const audioFiles = files.filter(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return ALLOWED_EXTENSIONS.includes(ext);
        });

        setSelectedFiles(audioFiles);
        setError(null);
        setUploadResult(null);

        // 자동으로 폴더명 추천 (첫 번째 파일의 상대 경로에서 추출)
        if (audioFiles.length > 0 && audioFiles[0].webkitRelativePath) {
            const parts = audioFiles[0].webkitRelativePath.split('/');
            if (parts.length > 1) {
                const folderName = parts[0];
                setTargetFolder(`회의록/${folderName}`);
            }
        }
    };

    // 파일 크기 포맷
    const formatSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    };

    // 총 파일 크기 계산
    const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);

    // 업로드 실행
    const handleUpload = async () => {
        if (selectedFiles.length === 0) {
            setError('선택된 파일이 없습니다');
            return;
        }

        if (!targetFolder.trim()) {
            setError('저장할 폴더명을 입력하세요');
            return;
        }

        setUploading(true);
        setError(null);
        setUploadProgress(0);

        try {
            // FormData 생성
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            formData.append('target_folder', targetFolder);

            // 업로드 요청
            const response = await fetch('/api/v1/admin/file-upload/upload-folder', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            setUploadResult(result);
            setUploadProgress(100);

            // 업로드 완료 콜백
            if (onUploadComplete) {
                onUploadComplete(result.target_path);
            }
        } catch (err) {
            setError(`업로드 실패: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    // 대화상자 닫기
    const handleClose = () => {
        if (!uploading) {
            setSelectedFiles([]);
            setTargetFolder('');
            setUploadResult(null);
            setError(null);
            setUploadProgress(0);
            onClose();
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
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
                    <CloudUploadIcon />
                    <Typography variant="h6">폴더 업로드</Typography>
                </Box>
            </DialogTitle>

            <DialogContent sx={{ pt: 3 }}>
                {/* 폴더 선택 버튼 */}
                <Box sx={{ mb: 3 }}>
                    <input
                        ref={fileInputRef}
                        type="file"
                        webkitdirectory="true"
                        directory="true"
                        multiple
                        style={{ display: 'none' }}
                        onChange={handleFolderSelected}
                    />
                    <Button
                        variant="outlined"
                        size="large"
                        startIcon={<FolderIcon />}
                        onClick={handleSelectFolder}
                        disabled={uploading}
                        fullWidth
                        sx={{
                            py: 2,
                            borderColor: '#2196f3',
                            color: '#2196f3',
                            '&:hover': {
                                borderColor: '#1976d2',
                                backgroundColor: '#e3f2fd',
                            },
                        }}
                    >
                        Windows 탐색기에서 폴더 선택
                    </Button>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                        음성 파일(MP3, WAV, M4A 등)만 자동으로 필터링됩니다
                    </Typography>
                </Box>

                {/* 저장 폴더명 입력 */}
                {selectedFiles.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                        <TextField
                            label="서버 저장 경로"
                            value={targetFolder}
                            onChange={(e) => setTargetFolder(e.target.value)}
                            fullWidth
                            disabled={uploading}
                            placeholder="예: 회의록/2024-10"
                            helperText="서버의 /data/audio/ 하위 경로입니다"
                            sx={{
                                '& .MuiInputBase-root': {
                                    fontFamily: 'monospace',
                                },
                            }}
                        />
                    </Box>
                )}

                {/* 선택된 파일 목록 */}
                {selectedFiles.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="subtitle2">
                                선택된 파일: {selectedFiles.length}개
                            </Typography>
                            <Chip
                                label={`총 크기: ${formatSize(totalSize)}`}
                                size="small"
                                color="primary"
                            />
                        </Box>
                        <List
                            sx={{
                                maxHeight: 300,
                                overflow: 'auto',
                                border: '1px solid #e0e0e0',
                                borderRadius: 1,
                            }}
                        >
                            {selectedFiles.slice(0, 100).map((file, index) => (
                                <ListItem key={index} dense>
                                    <ListItemText
                                        primary={file.webkitRelativePath || file.name}
                                        secondary={formatSize(file.size)}
                                        primaryTypographyProps={{ fontSize: '0.85rem' }}
                                        secondaryTypographyProps={{ fontSize: '0.75rem' }}
                                    />
                                </ListItem>
                            ))}
                            {selectedFiles.length > 100 && (
                                <ListItem>
                                    <ListItemText
                                        primary={`... 외 ${selectedFiles.length - 100}개 파일`}
                                        primaryTypographyProps={{ fontStyle: 'italic', color: 'text.secondary' }}
                                    />
                                </ListItem>
                            )}
                        </List>
                    </Box>
                )}

                {/* 업로드 진행률 */}
                {uploading && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" gutterBottom>
                            업로드 중... {uploadProgress}%
                        </Typography>
                        <LinearProgress variant="determinate" value={uploadProgress} />
                    </Box>
                )}

                {/* 업로드 결과 */}
                {uploadResult && (
                    <Alert severity="success" icon={<SuccessIcon />} sx={{ mb: 2 }}>
                        <Typography variant="body2" gutterBottom>
                            ✅ 업로드 완료!
                        </Typography>
                        <Typography variant="caption" component="div">
                            • 성공: {uploadResult.total_count}개 파일
                        </Typography>
                        <Typography variant="caption" component="div">
                            • 총 크기: {formatSize(uploadResult.total_size)}
                        </Typography>
                        <Typography variant="caption" component="div">
                            • 저장 경로: {uploadResult.target_path}
                        </Typography>
                        {uploadResult.skipped_files?.length > 0 && (
                            <Typography variant="caption" component="div" sx={{ color: 'warning.main', mt: 1 }}>
                                ⚠️ 건너뛴 파일: {uploadResult.skipped_files.length}개
                            </Typography>
                        )}
                    </Alert>
                )}

                {/* 에러 메시지 */}
                {error && (
                    <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}
            </DialogContent>

            <DialogActions sx={{ p: 2, borderTop: '1px solid #e0e0e0' }}>
                <Button onClick={handleClose} disabled={uploading}>
                    {uploadResult ? '닫기' : '취소'}
                </Button>
                {!uploadResult && (
                    <Button
                        onClick={handleUpload}
                        variant="contained"
                        disabled={uploading || selectedFiles.length === 0 || !targetFolder.trim()}
                        startIcon={<UploadIcon />}
                    >
                        {uploading ? '업로드 중...' : '업로드 시작'}
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
}
