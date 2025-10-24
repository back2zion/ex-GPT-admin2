/**
 * Satisfaction (만족도 조사) Resource - react-admin
 * 통일감 있는 디자인 + 사용성 우선
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    ShowButton,
    DeleteButton,
    Show,
    SimpleShowLayout,
    Filter,
    SelectInput,
    useRecordContext,
    downloadCSV,
    useInput,
} from 'react-admin';
import { Box, Grid, Typography, Paper, Rating, Chip, Card, CardContent, LinearProgress, Button } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import jsonExport from 'jsonexport/dist';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

/**
 * 카테고리 선택 옵션
 */
const categoryChoices = [
    { id: 'ui', name: 'UI/UX' },
    { id: 'speed', name: '응답 속도' },
    { id: 'accuracy', name: '답변 정확도' },
    { id: 'other', name: '기타' },
];

/**
 * 커스텀 DatePicker Input (달력 UI 제공)
 */
const CustomDateInput = ({ source, label, ...props }) => {
    const { field } = useInput({ source, ...props });

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
            <DatePicker
                label={label}
                value={field.value ? dayjs(field.value) : null}
                onChange={(newValue) => {
                    field.onChange(newValue ? newValue.format('YYYY-MM-DD') : null);
                }}
                slotProps={{
                    textField: {
                        fullWidth: true,
                        variant: 'filled',
                        size: 'small',
                    }
                }}
            />
        </LocalizationProvider>
    );
};

/**
 * UTF-8 BOM을 추가한 CSV exporter (한글 깨짐 방지)
 */
const exporter = (records) => {
    const dataToExport = records.map(record => ({
        'ID': record.id,
        '사용자': record.user_id,
        '평점': record.rating,
        '카테고리': record.category || '-',
        '피드백': record.feedback || '-',
        'IP주소': record.ip_address || '-',
        '제출일시': record.created_at,
    }));

    jsonExport(dataToExport, (err, csv) => {
        const csvWithBOM = '\uFEFF' + csv;
        downloadCSV(csvWithBOM, '만족도조사');
    });
};

/**
 * 필터
 */
const SatisfactionFilter = (props) => (
    <Filter {...props}>
        <SelectInput
            source="rating"
            label="평점"
            choices={[
                { id: 5, name: '⭐⭐⭐⭐⭐ (5점)' },
                { id: 4, name: '⭐⭐⭐⭐ (4점)' },
                { id: 3, name: '⭐⭐⭐ (3점)' },
                { id: 2, name: '⭐⭐ (2점)' },
                { id: 1, name: '⭐ (1점)' },
            ]}
            alwaysOn
        />
        <SelectInput
            source="category"
            label="카테고리"
            choices={categoryChoices}
            alwaysOn
        />
    </Filter>
);

/**
 * 평점 필드 (별점 표시)
 */
const RatingField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Rating value={record.rating} readOnly size="small" />
            <Typography variant="body2" color="text.secondary">
                ({record.rating})
            </Typography>
        </Box>
    );
};

/**
 * 카테고리 필드 (칩 표시)
 */
const CategoryField = (props) => {
    const record = useRecordContext();
    if (!record || !record.category) return <span>-</span>;

    const categoryMap = {
        ui: { label: 'UI/UX', color: 'primary' },
        speed: { label: '응답 속도', color: 'success' },
        accuracy: { label: '답변 정확도', color: 'warning' },
        other: { label: '기타', color: 'default' },
    };

    const cat = categoryMap[record.category] || { label: record.category, color: 'default' };

    return <Chip label={cat.label} color={cat.color} size="small" />;
};

/**
 * 피드백 필드 (긴 텍스트 줄임)
 */
const FeedbackField = (props) => {
    const record = useRecordContext();
    if (!record || !record.feedback) return <span>-</span>;

    const feedback = record.feedback;
    const shortened = feedback.length > 50
        ? feedback.substring(0, 50) + '...'
        : feedback;

    return <span>{shortened}</span>;
};

/**
 * 만족도 조사 목록
 */
