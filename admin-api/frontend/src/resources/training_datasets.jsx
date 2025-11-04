/**
 * Fine-tuning 데이터셋 관리 리소스
 *
 * Features:
 * - 데이터셋 업로드 (JSONL, JSON, CSV, Parquet)
 * - 품질 검증 결과 표시
 * - 데이터셋 통계 대시보드
 * - 전처리 상태 모니터링
 *
 * Security:
 * - XSS 방지: react-admin 자동 sanitization
 * - 파일 업로드 검증: 백엔드에서 처리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    Show,
    SimpleShowLayout,
    Create,
    SimpleForm,
    TextInput,
    SelectInput,
    FileInput,
    FileField,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    useNotify,
    useRefresh,
    useRedirect,
    required,
    minLength,
    maxLength
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
    Alert
} from '@mui/material';
import {
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon,
    HourglassEmpty as HourglassIcon,
    Description as DescriptionIcon
} from '@mui/icons-material';

// ============================================
// Constants
// ============================================

const formatOptions = [
    { id: 'jsonl', name: 'JSONL' },
    { id: 'json', name: 'JSON' },
    { id: 'csv', name: 'CSV' },
    { id: 'parquet', name: 'Parquet' }
];

const statusLabels = {
    'active': '활성',
    'deprecated': '폐기됨',
    'archived': '보관됨',
    'processing': '처리 중'
};

const statusColors = {
    'active': 'success',
    'deprecated': 'warning',
    'archived': 'default',
    'processing': 'info'
};

// ============================================
// Custom Fields
// ============================================

const DatasetStatusField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const label = statusLabels[record.status] || record.status;
    const color = statusColors[record.status] || 'default';

    return <Chip label={label} size="small" color={color} />;
};

const QualityScoreField = () => {
    const record = useRecordContext();
    if (!record || record.quality_score === null) return <Typography variant="body2" color="text.secondary">-</Typography>;

    const score = record.quality_score * 100;
    const color = score >= 90 ? 'success' : score >= 70 ? 'warning' : 'error';

    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LinearProgress
                variant="determinate"
                value={score}
                color={color}
                sx={{ width: 100, height: 8, borderRadius: 1 }}
            />
            <Typography variant="body2" fontWeight="bold">
                {score.toFixed(1)}%
            </Typography>
        </Box>
    );
};

const SampleCountField = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box>
            <Typography variant="body2" fontWeight="bold">
                {record.total_samples?.toLocaleString() || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
                Train: {record.train_samples || 0} / Val: {record.val_samples || 0} / Test: {record.test_samples || 0}
            </Typography>
        </Box>
    );
};

// ============================================
// List View
// ============================================

const DatasetListActions = () => (
    <TopToolbar>
        <FilterButton />
        <ExportButton />
    </TopToolbar>
);

export const TrainingDatasetList = () => (
    <List
        actions={<DatasetListActions />}
        sort={{ field: 'created_at', order: 'DESC' }}
        perPage={25}
        title="📊 학습 데이터셋"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#1976d2',
                    color: 'white',
                    fontWeight: 'bold'
                },
                '& .RaDatagrid-row:hover': {
                    backgroundColor: '#f5f5f5'
                }
            }}
        >
            <TextField source="id" label="ID" sx={{ width: '60px' }} />
            <TextField source="name" label="데이터셋 이름" sx={{ width: '200px' }} />
            <TextField source="version" label="버전" sx={{ width: '80px' }} />
            <TextField source="format" label="형식" sx={{ width: '80px' }} />
            <SampleCountField label="샘플 수" sx={{ width: '200px' }} />
            <QualityScoreField label="품질 점수" sx={{ width: '150px' }} />
            <DatasetStatusField label="상태" sx={{ width: '100px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '160px' }} />
        </Datagrid>
    </List>
);

// ============================================
// Show View
// ============================================

const DatasetShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1400 }}>
            {/* 기본 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                📄 데이터셋 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">데이터셋 이름</Typography>
                        <Typography variant="body1" fontWeight="bold" sx={{ mt: 0.5 }}>
                            {record.name}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">버전</Typography>
                        <Typography variant="body1" fontWeight="bold" sx={{ mt: 0.5 }}>
                            {record.version}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">파일 형식</Typography>
                        <Chip label={record.format?.toUpperCase()} size="small" color="primary" sx={{ mt: 0.5 }} />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">상태</Typography>
                        <Box sx={{ mt: 0.5 }}>
                            <DatasetStatusField />
                        </Box>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">설명</Typography>
                        <Typography variant="body1" sx={{ mt: 0.5 }}>
                            {record.description || '설명 없음'}
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>

            {/* 통계 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📊 데이터셋 통계
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">총 샘플 수</Typography>
                            <Typography variant="h4" color="primary" sx={{ mt: 1 }}>
                                {record.total_samples?.toLocaleString() || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">학습 샘플</Typography>
                            <Typography variant="h4" color="success.main" sx={{ mt: 1 }}>
                                {record.train_samples?.toLocaleString() || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">검증 샘플</Typography>
                            <Typography variant="h4" color="warning.main" sx={{ mt: 1 }}>
                                {record.val_samples?.toLocaleString() || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">테스트 샘플</Typography>
                            <Typography variant="h4" color="info.main" sx={{ mt: 1 }}>
                                {record.test_samples?.toLocaleString() || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* 평균 길이 */}
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">평균 Instruction 길이</Typography>
                        <Typography variant="h6" sx={{ mt: 0.5 }}>
                            {record.avg_instruction_length?.toFixed(1) || 0} 토큰
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">평균 Output 길이</Typography>
                        <Typography variant="h6" sx={{ mt: 0.5 }}>
                            {record.avg_output_length?.toFixed(1) || 0} 토큰
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>

            {/* 품질 점수 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                ✅ 품질 검증
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={6}>
                        <Typography variant="body1" fontWeight="bold">품질 점수</Typography>
                        <Box sx={{ mt: 1 }}>
                            <QualityScoreField />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        {record.quality_score >= 0.9 && (
                            <Alert severity="success" icon={<CheckCircleIcon />}>
                                품질이 우수한 데이터셋입니다
                            </Alert>
                        )}
                        {record.quality_score >= 0.7 && record.quality_score < 0.9 && (
                            <Alert severity="warning" icon={<HourglassIcon />}>
                                품질이 양호한 데이터셋입니다
                            </Alert>
                        )}
                        {record.quality_score < 0.7 && (
                            <Alert severity="error" icon={<ErrorIcon />}>
                                품질 개선이 필요한 데이터셋입니다
                            </Alert>
                        )}
                    </Grid>
                </Grid>
            </Paper>

            {/* 파일 경로 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📁 파일 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">원본 파일 경로</Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5, wordBreak: 'break-all' }}>
                            {record.file_path}
                        </Typography>
                    </Grid>
                    {record.preprocessed_path && (
                        <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">전처리된 파일 경로</Typography>
                            <Typography variant="body2" fontFamily="monospace" sx={{ mt: 0.5, wordBreak: 'break-all' }}>
                                {record.preprocessed_path}
                            </Typography>
                        </Grid>
                    )}
                </Grid>
            </Paper>

            {/* 메타데이터 */}
            {record.dataset_metadata && Object.keys(record.dataset_metadata).length > 0 && (
                <>
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        🔍 메타데이터
                    </Typography>
                    <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                        <pre style={{ overflow: 'auto', fontSize: '12px' }}>
                            {JSON.stringify(record.dataset_metadata, null, 2)}
                        </pre>
                    </Paper>
                </>
            )}
        </Box>
    );
};

