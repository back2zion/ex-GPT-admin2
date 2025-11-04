/**
 * 부서 관리 리소스
 * PRD P0: 문서 권한 관리 - 부서별 권한
 *
 * Security:
 * - XSS 방지: react-admin의 자동 sanitization
 * - CSRF 방지: dataProvider에서 처리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    required,
    BooleanField,
    ReferenceField,
    ReferenceInput,
    SelectInput,
    DeleteButton,
    EditButton,
    ShowButton,
    CreateButton,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext
} from 'react-admin';
import { Paper, Grid, Typography, Box } from '@mui/material';

// ============================================
// 부서 목록
// ============================================

const DepartmentListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="부서 추가" />
        <ExportButton />
    </TopToolbar>
);

const departmentFilters = [
    <TextInput key="search" source="search" label="검색" alwaysOn resettable />,
];

export const DepartmentList = () => (
    <List
        filters={departmentFilters}
        actions={<DepartmentListActions />}
        sort={{ field: 'code', order: 'ASC' }}
        perPage={50}
        title="부서 관리"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-table': {
                    tableLayout: 'fixed',
                    width: '100%'
                },
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#0a2986',
                    color: 'white',
                    fontWeight: 'bold'
                },
                '& .RaDatagrid-row:hover': {
                    backgroundColor: '#f8f8f8'
                }
            }}
        >
            <TextField source="id" label="ID" sortable={true} sx={{ width: '70px' }} />
            <TextField source="code" label="부서 코드" sortable={true} sx={{ width: '180px' }} />
            <TextField source="name" label="부서명" sortable={true} sx={{ width: '200px' }} />
            <TextField source="description" label="설명" sortable={true} sx={{ minWidth: '300px' }} />
            <ReferenceField
                source="parent_id"
                reference="departments"
                label="상위 부서"
                link="show"
                sortable={false}
                sx={{ width: '180px' }}
            >
                <TextField source="name" />
            </ReferenceField>
            <DateField source="created_at" label="생성일" showTime sortable={true} sx={{ width: '180px' }} />
            <ShowButton label="상세" />
            <EditButton label="수정" />
            <DeleteButton label="삭제" />
        </Datagrid>
    </List>
);

// ============================================
// 부서 상세
// ============================================

const DepartmentShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                📋 기본 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            ID
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="id" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            부서 코드
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="code" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={6}>
                        <Typography variant="caption" color="text.secondary">
                            부서명
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="h6" color="primary">
                                <TextField source="name" />
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">
                            설명
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                                <TextField source="description" />
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                🏢 조직 구조
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            상위 부서
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <ReferenceField
                                source="parent_id"
                                reference="departments"
                                label="상위 부서"
                                link="show"
                            >
                                <TextField source="name" />
                            </ReferenceField>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📊 메타데이터
            </Typography>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                            생성일시
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="created_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                            수정일시
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="updated_at" showTime />
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export const DepartmentShow = () => (
    <Show title="부서 상세">
        <DepartmentShowContent />
    </Show>
);

// ============================================
// 부서 수정
// ============================================

export const DepartmentEdit = () => (
    <Edit title="부서 수정" mutationMode="pessimistic">
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📋 기본 정보
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <TextInput
                                source="code"
                                label="부서 코드"
                                validate={[required()]}
                                fullWidth
                                helperText="영문 대문자 및 숫자 조합 (예: TECH, FIN)"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextInput
                                source="name"
                                label="부서명"
                                validate={[required()]}
                                fullWidth
                                helperText="부서의 정식 명칭"
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextInput
                                source="description"
                                label="설명"
                                multiline
                                rows={4}
                                fullWidth
                                helperText="부서의 역할 및 업무 설명"
                            />
                        </Grid>
                    </Grid>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    🏢 조직 구조
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                    <ReferenceInput
                        source="parent_id"
                        reference="departments"
                        label="상위 부서"
                    >
                        <SelectInput
                            optionText="name"
                            fullWidth
                            helperText="계층 구조가 있는 경우 선택"
                        />
                    </ReferenceInput>
                </Paper>
            </Box>
        </SimpleForm>
    </Edit>
);

// ============================================
// 부서 생성
// ============================================

export const DepartmentCreate = () => (
    <Create title="부서 생성" redirect="list">
        <SimpleForm
            sx={{
                '& .MuiFormControl-root': { marginBottom: '16px' }
            }}
        >
            <TextInput
                source="code"
                label="부서 코드"
                validate={[required()]}
                fullWidth
                helperText="영문 대문자 및 숫자 조합 (예: TECH, FIN)"
            />
            <TextInput
                source="name"
                label="부서명"
                validate={[required()]}
                fullWidth
                helperText="부서의 정식 명칭"
            />
            <TextInput
                source="description"
                label="설명"
                multiline
                rows={3}
                fullWidth
                helperText="부서의 역할 및 업무 설명"
            />
            <ReferenceInput
                source="parent_id"
                reference="departments"
                label="상위 부서"
            >
                <SelectInput
                    optionText="name"
                    fullWidth
                    helperText="계층 구조가 있는 경우 선택"
                />
            </ReferenceInput>
        </SimpleForm>
    </Create>
);