export const SatisfactionList = () => (
    <List
        filters={<SatisfactionFilter />}
        exporter={exporter}
        perPage={50}
        sort={{ field: 'created_at', order: 'DESC' }}
        title="⭐ 만족도 조사"
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
                    padding: '16px',
                    lineHeight: '24px',
                    verticalAlign: 'middle'
                },
                '& .RaDatagrid-rowCell': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                }
            }}
        >
            <TextField source="id" label="ID" sx={{ width: '60px' }} />
            <TextField source="user_id" label="사용자" sx={{ width: '150px' }} />
            <RatingField source="rating" label="평점" sx={{ width: '150px' }} />
            <CategoryField source="category" label="카테고리" sx={{ width: '130px' }} />
            <FeedbackField source="feedback" label="피드백" />
            <DateField
                source="created_at"
                label="제출일시"
                showTime
                sx={{ width: '160px' }}
                options={{
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                }}
            />
            <ShowButton label="상세보기" sx={{ width: '100px' }} />
            <DeleteButton label="삭제" sx={{ width: '80px' }} />
        </Datagrid>
    </List>
);

/**
 * STT 시스템 요약 위젯
 */
const STTSummaryWidget = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSTTStats = async () => {
            try {
                const response = await fetch('http://localhost:8010/api/v1/admin/stt-batches/?limit=10');

                // 시큐어 코딩: HTTP 상태 및 Content-Type 검증
                if (!response.ok) {
                    console.error(`STT API Error: ${response.status} ${response.statusText}`);
                    setLoading(false);
                    return;
                }

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    console.error('Invalid content type from STT API:', contentType);
                    setLoading(false);
                    return;
                }

                const data = await response.json();

                // 통계 계산
                const batches = data.items || [];
                const totalBatches = batches.length;
                const processingBatches = batches.filter(b => b.status === 'processing').length;
                const totalFiles = batches.reduce((sum, b) => sum + (b.total_files || 0), 0);
                const completedFiles = batches.reduce((sum, b) => sum + (b.completed_files || 0), 0);
                const progress = totalFiles > 0 ? (completedFiles / totalFiles) * 100 : 0;

                setStats({
                    totalBatches,
                    processingBatches,
                    totalFiles,
                    completedFiles,
                    progress,
                    latestBatches: batches.slice(0, 3)
                });
                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch STT stats:', error);
                setLoading(false);
            }
        };

        fetchSTTStats();
    }, []);

    if (loading) {
        return (
            <Paper elevation={2} sx={{ p: 3, mt: 4, backgroundColor: '#f5f5f5' }}>
                <Typography variant="h6" gutterBottom>
                    🎙️ STT 음성 전사 시스템
                </Typography>
                <Typography>로딩 중...</Typography>
            </Paper>
        );
    }

    if (!stats) {
        return null;
    }

    return (
        <Paper elevation={2} sx={{ p: 3, mt: 4, backgroundColor: '#f0f7ff' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                    🎙️ STT 음성 전사 시스템
                </Typography>
                <Button
                    component={Link}
                    to="/stt-batches"
                    variant="outlined"
                    size="small"
                >
                    전체 보기
                </Button>
            </Box>

            {/* 전체 통계 */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={3}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">전체 배치</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                {stats.totalBatches}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                    <Card variant="outlined" sx={{ backgroundColor: '#e3f2fd' }}>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">처리 중</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                {stats.processingBatches}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">총 파일</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                                {stats.totalFiles.toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={3}>
                    <Card variant="outlined" sx={{ backgroundColor: '#e8f5e9' }}>
                        <CardContent>
                            <Typography variant="caption" color="text.secondary">완료 파일</Typography>
                            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#2e7d32' }}>
                                {stats.completedFiles.toLocaleString()}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* 전체 진행률 */}
            <Box sx={{ mb: 3, p: 2, backgroundColor: '#ffffff', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        전체 진행률
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                        {stats.progress.toFixed(2)}%
                    </Typography>
                </Box>
                <LinearProgress
                    variant="determinate"
                    value={stats.progress}
                    sx={{
                        height: 10,
                        borderRadius: 1,
                        backgroundColor: '#e3f2fd',
                        '& .MuiLinearProgress-bar': {
                            borderRadius: 1,
                            backgroundColor: stats.progress === 100 ? '#4caf50' : '#2196f3',
                        },
                    }}
                />
            </Box>

            {/* 최근 배치 */}
            {stats.latestBatches && stats.latestBatches.length > 0 && (
                <>
                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2, mb: 1 }}>
                        최근 배치 작업
                    </Typography>
                    {stats.latestBatches.map((batch) => {
                        const batchProgress = batch.total_files > 0
                            ? (batch.completed_files / batch.total_files) * 100
                            : 0;

                        const statusMap = {
                            pending: { label: '대기 중', color: 'default' },
                            processing: { label: '처리 중', color: 'primary' },
                            completed: { label: '완료', color: 'success' },
                            failed: { label: '실패', color: 'error' },
                            paused: { label: '일시정지', color: 'warning' },
                        };

                        const status = statusMap[batch.status] || { label: batch.status, color: 'default' };

                        return (
                            <Paper
                                key={batch.id}
                                elevation={1}
                                sx={{
                                    p: 2,
                                    mb: 1,
                                    '&:hover': {
                                        backgroundColor: '#f5f5f5',
                                        cursor: 'pointer',
                                    },
                                }}
                                component={Link}
                                to={`/stt-batches/${batch.id}/show`}
                                style={{ textDecoration: 'none', color: 'inherit' }}
                            >
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                        {batch.name}
                                    </Typography>
                                    <Chip label={status.label} color={status.color} size="small" />
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                    <Typography variant="caption" color="text.secondary">
                                        {batch.completed_files?.toLocaleString() || 0} / {batch.total_files?.toLocaleString() || 0}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {batchProgress.toFixed(1)}%
                                    </Typography>
                                </Box>
                                <LinearProgress
                                    variant="determinate"
                                    value={batchProgress}
                                    sx={{
                                        height: 6,
                                        borderRadius: 1,
                                        backgroundColor: '#e0e0e0',
                                        '& .MuiLinearProgress-bar': {
                                            borderRadius: 1,
                                            backgroundColor: batchProgress === 100 ? '#4caf50' : '#2196f3',
                                        },
                                    }}
                                />
                            </Paper>
                        );
                    })}
                </>
            )}
        </Paper>
    );
};

/**
 * 만족도 조사 상세보기 내용 컴포넌트
 */
const SatisfactionShowContent = () => {
    const record = useRecordContext();

    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            {/* 평가 정보 섹션 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                ⭐ 평가 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">평점</Typography>
                        <Box sx={{ mt: 1 }}>
                            <Rating value={record.rating} readOnly size="large" />
                            <Typography variant="h5" component="span" sx={{ ml: 2 }}>
                                {record.rating} / 5
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">카테고리</Typography>
                        <Box sx={{ mt: 1 }}>
                            <CategoryField />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            {/* 피드백 섹션 */}
            {record.feedback && (
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: '#ed6c02' }}>
                        💬 피드백
                    </Typography>
                    <Typography
                        variant="body1"
                        sx={{
                            whiteSpace: 'pre-wrap',
                            mt: 1,
                            lineHeight: 1.8,
                        }}
                    >
                        {record.feedback}
                    </Typography>
                </Paper>
            )}

            {/* 메타데이터 섹션 */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📊 메타데이터
            </Typography>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">사용자 ID</Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="user_id" />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">IP 주소</Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="ip_address" />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">관련 질문 ID</Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="related_question_id" />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">제출일시</Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="created_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">수정일시</Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="updated_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
            </Grid>

            {/* STT 시스템 요약 위젯 */}
            <STTSummaryWidget />
        </Box>
    );
};

/**
 * 만족도 조사 상세보기
 */
export const SatisfactionShow = () => (
    <Show title="⭐ 만족도 조사 상세">
        <SimpleShowLayout>
            <SatisfactionShowContent />
        </SimpleShowLayout>
    </Show>
);
