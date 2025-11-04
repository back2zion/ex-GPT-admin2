/**
 * 결재라인 관리 리소스
 * PRD P0: 문서 권한 관리 - 결재라인 기반 권한
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
    SelectArrayInput,
    ReferenceArrayInput,
    required,
    DeleteButton,
    EditButton,
    ShowButton,
    CreateButton,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext
} from 'react-admin';
import { Chip, Box, Paper, Grid, Typography } from '@mui/material';

// ============================================
// 결재라인 목록
// ============================================

const ApprovalLineListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="결재라인 추가" />
        <ExportButton />
    </TopToolbar>
);

const approvalLineFilters = [
    <TextInput key="search" source="search" label="검색" alwaysOn resettable />,
];

// Custom field for departments list
const DepartmentsField = () => {
    const record = useRecordContext();
    if (!record || !record.departments || record.departments.length === 0) {
        return <span>-</span>;
    }

    return (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {record.departments.map((deptId) => (
                <Chip
                    key={deptId}
                    label={`부서 #${deptId}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                />
            ))}
        </Box>
    );
};

export const ApprovalLineList = () => (
    <List
        filters={approvalLineFilters}
        actions={<ApprovalLineListActions />}
        sort={{ field: 'name', order: 'ASC' }}
        perPage={50}
        title="결재라인 관리"
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
            <TextField source="id" label="ID" sortable={false} sx={{ width: '70px' }} />
            <TextField source="name" label="결재라인명" sx={{ width: '200px' }} />
            <TextField source="description" label="설명" sx={{ minWidth: '250px' }} />
            <DepartmentsField label="포함된 부서" sx={{ width: '300px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '180px' }} />
            <ShowButton label="상세" sx={{ width: '80px' }} />
            <EditButton label="수정" sx={{ width: '80px' }} />
            <DeleteButton label="삭제" sx={{ width: '80px' }} />
        </Datagrid>
    </List>
);

// ============================================
// 결재라인 상세
// ============================================

const ApprovalLineShowContent = () => {
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
                    <Grid item xs={12} sm={6} md={9}>
                        <Typography variant="caption" color="text.secondary">
                            결재라인명
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
                🏢 포함된 부서
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                <DepartmentsField label="포함된 부서" />
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

export const ApprovalLineShow = () => (
    <Show title="결재라인 상세">
        <ApprovalLineShowContent />
    </Show>
);

// ============================================
// 결재라인 수정
// ============================================

export const ApprovalLineEdit = () => (
    <Edit title="결재라인 수정" mutationMode="pessimistic">
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📋 기본 정보
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <TextInput
                                source="name"
                                label="결재라인명"
                                validate={[required()]}
                                fullWidth
                                helperText="결재라인의 명칭 (예: 계약승인라인, 예산승인라인)"
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextInput
                                source="description"
                                label="설명"
                                multiline
                                rows={4}
                                fullWidth
                                helperText="결재라인의 용도 및 설명"
                            />
                        </Grid>
                    </Grid>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    🏢 포함된 부서
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                    <ReferenceArrayInput
                        source="departments"
                        reference="departments"
                        label="포함된 부서"
                    >
                        <SelectArrayInput
                            optionText="name"
                            fullWidth
                            helperText="이 결재라인에 포함될 부서들을 선택하세요"
                        />
                    </ReferenceArrayInput>
                </Paper>
            </Box>
        </SimpleForm>
    </Edit>
);

// ============================================
// 결재라인 생성
// ============================================

export const ApprovalLineCreate = () => (
    <Create title="결재라인 생성" redirect="list">
        <SimpleForm
            sx={{
                '& .MuiFormControl-root': { marginBottom: '16px' }
            }}
        >
            <TextInput
                source="name"
                label="결재라인명"
                validate={[required()]}
                fullWidth
                helperText="결재라인의 명칭 (예: 계약승인라인, 예산승인라인)"
            />

            <TextInput
                source="description"
                label="설명"
                multiline
                rows={3}
                fullWidth
                helperText="결재라인의 용도 및 설명"
            />

            <ReferenceArrayInput
                source="departments"
                reference="departments"
                label="포함된 부서"
            >
                <SelectArrayInput
                    optionText="name"
                    fullWidth
                    helperText="이 결재라인에 포함될 부서들을 선택하세요"
                />
            </ReferenceArrayInput>
        </SimpleForm>
    </Create>
);
