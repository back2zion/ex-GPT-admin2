/**
 * A/B Testing 대시보드 리소스
 *
 * Features:
 * - A/B 실험 생성 및 관리
 * - 통계 결과 시각화
 * - 실험 종료 및 승자 선정
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    Show,
    Create,
    SimpleForm,
    ReferenceInput,
    SelectInput,
    NumberInput,
    TextInput,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    useNotify,
    useRefresh,
    useRedirect,
    required,
    minValue,
    maxValue
} from 'react-admin';
import {
    Chip,
    Paper,
    Grid,
    Typography,
    Box,
    Card,
    CardContent,
    Alert,
    LinearProgress
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    Stop as StopIcon,
    CheckCircle as CheckCircleIcon,
    Science as ScienceIcon
} from '@mui/icons-material';

// Status labels
const statusLabels = {
    'running': '실행 중',
    'completed': '완료',
    'stopped': '중지됨'
};

const statusColors = {
    'running': 'info',
    'completed': 'success',
    'stopped': 'default'
};

const statusIcons = {
    'running': <PlayIcon fontSize="small" />,
    'completed': <CheckCircleIcon fontSize="small" />,
    'stopped': <StopIcon fontSize="small" />
};

// Custom Fields
const ExperimentStatusField = () => {
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

    // Calculate progress (samples collected / target)
    const progress = record.target_samples > 0
        ? Math.min((record.collected_samples || 0) / record.target_samples * 100, 100)
        : 0;

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

// List View
const ExperimentListActions = () => (
    <TopToolbar>
        <FilterButton />
        <ExportButton />
    </TopToolbar>
);

export const ABTestingList = () => (
    <List
        actions={<ExperimentListActions />}
        sort={{ field: 'start_date', order: 'DESC' }}
        perPage={25}
        title="🧪 A/B 테스트"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#f57c00',
                    color: 'white',
                    fontWeight: 'bold'
                }
            }}
        >
            <TextField source="id" label="ID" sx={{ width: '60px' }} />
            <TextField source="experiment_name" label="실험 이름" sx={{ width: '200px' }} />
            <TextField source="model_a_id" label="모델 A" sx={{ width: '80px' }} />
            <TextField source="model_b_id" label="모델 B" sx={{ width: '80px' }} />
            <ExperimentStatusField label="상태" sx={{ width: '120px' }} />
            <ProgressField label="진행률" sx={{ width: '180px' }} />
            <TextField source="success_metric" label="평가 지표" sx={{ width: '120px' }} />
            <DateField source="start_date" label="시작일" showTime sx={{ width: '160px' }} />
        </Datagrid>
    </List>
);

// Show View
const ExperimentShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1400 }}>
            {/* 기본 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                🧪 실험 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">실험 이름</Typography>
                        <Typography variant="body1" fontWeight="bold" sx={{ mt: 0.5 }}>
                            {record.experiment_name}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">상태</Typography>
                        <Box sx={{ mt: 0.5 }}>
                            <ExperimentStatusField />
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

            {/* 모델 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                🤖 비교 모델
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" color="primary">모델 A</Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                                Model ID: {record.model_a_id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                트래픽: {((record.traffic_split?.a || 0.5) * 100).toFixed(0)}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" color="secondary">모델 B</Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                                Model ID: {record.model_b_id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                트래픽: {((record.traffic_split?.b || 0.5) * 100).toFixed(0)}%
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* 진행 상황 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📊 진행 상황
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">목표 샘플 수</Typography>
                        <Typography variant="h5" sx={{ mt: 0.5 }}>
                            {record.target_samples?.toLocaleString()}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">수집된 샘플</Typography>
                        <Typography variant="h5" color="primary" sx={{ mt: 0.5 }}>
                            {(record.collected_samples || 0).toLocaleString()}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">진행률</Typography>
                        <Box sx={{ mt: 0.5 }}>
                            <ProgressField />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            {/* 평가 지표 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📈 평가 지표
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Typography variant="body1" fontWeight="bold">
                    Success Metric: {record.success_metric}
                </Typography>
                {record.status === 'completed' && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                        실험이 완료되었습니다. 결과를 확인하세요.
                    </Alert>
                )}
            </Paper>

            {/* 날짜 정보 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📅 실행 기간
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">시작 날짜</Typography>
                        <Typography variant="body1" sx={{ mt: 0.5 }}>
                            {record.start_date ? new Date(record.start_date).toLocaleString('ko-KR') : '-'}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">종료 날짜</Typography>
                        <Typography variant="body1" sx={{ mt: 0.5 }}>
                            {record.end_date ? new Date(record.end_date).toLocaleString('ko-KR') : '진행 중'}
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>
        </Box>
    );
};

export const ABTestingShow = () => (
    <Show title="A/B 실험 상세">
        <ExperimentShowContent />
    </Show>
);

// Create View
export const ABTestingCreate = () => {
    const notify = useNotify();
    const redirect = useRedirect();
    const refresh = useRefresh();

    const onSuccess = (data) => {
        notify('A/B 실험이 생성되었습니다', { type: 'success' });
        redirect('show', 'ab_testing', data.id);
        refresh();
    };

    const onError = (error) => {
        notify(`실험 생성 실패: ${error.message}`, { type: 'error' });
    };

    return (
        <Create
            title="🧪 A/B 실험 생성"
            mutationOptions={{ onSuccess, onError }}
        >
            <SimpleForm>
                <Alert severity="info" sx={{ mb: 2, width: '100%' }}>
                    <Typography variant="body2">
                        두 모델의 성능을 비교하기 위한 A/B 테스트를 생성합니다.
                    </Typography>
                </Alert>

                <TextInput
                    source="experiment_name"
                    label="실험 이름"
                    fullWidth
                    validate={[required()]}
                    helperText="고유한 실험 이름 (예: qwen_vs_llama_legal)"
                />

                <ReferenceInput source="model_a_id" reference="model_registry" label="모델 A">
                    <SelectInput
                        optionText="model_name"
                        validate={[required()]}
                        fullWidth
                    />
                </ReferenceInput>

                <ReferenceInput source="model_b_id" reference="model_registry" label="모델 B">
                    <SelectInput
                        optionText="model_name"
                        validate={[required()]}
                        fullWidth
                    />
                </ReferenceInput>

                <NumberInput
                    source="traffic_split.a"
                    label="모델 A 트래픽 비율"
                    defaultValue={0.5}
                    validate={[required(), minValue(0), maxValue(1)]}
                    step={0.1}
                    helperText="0.0 ~ 1.0 사이의 값 (예: 0.5 = 50%)"
                />

                <NumberInput
                    source="traffic_split.b"
                    label="모델 B 트래픽 비율"
                    defaultValue={0.5}
                    validate={[required(), minValue(0), maxValue(1)]}
                    step={0.1}
                    helperText="0.0 ~ 1.0 사이의 값 (합계는 1.0)"
                />

                <NumberInput
                    source="target_samples"
                    label="목표 샘플 수"
                    defaultValue={200}
                    validate={[required(), minValue(30)]}
                    helperText="최소 30개 이상 (통계적 유의성 확보)"
                />

                <SelectInput
                    source="success_metric"
                    label="평가 지표"
                    choices={[
                        { id: 'user_rating', name: '사용자 평점' },
                        { id: 'response_time', name: '응답 시간' },
                        { id: 'accuracy', name: '정확도' }
                    ]}
                    defaultValue="user_rating"
                    validate={[required()]}
                    fullWidth
                />

                <TextInput
                    source="description"
                    label="설명"
                    multiline
                    rows={3}
                    fullWidth
                    helperText="실험 목적 및 내용 설명"
                />
            </SimpleForm>
        </Create>
    );
};
