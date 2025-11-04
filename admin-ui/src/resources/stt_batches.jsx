/**
 * STT Batches Resource - react-admin
 * 음성 전사 배치 관리 (500만건 처리)
 *
 * 기능:
 * - 배치 목록 조회 (진행률, 상태)
 * - 배치 상세보기 (전사 결과, 진행 상황)
 * - 실시간 진행률 모니터링
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    ShowButton,
    Show,
    SimpleShowLayout,
    Filter,
    SelectInput,
    useRecordContext,
    useRefresh,
    FunctionField,
    CreateButton,
    Create,
    SimpleForm,
    TextInput,
    required,
    useNotify,
    useRedirect,
} from 'react-admin';
import { useFormContext } from 'react-hook-form';
import {
    Box,
    Grid,
    Typography,
    Paper,
    Chip,
    LinearProgress,
    Card,
    CardContent,
    Button,
} from '@mui/material';
import { Mic as MicIcon, Folder as FolderIcon, CloudUpload as UploadIcon } from '@mui/icons-material';
import React, { useEffect, useState } from 'react';
import FolderBrowserDialog from '../components/FolderBrowserDialog';
import FolderUploadDialog from '../components/FolderUploadDialog';

/**
 * 상태 선택 옵션
 */
const statusChoices = [
    { id: 'pending', name: '대기 중' },
    { id: 'processing', name: '처리 중' },
    { id: 'completed', name: '완료' },
    { id: 'failed', name: '실패' },
    { id: 'paused', name: '일시정지' },
];

/**
 * 우선순위 선택 옵션
 */
const priorityChoices = [
    { id: 'low', name: '낮음' },
    { id: 'normal', name: '보통' },
    { id: 'high', name: '높음' },
    { id: 'urgent', name: '긴급' },
];

/**
 * 상태 칩 컴포넌트
 */
const StatusField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    const statusMap = {
        pending: { label: '대기 중', color: 'default' },
        processing: { label: '처리 중', color: 'primary' },
        completed: { label: '완료', color: 'success' },
        failed: { label: '실패', color: 'error' },
        paused: { label: '일시정지', color: 'warning' },
    };

    const status = statusMap[record.status] || { label: record.status, color: 'default' };

    return <Chip label={status.label} color={status.color} size="small" />;
};

/**
 * 우선순위 필드
 */
const PriorityField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    const priorityMap = {
        low: '낮음',
        normal: '보통',
        high: '높음',
        urgent: '긴급',
    };

    return <span>{priorityMap[record.priority] || record.priority}</span>;
};

/**
 * 진행률 바 컴포넌트
 */
const ProgressField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    const total = record.total_files || 0;
    const completed = record.completed_files || 0;
    const progress = total > 0 ? (completed / total) * 100 : 0;

    return (
        <Box sx={{ width: '100%', minWidth: 150 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                    {completed.toLocaleString()} / {total.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {progress.toFixed(1)}%
                </Typography>
            </Box>
            <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                        borderRadius: 1,
                        backgroundColor: progress === 100 ? '#4caf50' : '#2196f3',
                    },
                }}
            />
        </Box>
    );
};

/**
 * STT 배치 필터
 */
const STTBatchFilter = (props) => (
    <Filter {...props}>
        <SelectInput
            source="status"
            label="상태"
            choices={statusChoices}
            alwaysOn
        />
        <SelectInput
            source="priority"
            label="우선순위"
            choices={priorityChoices}
            alwaysOn
        />
    </Filter>
);

/**
 * Empty state 컴포넌트 (데이터가 없을 때)
 */
const EmptySTTList = () => (
    <Box
        sx={{
            textAlign: 'center',
            py: 8,
            px: 3,
        }}
    >
        <MicIcon
            sx={{
                fontSize: 80,
                color: 'rgba(0, 0, 0, 0.2)',
                mb: 2,
            }}
        />
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
            아직 STT 배치 작업이 없습니다
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            500만건의 음성파일을 처리할 배치 작업을 생성해보세요.
        </Typography>
        <CreateButton label="첫 배치 작업 만들기" />
    </Box>
);

/**
 * STT 배치 목록
 */