export const TrainingDatasetShow = () => (
    <Show title="데이터셋 상세">
        <DatasetShowContent />
    </Show>
);

// ============================================
// Create View
// ============================================

export const TrainingDatasetCreate = () => {
    const notify = useNotify();
    const redirect = useRedirect();
    const refresh = useRefresh();

    const onSuccess = (data) => {
        notify('데이터셋이 성공적으로 업로드되었습니다', { type: 'success' });
        redirect('show', 'training_datasets', data.id);
        refresh();
    };

    const onError = (error) => {
        notify(`업로드 실패: ${error.message}`, { type: 'error' });
    };

    return (
        <Create
            title="📤 데이터셋 업로드"
            mutationOptions={{ onSuccess, onError }}
        >
            <SimpleForm>
                <Alert severity="info" sx={{ mb: 2, width: '100%' }}>
                    <Typography variant="body2">
                        <strong>지원 형식:</strong> JSONL, JSON, CSV, Parquet<br />
                        <strong>예시 형식:</strong> {`{"instruction": "질문", "output": "답변"}`}
                    </Typography>
                </Alert>

                <TextInput
                    source="name"
                    label="데이터셋 이름"
                    fullWidth
                    validate={[required(), minLength(2), maxLength(255)]}
                    helperText="데이터셋을 식별할 수 있는 이름 (예: legal_qa_v1)"
                />

                <TextInput
                    source="version"
                    label="버전"
                    defaultValue="v1.0"
                    fullWidth
                    validate={[required()]}
                    helperText="데이터셋 버전 (예: v1.0, v2.1)"
                />

                <SelectInput
                    source="format"
                    label="파일 형식"
                    choices={formatOptions}
                    defaultValue="jsonl"
                    validate={[required()]}
                    fullWidth
                />

                <FileInput
                    source="file"
                    label="데이터셋 파일"
                    accept=".jsonl,.json,.csv,.parquet"
                    validate={[required()]}
                    helperText="업로드할 데이터셋 파일을 선택하세요"
                    sx={{ width: '100%' }}
                >
                    <FileField source="src" title="title" />
                </FileInput>

                <TextInput
                    source="description"
                    label="설명"
                    multiline
                    rows={3}
                    fullWidth
                    helperText="데이터셋에 대한 설명 (선택 사항)"
                />
            </SimpleForm>
        </Create>
    );
};
