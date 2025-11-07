/**
 * Notices Resource - react-admin CRUD
 * 공지사항 관리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    BooleanField,
    NumberField,
    EditButton,
    ShowButton,
    DeleteButton,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    BooleanInput,
    SelectInput,
    Filter,
    required,
    useRecordContext,
    useInput,
} from 'react-admin';
import { Box, Grid, Typography, Paper } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';

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
                    }
                }}
            />
        </LocalizationProvider>
    );
};

/**
 * 우선순위 필드 (한글 표시)
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
 * 제목 필드 (중요 공지사항 강조)
 */
const TitleField = (props) => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <span style={{
            fontWeight: record.is_important ? 'bold' : 'normal',
            color: record.is_important ? '#d32f2f' : 'inherit',
        }}>
            {record.is_important && '⭐ '}
            {record.title}
        </span>
    );
};

/**
 * 공지사항 필터
 */
const NoticeFilter = (props) => (
    <Filter {...props}>
        <SelectInput
            source="priority"
            label="우선순위"
            choices={priorityChoices}
            alwaysOn
        />
        <SelectInput
            source="is_active"
            label="활성화"
            choices={[
                { id: 'true', name: '활성화' },
                { id: 'false', name: '비활성화' },
            ]}
            alwaysOn
        />
        <SelectInput
            source="is_important"
            label="중요 공지"
            choices={[
                { id: 'true', name: '중요' },
                { id: 'false', name: '일반' },
            ]}
            alwaysOn
        />
    </Filter>
);

/**
 * 공지사항 목록
 */
export const NoticeList = () => (
    <List
        filters={<NoticeFilter />}
        sort={{ field: 'created_at', order: 'DESC' }}
        perPage={25}
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
            <TextField source="id" label="ID" sx={{ width: '40px' }} />
            <TitleField source="title" label="제목" />
            <PriorityField source="priority" label="우선순위" sx={{ width: '70px' }} />
            <BooleanField source="is_active" label="활성화" sx={{ width: '50px' }} />
            <BooleanField source="is_important" label="중요" sx={{ width: '45px' }} />
            <BooleanField source="is_popup" label="팝업" sx={{ width: '45px' }} />
            <DateField source="start_date" label="시작일" sx={{ width: '110px' }} />
            <DateField source="end_date" label="종료일" sx={{ width: '110px' }} />
            <NumberField source="view_count" label="조회수" sx={{ width: '55px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '165px' }} options={{
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
            }} />
            <ShowButton label="" sx={{ width: '65px' }} />
            <EditButton label="" sx={{ width: '65px' }} />
            <DeleteButton label="" sx={{ width: '65px' }} />
        </Datagrid>
    </List>
);

/**
 * 공지사항 상세보기 (개선된 레이아웃)
 */
export const NoticeShow = () => {
    const record = useRecordContext();

    return (
        <Show>
            <SimpleShowLayout>
                <Box sx={{ width: '100%', maxWidth: 1200 }}>
                    {/* 공지 내용 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                        📢 공지사항 내용
                    </Typography>
                    <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                            {record?.is_important && '⭐ '}
                            <TextField source="title" />
                        </Typography>
                        <Typography
                            variant="body1"
                            sx={{
                                whiteSpace: 'pre-wrap',
                                mt: 2,
                                lineHeight: 1.8,
                            }}
                        >
                            <TextField source="content" />
                        </Typography>
                    </Paper>

                    {/* 공지 설정 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        ⚙️ 공지 설정
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">우선순위</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <PriorityField source="priority" />
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">활성화</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <BooleanField source="is_active" />
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">중요 공지</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <BooleanField source="is_important" />
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">팝업 표시</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <BooleanField source="is_popup" />
                                </Box>
                            </Paper>
                        </Grid>
                    </Grid>

                    {/* 게시 기간 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        📅 게시 기간
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                        <Grid item xs={12} sm={6}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">게시 시작일</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <DateField source="start_date" />
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">게시 종료일</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <DateField source="end_date" />
                                </Box>
                            </Paper>
                        </Grid>
                    </Grid>

                    {/* 통계 정보 섹션 */}
                    <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                        📊 통계 정보
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={4}>
                            <Paper elevation={1} sx={{ p: 2 }}>
                                <Typography variant="caption" color="text.secondary">조회수</Typography>
                                <Box sx={{ mt: 1 }}>
                                    <NumberField source="view_count" />
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
                </Box>
            </SimpleShowLayout>
        </Show>
    );
};

/**
 * 공지사항 편집
 */
export const NoticeEdit = () => (
    <Edit>
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                {/* 기본 정보 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📝 기본 정보
                </Typography>
                <TextInput
                    source="title"
                    label="제목"
                    validate={[required()]}
                    fullWidth
                />
                <TextInput
                    source="content"
                    label="내용"
                    validate={[required()]}
                    multiline
                    rows={5}
                    fullWidth
                />

                {/* 설정 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    ⚙️ 공지 설정
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <SelectInput
                            source="priority"
                            label="우선순위"
                            choices={priorityChoices}
                            defaultValue="normal"
                            fullWidth
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Box sx={{ pt: 2 }}>
                            <BooleanInput source="is_active" label="활성화" defaultValue={true} />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <BooleanInput source="is_important" label="⭐ 중요 공지" defaultValue={false} />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <BooleanInput source="is_popup" label="🔔 팝업 표시" defaultValue={false} />
                    </Grid>
                </Grid>

                {/* 게시 기간 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    📅 게시 기간
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <CustomDateInput
                            source="start_date"
                            label="게시 시작일"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <CustomDateInput
                            source="end_date"
                            label="게시 종료일"
                        />
                    </Grid>
                </Grid>

                {/* 통계 정보 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    📊 통계 정보
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                        <NumberField source="view_count" label="조회수" />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <DateField source="created_at" label="생성일시" showTime />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <DateField source="updated_at" label="수정일시" showTime />
                    </Grid>
                </Grid>
            </Box>
        </SimpleForm>
    </Edit>
);

/**
 * 공지사항 생성
 */
export const NoticeCreate = () => (
    <Create>
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                {/* 기본 정보 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📝 기본 정보
                </Typography>
                <TextInput
                    source="title"
                    label="제목"
                    validate={[required()]}
                    fullWidth
                />
                <TextInput
                    source="content"
                    label="내용"
                    validate={[required()]}
                    multiline
                    rows={5}
                    fullWidth
                />

                {/* 설정 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    ⚙️ 공지 설정
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <SelectInput
                            source="priority"
                            label="우선순위"
                            choices={priorityChoices}
                            defaultValue="normal"
                            fullWidth
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Box sx={{ pt: 2 }}>
                            <BooleanInput source="is_active" label="활성화" defaultValue={true} />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <BooleanInput source="is_important" label="⭐ 중요 공지" defaultValue={false} />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <BooleanInput source="is_popup" label="🔔 팝업 표시" defaultValue={false} />
                    </Grid>
                </Grid>

                {/* 게시 기간 섹션 */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    📅 게시 기간
                </Typography>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <CustomDateInput
                            source="start_date"
                            label="게시 시작일"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <CustomDateInput
                            source="end_date"
                            label="게시 종료일"
                        />
                    </Grid>
                </Grid>
            </Box>
        </SimpleForm>
    </Create>
);