export const STTBatchList = () => (
    <List
        filters={<STTBatchFilter />}
        sort={{ field: 'created_at', order: 'DESC' }}
        perPage={25}
        title="🎙️ STT 음성 전사 배치"
        empty={<EmptySTTList />}
    >
        <Datagrid
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-table': {
                    tableLayout: 'fixed',
                    width: '100%'
                },
                '& .RaDatagrid-headerCell': {
                    height: '66px !important',
                    minHeight: '66px !important',
                    maxHeight: '66px !important',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    padding: '16px !important',
                    lineHeight: '24px',
                    verticalAlign: 'middle'
                },
                '& .RaDatagrid-rowCell': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    padding: '8px 16px !important'
                },
                // 각 컬럼 너비 고정
                '& .RaDatagrid-headerCell:nth-of-type(1), & .RaDatagrid-rowCell:nth-of-type(1)': { width: '80px', minWidth: '80px', maxWidth: '80px' },
                '& .RaDatagrid-headerCell:nth-of-type(2), & .RaDatagrid-rowCell:nth-of-type(2)': { width: '220px', minWidth: '220px', maxWidth: '220px' },
                '& .RaDatagrid-headerCell:nth-of-type(3), & .RaDatagrid-rowCell:nth-of-type(3)': { width: '110px', minWidth: '110px', maxWidth: '110px' },
                '& .RaDatagrid-headerCell:nth-of-type(4), & .RaDatagrid-rowCell:nth-of-type(4)': { width: '100px', minWidth: '100px', maxWidth: '100px' },
                '& .RaDatagrid-headerCell:nth-of-type(5), & .RaDatagrid-rowCell:nth-of-type(5)': { width: 'auto', minWidth: '250px' },
                '& .RaDatagrid-headerCell:nth-of-type(6), & .RaDatagrid-rowCell:nth-of-type(6)': { width: '180px', minWidth: '180px', maxWidth: '180px' },
                '& .RaDatagrid-headerCell:nth-of-type(7), & .RaDatagrid-rowCell:nth-of-type(7)': { width: '110px', minWidth: '110px', maxWidth: '110px' }
            }}
        >
            <TextField source="id" label="ID" />
            <TextField source="name" label="배치 이름" />
            <StatusField source="status" label="상태" />
            <PriorityField source="priority" label="우선순위" />
            <ProgressField source="progress" label="진행률" />
            <DateField
                source="created_at"
                label="생성일시"
                showTime
                options={{
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                }}
            />
            <ShowButton label="상세보기" />
        </Datagrid>
    </List>
);

/**
 * 진행 상황 카드 컴포넌트 (실시간 업데이트)
 */
