/**
 * Conversations Resource - react-admin 방식
 * 기존 ConversationsPage.jsx를 대체
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
    RichTextField,
    Filter,
    useRecordContext,
    downloadCSV,
    useInput,
} from 'react-admin';
import { Box, Grid, Typography, Paper } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import jsonExport from 'jsonexport/dist';

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
        '세션ID': record.session_id,
        '모델명': record.model_name,
        '일시': record.created_at,
        'IP주소': record.ip_address,
        '질문': record.question,
        '답변': record.answer,
        '추론과정': record.thinking_content,
        '참조문서': record.referenced_documents,
        '응답시간(ms)': record.response_time || '-',
    }));

    jsonExport(dataToExport, (err, csv) => {
        // UTF-8 BOM 추가 (\uFEFF)
        const csvWithBOM = '\uFEFF' + csv;
        downloadCSV(csvWithBOM, '대화내역');
    });
};

/**
 * 날짜 범위 필터 (달력 UI)
 */
const ConversationFilter = (props) => (
    <Filter {...props}>
        <CustomDateInput
            source="start"
            label="📅 시작 날짜"
            alwaysOn
        />
        <CustomDateInput
            source="end"
            label="📅 종료 날짜"
            alwaysOn
        />
    </Filter>
);

/**
 * 질문 필드 (긴 텍스트 줄임)
 */
const QuestionField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    const question = record.question || '';
    const shortened = question.length > 100
        ? question.substring(0, 100) + '...'
        : question;

    return <span>{shortened}</span>;
};

/**
 * 응답 시간 필드 (ms 단위)
 */
const ResponseTimeField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    return record.response_time
        ? <span>{record.response_time}ms</span>
        : <span>-</span>;
};

/**
 * 대화내역 목록
 */
export const ConversationList = () => (
    <List
        filters={<ConversationFilter />}
        filterDefaultValues={{
            start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            end: new Date().toISOString().split('T')[0],
        }}
        exporter={exporter}
        perPage={50}
        sort={{ field: 'created_at', order: 'DESC' }}
        title="💬 대화내역 조회"
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
            <TextField source="id" label="ID" sx={{ width: '80px' }} />
            <TextField source="user_id" label="사용자" sx={{ width: '150px' }} />
            <DateField
                source="created_at"
                label="일시"
                showTime
                sx={{ width: '180px' }}
                options={{
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                }}
            />
            <QuestionField source="question" label="질문" />
            <ResponseTimeField source="response_time" label="응답시간" sx={{ width: '120px' }} />
            <ShowButton label="상세보기" sx={{ width: '100px' }} />
        </Datagrid>
    </List>
);

/**
 * 대화내역 상세 (개선된 레이아웃)
 */
export const ConversationShow = () => {
    const record = useRecordContext();

    return (
        <Show title="💬 대화내역 상세">
            <SimpleShowLayout>
                <Box sx={{ width: '100%', maxWidth: 1400 }}>
                    {/* 메타데이터 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                        📊 메타데이터
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">ID</Typography>
                                <TextField source="id" />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">사용자</Typography>
                                <TextField source="user_id" />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">모델명</Typography>
                                <TextField source="model_name" />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">응답시간</Typography>
                                <ResponseTimeField source="response_time" />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">일시</Typography>
                                <DateField
                                    source="created_at"
                                    showTime
                                    options={{
                                        year: 'numeric',
                                        month: '2-digit',
                                        day: '2-digit',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                    }}
                                />
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">IP 주소</Typography>
                                <TextField source="ip_address" />
                            </Paper>
                        </Grid>
                    </Grid>

                    {/* 대화 내용 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        💭 대화 내용
                    </Typography>

                    {/* 질문 */}
                    <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f8f8' }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                            ❓ 질문
                        </Typography>
                        <RichTextField
                            source="question"
                            sx={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'inherit',
                                fontSize: '1rem',
                            }}
                        />
                    </Paper>

                    {/* 추론 과정 */}
                    <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: '#ed6c02' }}>
                            🧠 추론 과정 (Thinking)
                        </Typography>
                        <RichTextField
                            source="thinking_content"
                            sx={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace',
                                fontSize: '0.9rem',
                            }}
                        />
                    </Paper>

                    {/* 답변 */}
                    <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: '#2e7d32' }}>
                            💡 답변
                        </Typography>
                        <RichTextField
                            source="answer"
                            sx={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'inherit',
                                fontSize: '1rem',
                            }}
                        />
                    </Paper>

                    {/* 참조 문서 */}
                    {record?.referenced_documents && (
                        <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f3e5f5' }}>
                            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: '#7b1fa2' }}>
                                📚 참조 문서
                            </Typography>
                            <TextField source="referenced_documents" />
                        </Paper>
                    )}
                </Box>
            </SimpleShowLayout>
        </Show>
    );
};
