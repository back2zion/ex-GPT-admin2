/**
 * Fine-tuning 작업 관리 리소스
 *
 * Features:
 * - Fine-tuning 작업 생성 (하이퍼파라미터 설정)
 * - 작업 목록 및 상태 모니터링
 * - 실시간 로그 뷰어
 * - 메트릭 차트 (MLflow 연동)
 * - 작업 제어 (시작/중지/재시작)
 *
 * Security:
 * - XSS 방지: react-admin 자동 sanitization
 * - GPU 리소스 격리: 백엔드에서 처리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    Show,
    Create,
    SimpleForm,
    TextInput,
    SelectInput,
    ReferenceInput,
    NumberInput,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    useNotify,
    useRefresh,
    useRedirect,
    required,
    minValue,
    maxValue,
    Button,
    useDataProvider,
    useGetOne
} from 'react-admin';
import {
    Chip,
    Paper,
    Grid,
    Typography,
    Box,
    LinearProgress,
    Card,
    CardContent,
    Alert,
    Divider,
    IconButton,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    Stop as StopIcon,
    Refresh as RefreshIcon,
    TrendingUp as TrendingUpIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    HourglassEmpty as HourglassIcon,
    Terminal as TerminalIcon
} from '@mui/icons-material';
import { useState, useEffect } from 'react';

// ============================================
// Constants
// ============================================

const methodOptions = [
    { id: 'lora', name: 'LoRA (Low-Rank Adaptation)' },
    { id: 'qlora', name: 'QLoRA (Quantized LoRA)' },
    { id: 'full', name: 'Full Fine-tuning' }
];

const baseModelOptions = [
    { id: 'Qwen/Qwen2.5-7B-Instruct', name: 'Qwen2.5-7B-Instruct' },
    { id: 'Qwen/Qwen2.5-14B-Instruct', name: 'Qwen2.5-14B-Instruct' },
    { id: 'meta-llama/Llama-3.1-8B-Instruct', name: 'Llama-3.1-8B-Instruct' }
];

const statusLabels = {
    'pending': '대기 중',
    'running': '실행 중',
    'completed': '완료',
    'failed': '실패',
    'stopped': '중지됨'
};

const statusColors = {
    'pending': 'warning',
    'running': 'info',
    'completed': 'success',
    'failed': 'error',
    'stopped': 'default'
};

const statusIcons = {
    'pending': <HourglassIcon />,
    'running': <PlayIcon />,
    'completed': <CheckCircleIcon />,
    'failed': <ErrorIcon />,
    'stopped': <StopIcon />
};

// ============================================
// Custom Fields
// ============================================

const JobStatusField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const label = statusLabels[record.status] || record.status;
    const color = statusColors[record.status] || 'default';
    const icon = statusIcons[record.status];

    return (
        <Chip
            label={label}
            size="small"
            color={color}
            icon={icon}
        />
    );
};

const ProgressField = () => {
    const record = useRecordContext();
    if (!record) return null;

    // Calculate progress based on status and time
    let progress = 0;
    if (record.status === 'pending') progress = 0;
    else if (record.status === 'running') {
        // Estimate progress based on elapsed time (simple heuristic)
        if (record.start_time) {
            const elapsed = Date.now() - new Date(record.start_time).getTime();
            const estimated = 3600000; // 1 hour estimated
            progress = Math.min((elapsed / estimated) * 100, 95);
        } else {
            progress = 10;
        }
    }
    else if (record.status === 'completed') progress = 100;
    else progress = 0;

    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 150 }}>
            <LinearProgress
                variant="determinate"
                value={progress}
                sx={{ flexGrow: 1, height: 8, borderRadius: 1 }}
            />
            <Typography variant="caption" fontWeight="bold">
                {progress.toFixed(0)}%
            </Typography>
        </Box>
    );
};

const DurationField = () => {
    const record = useRecordContext();
    if (!record || !record.start_time) return <Typography variant="body2">-</Typography>;

    const start = new Date(record.start_time);
    const end = record.end_time ? new Date(record.end_time) : new Date();
    const duration = end - start;

    const hours = Math.floor(duration / 3600000);
    const minutes = Math.floor((duration % 3600000) / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);

    return (
        <Typography variant="body2">
            {hours > 0 && `${hours}h `}
            {minutes}m {seconds}s
        </Typography>
    );
};

// ============================================
// List View
// ============================================

const JobListActions = () => (
    <TopToolbar>
        <FilterButton />
        <ExportButton />
    </TopToolbar>
);

export const FinetuningJobList = () => (
    <List
        actions={<JobListActions />}
        sort={{ field: 'created_at', order: 'DESC' }}
        perPage={25}
        title="🔧 Fine-tuning 작업"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#2e7d32',
                    color: 'white',
                    fontWeight: 'bold'
                },
                '& .RaDatagrid-row:hover': {
                    backgroundColor: '#f5f5f5'
                }
            }}
        >
            <TextField source="id" label="ID" sx={{ width: '60px' }} />
            <TextField source="job_name" label="작업 이름" sx={{ width: '200px' }} />
            <TextField source="base_model" label="베이스 모델" sx={{ width: '250px' }} />
            <TextField source="method" label="방법" sx={{ width: '80px' }} />
            <JobStatusField label="상태" sx={{ width: '120px' }} />
            <ProgressField label="진행률" sx={{ width: '180px' }} />
            <DurationField label="소요 시간" sx={{ width: '120px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '160px' }} />
        </Datagrid>
    </List>
);

// ============================================
// Show View with Real-time Monitoring
// ============================================

const LogViewer = ({ jobId }) => {
    const [logs, setLogs] = useState('로그 로딩 중...');
    const [open, setOpen] = useState(false);
    const dataProvider = useDataProvider();

    const loadLogs = async () => {
        try {
            const { data } = await dataProvider.getOne('finetuning_jobs', {
                id: jobId,
                meta: { endpoint: 'logs' }
            });
            setLogs(data.logs || '로그가 없습니다');
        } catch (error) {
            setLogs(`로그 로딩 실패: ${error.message}`);
        }
    };

    useEffect(() => {
        if (open) {
            loadLogs();
            const interval = setInterval(loadLogs, 5000); // Auto-refresh every 5s
            return () => clearInterval(interval);
        }
    }, [open, jobId]);

    return (
        <>
            <Button
                label="로그 보기"
                onClick={() => setOpen(true)}
                startIcon={<TerminalIcon />}
            />
            <Dialog open={open} onClose={() => setOpen(false)} maxWidth="lg" fullWidth>
                <DialogTitle>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h6">학습 로그</Typography>
                        <IconButton onClick={loadLogs} size="small">
                            <RefreshIcon />
                        </IconButton>
                    </Box>
                </DialogTitle>
                <DialogContent>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2,
                            backgroundColor: '#1e1e1e',
                            color: '#d4d4d4',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            maxHeight: '500px',
                            overflow: 'auto',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all'
                        }}
                    >
                        {logs}
                    </Paper>
                </DialogContent>
                <DialogActions>
                    <Button label="닫기" onClick={() => setOpen(false)} />
                </DialogActions>
            </Dialog>
        </>
    );
};

const JobShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1400 }}>
            {/* 기본 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                🔧 작업 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">작업 이름</Typography>
                        <Typography variant="body1" fontWeight="bold" sx={{ mt: 0.5 }}>
                            {record.job_name}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">상태</Typography>
                        <Box sx={{ mt: 0.5 }}>
                            <JobStatusField />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">Fine-tuning 방법</Typography>
                        <Chip label={record.method?.toUpperCase()} color="primary" size="small" sx={{ mt: 0.5 }} />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">GPU</Typography>
                        <Typography variant="body1" fontWeight="bold" sx={{ mt: 0.5 }}>
                            {record.gpu_ids || 'N/A'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">베이스 모델</Typography>
                        <Typography variant="body1" fontFamily="monospace" sx={{ mt: 0.5 }}>
                            {record.base_model}
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>

            {/* 진행 상황 */}
            {record.status === 'running' && (
                <Alert severity="info" icon={<TrendingUpIcon />} sx={{ mb: 3 }}>
                    <Typography variant="body2" fontWeight="bold">학습이 진행 중입니다</Typography>
                    <Box sx={{ mt: 1 }}>
                        <ProgressField />
                    </Box>
                </Alert>
            )}

            {record.status === 'completed' && (
                <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 3 }}>
                    학습이 성공적으로 완료되었습니다
                </Alert>
            )}

            {record.status === 'failed' && record.error_message && (
                <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 3 }}>
                    <Typography variant="body2" fontWeight="bold">학습 실패</Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>{record.error_message}</Typography>
                </Alert>
            )}

            {/* 시간 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                ⏱️ 실행 시간
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">시작 시간</Typography>
                        <Typography variant="body1" sx={{ mt: 0.5 }}>
                            {record.start_time ? new Date(record.start_time).toLocaleString('ko-KR') : '-'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">종료 시간</Typography>
                        <Typography variant="body1" sx={{ mt: 0.5 }}>
                            {record.end_time ? new Date(record.end_time).toLocaleString('ko-KR') : '-'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">소요 시간</Typography>
                        <Box sx={{ mt: 0.5 }}>
                            <DurationField />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            {/* 하이퍼파라미터 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                ⚙️ 하이퍼파라미터
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <pre style={{ overflow: 'auto', fontSize: '12px', margin: 0 }}>
                    {JSON.stringify(record.hyperparameters, null, 2)}
                </pre>
            </Paper>

            {/* MLflow 정보 */}
            {record.mlflow_run_id && (
                <>
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        📊 MLflow 연동
                    </Typography>
                    <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                        <Typography variant="caption" color="text.secondary">MLflow Run ID</Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5 }}>
                            {record.mlflow_run_id}
                        </Typography>
                        <Button
                            label="MLflow UI에서 보기"
                            onClick={() => window.open(`http://localhost:5000/#/experiments`, '_blank')}
                            sx={{ mt: 2 }}
                        />
                    </Paper>
                </>
            )}

            {/* 출력 디렉토리 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📁 파일 경로
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">출력 디렉토리</Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5 }}>
                            {record.output_dir}
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">체크포인트 디렉토리</Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5 }}>
                            {record.checkpoint_dir}
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">로그 파일</Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5 }}>
                            {record.logs_path}
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>

            {/* 로그 뷰어 */}
            <Box sx={{ mt: 3 }}>
                <LogViewer jobId={record.id} />
            </Box>
        </Box>
    );
};