const ProgressCard = ({ batchId }) => {
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProgress = async () => {
            try {
                // 상대 경로 사용 (프록시 통해 백엔드로 전달됨)
                const response = await fetch(`/api/v1/admin/stt-batches/${batchId}/progress`, {
                    headers: {
                        'Accept': 'application/json',
                        'X-Test-Auth': 'admin'  // 인증 헤더 추가
                    }
                });

                // 시큐어 코딩: HTTP 상태 검증 및 에러 핸들링
                if (!response.ok) {
                    console.error(`API Error: ${response.status} ${response.statusText}`);
                    setLoading(false);
                    return;
                }

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    console.error('Invalid content type:', contentType);
                    setLoading(false);
                    return;
                }

                const data = await response.json();
                setProgress(data);
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch progress:', error);
                setLoading(false);
            }
        };

        fetchProgress();

        // 처리 중인 경우 5초마다 자동 갱신
        const interval = setInterval(() => {
            if (progress?.status === 'processing') {
                fetchProgress();
            }
        }, 5000);

        return () => clearInterval(interval);
    }, [batchId, progress?.status]);

    if (loading) {
        return (
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography>로딩 중...</Typography>
            </Paper>
        );
    }

    if (!progress) {
        return null;
    }

    const progressPercentage = progress.progress_percentage || 0;

    return (
        <Paper elevation={2} sx={{ p: 3, mb: 3, backgroundColor: '#f0f7ff' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                📊 진행 상황
            </Typography>

            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                {progressPercentage.toFixed(2)}%
                            </Typography>
                            <StatusField />
                        </Box>
                        <LinearProgress
                            variant="determinate"
                            value={progressPercentage}
                            sx={{
                                height: 20,
                                borderRadius: 2,
                                backgroundColor: '#e3f2fd',
                                '& .MuiLinearProgress-bar': {
                                    borderRadius: 2,
                                    backgroundColor: progressPercentage === 100 ? '#4caf50' : '#2196f3',
                                },
                            }}
                        />
                    </Box>
                </Grid>

                <Grid item xs={12} sm={3}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">총 파일 수</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                {(progress.total_files || 0).toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={3}>
                    <Card variant="outlined" sx={{ backgroundColor: '#e8f5e9' }}>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">완료</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#2e7d32' }}>
                                {(progress.completed || 0).toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={3}>
                    <Card variant="outlined" sx={{ backgroundColor: '#ffebee' }}>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">실패</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#c62828' }}>
                                {(progress.failed || 0).toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={3}>
                    <Card variant="outlined" sx={{ backgroundColor: '#fff3e0' }}>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">대기 중</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#ef6c00' }}>
                                {(progress.pending || 0).toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {progress.avg_processing_time && (
                <Box sx={{ mt: 3, p: 2, backgroundColor: '#ffffff', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">평균 처리 시간</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                        {progress.avg_processing_time.toFixed(2)}초 / 파일
                    </Typography>
                </Box>
            )}
        </Paper>
    );
};

/**
 * STT 배치 상세보기 내용
 */
const STTBatchShowContent = () => {
    const record = useRecordContext();

    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            {/* 진행 상황 카드 */}
            <ProgressCard batchId={record.id} />

            {/* 배치 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📋 배치 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">배치 이름</Typography>
                        <Typography variant="h6" sx={{ mt: 1 }}>
                            {record.name}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">우선순위</Typography>
                        <Box sx={{ mt: 1 }}>
                            <PriorityField />
                        </Box>
                    </Grid>
                    {record.description && (
                        <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">설명</Typography>
                            <Typography variant="body1" sx={{ mt: 1 }}>
                                {record.description}
                            </Typography>
                        </Grid>
                    )}
                </Grid>
            </Paper>

            {/* 파일 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📁 파일 정보
            </Typography>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">소스 경로</Typography>
                        <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', wordBreak: 'break-all' }}>
                            {record.source_path}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">파일 패턴</Typography>
                        <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace' }}>
                            {record.file_pattern}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">총 파일 수</Typography>
                        <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold' }}>
                            {(record.total_files || 0).toLocaleString()}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2, backgroundColor: '#e8f5e9' }}>
                        <Typography variant="caption" color="text.secondary">완료 파일</Typography>
                        <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold', color: '#2e7d32' }}>
                            {(record.completed_files || 0).toLocaleString()}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2, backgroundColor: '#ffebee' }}>
                        <Typography variant="caption" color="text.secondary">실패 파일</Typography>
                        <Typography variant="h5" sx={{ mt: 1, fontWeight: 'bold', color: '#c62828' }}>
                            {(record.failed_files || 0).toLocaleString()}
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>

            {/* 처리 시간 정보 */}
            {(record.started_at || record.completed_at || record.avg_processing_time) && (
                <>
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        ⏱️ 처리 시간
                    </Typography>
                    <Grid container spacing={2}>
                        {record.started_at && (
                            <Grid item xs={12} sm={4}>
                                <Paper elevation={1} sx={{ p: 2 }}>
                                    <Typography variant="caption" color="text.secondary">시작 시간</Typography>
                                    <Box sx={{ mt: 1 }}>
                                        <DateField source="started_at" showTime record={record} />
                                    </Box>
                                </Paper>
                            </Grid>
                        )}
                        {record.completed_at && (
                            <Grid item xs={12} sm={4}>
                                <Paper elevation={1} sx={{ p: 2 }}>
                                    <Typography variant="caption" color="text.secondary">완료 시간</Typography>
                                    <Box sx={{ mt: 1 }}>
                                        <DateField source="completed_at" showTime record={record} />
                                    </Box>
                                </Paper>
                            </Grid>
                        )}
                        {record.avg_processing_time && (
                            <Grid item xs={12} sm={4}>
                                <Paper elevation={1} sx={{ p: 2 }}>
                                    <Typography variant="caption" color="text.secondary">평균 처리 시간</Typography>
                                    <Typography variant="h6" sx={{ mt: 1 }}>
                                        {record.avg_processing_time.toFixed(2)}초
                                    </Typography>
                                </Paper>
                            </Grid>
                        )}
                    </Grid>
                </>
            )}

            {/* 메타데이터 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📊 메타데이터
            </Typography>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">생성자</Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="created_by" />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">생성일시</Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="created_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">수정일시</Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="updated_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
            </Grid>

            {/* 알림 이메일 */}
            {record.notify_emails && record.notify_emails.length > 0 && (
                <Paper elevation={1} sx={{ mt: 3, p: 2 }}>
                    <Typography variant="caption" color="text.secondary">알림 이메일</Typography>
                    <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {record.notify_emails.map((email, index) => (
                            <Chip key={index} label={email} size="small" variant="outlined" />
                        ))}
                    </Box>
                </Paper>
            )}
        </Box>
    );
};

/**
 * STT 배치 상세보기
 */
export const STTBatchShow = () => (
    <Show title="🎙️ STT 배치 상세">
        <SimpleShowLayout>
            <STTBatchShowContent />
        </SimpleShowLayout>
    </Show>
);

/**
 * 파일 경로 입력 + 찾아보기/업로드 버튼 컴포넌트
 */
const PathInputWithBrowser = ({ folderBrowserOpen, setFolderBrowserOpen, folderUploadOpen, setFolderUploadOpen, handleFolderSelect, handleUploadComplete }) => {
    const form = useFormContext();

    return (
        <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <Box sx={{ flex: 1 }}>
                    <TextInput
                        source="source_path"
                        label="📂 파일 경로 (필수)"
                        validate={[required('파일 경로를 입력해주세요')]}
                        fullWidth
                        placeholder="예: /data/audio/회의록/2024-10"
                        helperText="서버의 경로 또는 Windows에서 업로드한 폴더 경로"
                        sx={{
                            '& .MuiInputBase-root': {
                                fontFamily: 'monospace',
                                fontSize: '0.95rem',
                            },
                        }}
                    />
                </Box>
                <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={() => setFolderUploadOpen(true)}
                    sx={{
                        mt: '8px',
                        height: '56px',
                        minWidth: '160px',
                        borderColor: '#f57c00',
                        color: '#f57c00',
                        '&:hover': {
                            borderColor: '#e65100',
                            backgroundColor: '#fff3e0',
                        },
                    }}
                >
                    폴더 업로드
                </Button>
                <Button
                    variant="outlined"
                    startIcon={<FolderIcon />}
                    onClick={() => setFolderBrowserOpen(true)}
                    sx={{
                        mt: '8px',
                        height: '56px',
                        minWidth: '140px',
                        borderColor: '#2196f3',
                        color: '#2196f3',
                        '&:hover': {
                            borderColor: '#1976d2',
                            backgroundColor: '#e3f2fd',
                        },
                    }}
                >
                    서버 탐색
                </Button>
            </Box>

            {/* Windows 폴더 업로드 대화상자 */}
            <FolderUploadDialog
                open={folderUploadOpen}
                onClose={() => setFolderUploadOpen(false)}
                onUploadComplete={(path) => handleUploadComplete(path, form)}
            />

            {/* 서버 폴더 브라우저 대화상자 */}
            <FolderBrowserDialog
                open={folderBrowserOpen}
                onClose={() => setFolderBrowserOpen(false)}
                onSelect={(path) => handleFolderSelect(path, form)}
            />
        </Box>
    );
};

/**
 * STT 배치 생성 폼
 */
export const STTBatchCreate = () => {
    const notify = useNotify();
    const redirect = useRedirect();
    const [folderBrowserOpen, setFolderBrowserOpen] = useState(false);
    const [folderUploadOpen, setFolderUploadOpen] = useState(false);

    const onSuccess = (data) => {
        console.log('[STTBatchCreate] 생성 성공:', data);
        notify('✅ 배치 작업이 생성되었습니다. 자동으로 처리가 시작됩니다.', { type: 'success' });
        redirect('/stt-batches');
    };

    const onError = (error) => {
        console.error('[STTBatchCreate] 생성 실패:', error);
        notify(`❌ 배치 생성 실패: ${error.message || '알 수 없는 오류'}`, { type: 'error' });
    };

    const handleFolderSelect = (path, form) => {
        // 폼의 source_path 필드에 선택한 경로 설정
        form.change('source_path', path);
        setFolderBrowserOpen(false);
    };

    const handleUploadComplete = (path, form) => {
        // 업로드 완료 후 경로 설정
        form.change('source_path', path);
        setFolderUploadOpen(false);
        notify('✅ 파일 업로드가 완료되었습니다.', { type: 'success' });
    };

    return (
        <Create
            title="🎙️ STT 배치 작업 생성"
            mutationOptions={{ onSuccess, onError }}
        >
            <SimpleForm
                sx={{
                    maxWidth: 900,
                    '& .MuiTextField-root': {
                        mb: 2,
                    },
                }}
                defaultValues={{
                    file_pattern: '*.mp3',
                    priority: 'normal'
                }}
                onSubmit={(data) => {
                    console.log('[STTBatchCreate] Form Submit 시작:', data);
                    return data;
                }}
                validate={(values) => {
                    const errors = {};
                    console.log('[STTBatchCreate] Validation 체크:', values);

                    if (!values.name) {
                        errors.name = '배치 이름을 입력해주세요';
                        console.error('[STTBatchCreate] Validation 실패: name 누락');
                    }
                    if (!values.source_path) {
                        errors.source_path = '파일 경로를 입력해주세요';
                        console.error('[STTBatchCreate] Validation 실패: source_path 누락');
                    }

                    if (Object.keys(errors).length > 0) {
                        console.error('[STTBatchCreate] Validation 에러:', errors);
                    }

                    return errors;
                }}
            >
                {/* 기본 정보 섹션 */}
                <Paper
                    elevation={2}
                    sx={{
                        p: 3,
                        mb: 3,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                    }}
                >
                    <Typography variant="h6" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                            sx={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            📋
                        </Box>
                        기본 정보
                    </Typography>
                </Paper>

                <Box sx={{ px: 2 }}>
                    <TextInput
                        source="name"
                        label="배치 이름 (필수)"
                        validate={[required('배치 이름을 입력해주세요')]}
                        fullWidth
                        helperText="예: 2024년 12월 총무처 회의록 / 임원진 미팅 녹음본"
                        sx={{
                            '& .MuiInputBase-root': {
                                fontSize: '1.1rem',
                            },
                        }}
                    />

                    <TextInput
                        source="description"
                        label="설명 (선택사항)"
                        multiline
                        rows={3}
                        fullWidth
                        placeholder="이 배치 작업에 대한 상세 설명을 입력하세요..."
                        helperText="배치 작업의 목적, 처리할 파일 종류 등을 자유롭게 기록"
                    />
                </Box>

                {/* 파일 정보 섹션 */}
                <Paper
                    elevation={2}
                    sx={{
                        p: 3,
                        mb: 3,
                        mt: 4,
                        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                        color: 'white',
                    }}
                >
                    <Typography variant="h6" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                            sx={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            📁
                        </Box>
                        파일 위치 및 패턴
                    </Typography>
                </Paper>

                <Box sx={{ px: 2 }}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2,
                            mb: 2,
                            backgroundColor: '#e3f2fd',
                            borderLeft: '4px solid #2196f3',
                        }}
                    >
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1976d2', mb: 1 }}>
                            💡 경로 입력 방법 (Windows/Linux 모두 지원)
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5, fontWeight: 'bold' }}>
                            📂 Windows 경로:
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5, pl: 2 }}>
                            • <strong>로컬 디스크:</strong> <code>C:\AudioFiles\2024\meetings\</code>
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 1, pl: 2 }}>
                            • <strong>네트워크 공유 (UNC):</strong> <code>\\server\share\audio\</code>
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5, fontWeight: 'bold' }}>
                            🐧 Linux 경로:
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5, pl: 2 }}>
                            • <strong>로컬 디스크:</strong> <code>/data/audio/meetings/2024/</code>
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5, pl: 2 }}>
                            • <strong>S3:</strong> <code>s3://bucket-name/folder/2024/</code>
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 1, pl: 2 }}>
                            • <strong>MinIO:</strong> <code>minio://my-bucket/audio-files/</code>
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic', color: '#1976d2' }}>
                            ✅ 한글 파일명도 지원합니다: <code>C:\회의록\2024\총무처 회의.mp3</code>
                        </Typography>
                    </Paper>

                    {/* 파일 경로 입력 + 업로드/찾아보기 버튼 */}
                    <PathInputWithBrowser
                        folderBrowserOpen={folderBrowserOpen}
                        setFolderBrowserOpen={setFolderBrowserOpen}
                        folderUploadOpen={folderUploadOpen}
                        setFolderUploadOpen={setFolderUploadOpen}
                        handleFolderSelect={handleFolderSelect}
                        handleUploadComplete={handleUploadComplete}
                    />

                    <TextInput
                        source="file_pattern"
                        label="🎯 파일 패턴 (확장자 필터)"
                        fullWidth
                        placeholder="예: *.mp3 (기본값)"
                        helperText="예: *.mp3 (MP3만), *.wav (WAV만), *.* (모든 파일) - 기본값: *.mp3"
                        sx={{
                            '& .MuiInputBase-root': {
                                fontFamily: 'monospace',
                            },
                        }}
                    />

                    <Paper
                        elevation={0}
                        sx={{
                            p: 2,
                            mt: 2,
                            backgroundColor: '#fff3e0',
                            borderLeft: '4px solid #ff9800',
                        }}
                    >
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#e65100', mb: 1 }}>
                            📊 처리 방식
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary">
                            • 지정한 경로에서 파일 패턴에 맞는 <strong>모든 음성 파일을 자동으로 스캔</strong>합니다
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary">
                            • 각 파일은 STT 엔진(Whisper)으로 전사되어 <strong>PostgreSQL DB</strong>에 저장됩니다
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary">
                            • 전사 결과는 <code>stt_transcriptions</code> 테이블의 <code>transcription_text</code> 컬럼에 저장
                        </Typography>
                        <Typography variant="caption" component="div" color="text.secondary">
                            • 요약/회의록은 <code>stt_summaries</code> 테이블에 별도 저장 (LLM 처리)
                        </Typography>
                    </Paper>
                </Box>

                {/* 처리 옵션 섹션 */}
                <Paper
                    elevation={2}
                    sx={{
                        p: 3,
                        mb: 3,
                        mt: 4,
                        background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                        color: 'white',
                    }}
                >
                    <Typography variant="h6" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                            sx={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            ⚙️
                        </Box>
                        처리 옵션
                    </Typography>
                </Paper>

                <Box sx={{ px: 2 }}>
                    <Grid container spacing={3}>
                        <Grid item xs={12} sm={6}>
                            <SelectInput
                                source="priority"
                                label="⏱️ 우선순위"
                                choices={priorityChoices}
                                fullWidth
                                helperText="높은 우선순위 작업이 먼저 처리됩니다 (기본값: 보통)"
                            />
                        </Grid>
                    </Grid>

                    <TextInput
                        source="notify_emails"
                        label="📧 완료 알림 이메일 (선택사항)"
                        fullWidth
                        placeholder="user1@company.com, user2@company.com"
                        helperText="쉼표(,)로 구분하여 여러 이메일 입력 가능. 배치 완료 시 자동 알림"
                        parse={(value) => value ? value.split(',').map(e => e.trim()).filter(e => e) : null}
                        format={(value) => value ? value.join(', ') : ''}
                        sx={{
                            mt: 2,
                        }}
                    />
                </Box>

                {/* 주의사항 */}
                <Paper
                    elevation={3}
                    sx={{
                        p: 3,
                        mt: 4,
                        backgroundColor: '#ffebee',
                        borderLeft: '6px solid #d32f2f',
                    }}
                >
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#c62828', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        ⚠️ 중요 안내사항
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                🔒 보안
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5 }}>
                                • Path Traversal 공격 차단 (../../ 불가)
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5 }}>
                                • 허용 경로: s3://, minio://, /data/audio/
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary">
                                • 개당 파일 크기 1GB 제한
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                💾 저장 위치
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5 }}>
                                • 전사 텍스트: PostgreSQL DB
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary" sx={{ mb: 0.5 }}>
                                • 테이블: stt_transcriptions
                            </Typography>
                            <Typography variant="caption" component="div" color="text.secondary">
                                • 배치 생성 후 자동 처리 시작
                            </Typography>
                        </Grid>
                    </Grid>
                </Paper>
            </SimpleForm>
        </Create>
    );
};