export const FinetuningJobShow = () => (
    <Show title="Fine-tuning 작업 상세">
        <JobShowContent />
    </Show>
);

// ============================================
// Create View
// ============================================

export const FinetuningJobCreate = () => {
    const notify = useNotify();
    const redirect = useRedirect();
    const refresh = useRefresh();

    const onSuccess = (data) => {
        notify('Fine-tuning 작업이 생성되었습니다', { type: 'success' });
        redirect('show', 'finetuning_jobs', data.id);
        refresh();
    };

    const onError = (error) => {
        notify(`작업 생성 실패: ${error.message}`, { type: 'error' });
    };

    return (
        <Create
            title="🚀 Fine-tuning 작업 생성"
            mutationOptions={{ onSuccess, onError }}
        >
            <SimpleForm>
                <Alert severity="info" sx={{ mb: 2, width: '100%' }}>
                    <Typography variant="body2">
                        <strong>주의:</strong> Fine-tuning 작업은 GPU 리소스를 많이 사용합니다.<br />
                        작업 생성 전 GPU 가용성을 확인하세요.
                    </Typography>
                </Alert>

                <TextInput
                    source="job_name"
                    label="작업 이름"
                    fullWidth
                    validate={[required()]}
                    helperText="고유한 작업 이름 (예: legal_qa_lora_v1)"
                />

                <SelectInput
                    source="base_model"
                    label="베이스 모델"
                    choices={baseModelOptions}
                    defaultValue="Qwen/Qwen2.5-7B-Instruct"
                    validate={[required()]}
                    fullWidth
                />

                <ReferenceInput source="dataset_id" reference="training_datasets" label="데이터셋">
                    <SelectInput
                        optionText="name"
                        validate={[required()]}
                        fullWidth
                    />
                </ReferenceInput>

                <SelectInput
                    source="method"
                    label="Fine-tuning 방법"
                    choices={methodOptions}
                    defaultValue="lora"
                    validate={[required()]}
                    fullWidth
                />

                <Divider sx={{ my: 2, width: '100%' }} />
                <Typography variant="h6" gutterBottom>하이퍼파라미터</Typography>

                <NumberInput
                    source="hyperparameters.learning_rate"
                    label="Learning Rate"
                    defaultValue={0.00005}
                    validate={[required(), minValue(0.000001), maxValue(0.001)]}
                    step={0.000001}
                />

                <NumberInput
                    source="hyperparameters.batch_size"
                    label="Batch Size"
                    defaultValue={4}
                    validate={[required(), minValue(1), maxValue(128)]}
                />

                <NumberInput
                    source="hyperparameters.num_epochs"
                    label="Epochs"
                    defaultValue={3}
                    validate={[required(), minValue(1), maxValue(20)]}
                />

                <NumberInput
                    source="hyperparameters.lora_r"
                    label="LoRA Rank (r)"
                    defaultValue={16}
                    validate={[minValue(1), maxValue(256)]}
                    helperText="LoRA/QLoRA 전용 (기본: 16)"
                />

                <NumberInput
                    source="hyperparameters.lora_alpha"
                    label="LoRA Alpha"
                    defaultValue={32}
                    validate={[minValue(1), maxValue(512)]}
                    helperText="LoRA/QLoRA 전용 (기본: 32)"
                />

                <TextInput
                    source="gpu_ids"
                    label="GPU IDs"
                    defaultValue="0"
                    fullWidth
                    helperText="사용할 GPU ID (예: 0 또는 0,1,2,3)"
                />
            </SimpleForm>
        </Create>
    );
};
