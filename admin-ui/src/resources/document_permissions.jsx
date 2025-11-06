/**
 * 문서 권한 관리 리소스
 * PRD P0: 문서 권한 관리 - 부서별/결재라인별 권한
 *
 * Security:
 * - XSS 방지: react-admin의 자동 sanitization
 * - CSRF 방지: dataProvider에서 처리
 */

import {
    List,
    Datagrid,
    TextField,
    BooleanField,
    DateField,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    ReferenceField,
    ReferenceInput,
    SelectInput,
    BooleanInput,
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
import { Chip, Paper, Grid, Typography, Box, Button } from '@mui/material';

// ============================================
// 문서 권한 목록
// ============================================

const DocumentPermissionListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="권한 추가" />
        <ExportButton />
    </TopToolbar>
);

const documentPermissionFilters = [
    <ReferenceInput key="document_id" source="document_id" reference="documents" label="문서">
        <SelectInput optionText="title" />
    </ReferenceInput>,
    <ReferenceInput key="department_id" source="department_id" reference="departments" label="부서">
        <SelectInput optionText="name" />
    </ReferenceInput>,
];

// Empty state component
const Empty = () => (
    <Box
        sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            textAlign: 'center'
        }}
    >
        <Typography variant="h6" color="text.secondary" gutterBottom>
            데이터가 없습니다
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            추가하시겠습니까?
        </Typography>
        <CreateButton label="권한 추가" />
    </Box>
);

// Custom field for permission target (department or approval line)
const PermissionTargetField = () => {
    const record = useRecordContext();
    if (!record) return null;

    if (record.department_id) {
        return (
            <ReferenceField source="department_id" reference="departments" link="show">
                <TextField source="name" />
            </ReferenceField>
        );
    } else if (record.approval_line_id) {
        return (
            <ReferenceField source="approval_line_id" reference="approval-lines" link="show">
                <TextField source="name" />
            </ReferenceField>
        );
    }
    return <span>-</span>;
};

// Custom field for permission summary
const PermissionSummaryField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const permissions = [];
    if (record.can_read) permissions.push('읽기');
    if (record.can_write) permissions.push('쓰기');
    if (record.can_delete) permissions.push('삭제');

    return (
        <div style={{ display: 'flex', gap: '4px' }}>
            {permissions.map(perm => (
                <Chip
                    key={perm}
                    label={perm}
                    size="small"
                    color={perm === '읽기' ? 'success' : perm === '쓰기' ? 'warning' : 'error'}
                />
            ))}
        </div>
    );
};

export const DocumentPermissionList = () => (
    <List
        filters={documentPermissionFilters}
        actions={<DocumentPermissionListActions />}
        sort={{ field: 'document_id', order: 'ASC' }}
        perPage={50}
        title="문서 권한 관리"
        empty={<Empty />}
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
            <ReferenceField source="document_id" reference="documents" label="문서" link="show" sx={{ width: '250px' }}>
                <TextField source="title" />
            </ReferenceField>
            <PermissionTargetField label="권한 대상" sx={{ width: '200px' }} />
            <PermissionSummaryField label="권한" sx={{ width: '220px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '180px' }} />
            <ShowButton label="상세" sx={{ width: '80px' }} />
            <EditButton label="수정" sx={{ width: '80px' }} />
            <DeleteButton label="삭제" sx={{ width: '80px' }} />
        </Datagrid>
    </List>
);

// ============================================
// 문서 권한 상세
// ============================================

const DocumentPermissionShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                📄 문서 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            권한 ID
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="id" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={9}>
                        <Typography variant="caption" color="text.secondary">
                            문서
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="h6" color="primary">
                                <ReferenceField source="document_id" reference="documents" label="문서" link="show">
                                    <TextField source="title" />
                                </ReferenceField>
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                👥 권한 대상
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            부서
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <ReferenceField source="department_id" reference="departments" label="부서" link="show">
                                <TextField source="name" />
                            </ReferenceField>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            결재라인
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <ReferenceField source="approval_line_id" reference="approval-lines" label="결재라인" link="show">
                                <TextField source="name" />
                            </ReferenceField>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                🔐 권한 설정
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">
                            읽기 권한
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="can_read" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">
                            쓰기 권한
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="can_write" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                        <Typography variant="caption" color="text.secondary">
                            삭제 권한
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="can_delete" />
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

export const DocumentPermissionShow = () => (
    <Show title="문서 권한 상세">
        <DocumentPermissionShowContent />
    </Show>
);

// ============================================
// 문서 권한 수정
// ============================================

export const DocumentPermissionEdit = () => (
    <Edit title="문서 권한 수정" mutationMode="pessimistic">
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📄 문서 선택
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                    <ReferenceInput
                        source="document_id"
                        reference="documents"
                        label="문서"
                        validate={[required()]}
                    >
                        <SelectInput
                            optionText="title"
                            fullWidth
                            disabled
                            helperText="생성 후 변경 불가"
                        />
                    </ReferenceInput>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    👥 권한 대상
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <ReferenceInput
                                source="department_id"
                                reference="departments"
                                label="부서 (선택)"
                            >
                                <SelectInput
                                    optionText="name"
                                    fullWidth
                                    helperText="부서 또는 결재라인 중 하나 선택"
                                />
                            </ReferenceInput>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <ReferenceInput
                                source="approval_line_id"
                                reference="approval-lines"
                                label="결재라인 (선택)"
                            >
                                <SelectInput
                                    optionText="name"
                                    fullWidth
                                    helperText="부서 또는 결재라인 중 하나 선택"
                                />
                            </ReferenceInput>
                        </Grid>
                    </Grid>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    🔐 권한 설정
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={4}>
                            <BooleanInput
                                source="can_read"
                                label="읽기 권한"
                                defaultValue={true}
                                helperText="문서 조회 권한"
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <BooleanInput
                                source="can_write"
                                label="쓰기 권한"
                                defaultValue={false}
                                helperText="문서 수정 권한"
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <BooleanInput
                                source="can_delete"
                                label="삭제 권한"
                                defaultValue={false}
                                helperText="문서 삭제 권한"
                            />
                        </Grid>
                    </Grid>
                </Paper>
            </Box>
        </SimpleForm>
    </Edit>
);

// ============================================
// 문서 권한 생성
// ============================================

export const DocumentPermissionCreate = () => (
    <Create title="문서 권한 생성" redirect="list">
        <SimpleForm
            sx={{
                '& .MuiFormControl-root': { marginBottom: '16px' },
                maxWidth: 800,
                margin: '0 auto'
            }}
        >
            <ReferenceInput
                source="document_id"
                reference="documents"
                label="문서"
                validate={[required()]}
            >
                <SelectInput
                    optionText="title"
                    fullWidth
                    helperText="권한을 부여할 문서 선택"
                />
            </ReferenceInput>

            <ReferenceInput
                source="department_id"
                reference="departments"
                label="부서 (선택)"
            >
                <SelectInput
                    optionText="name"
                    fullWidth
                    helperText="부서 또는 결재라인 중 하나 선택"
                />
            </ReferenceInput>

            <ReferenceInput
                source="approval_line_id"
                reference="approval-lines"
                label="결재라인 (선택)"
            >
                <SelectInput
                    optionText="name"
                    fullWidth
                    helperText="부서 또는 결재라인 중 하나 선택"
                />
            </ReferenceInput>

            <BooleanInput
                source="can_read"
                label="읽기 권한"
                defaultValue={true}
                helperText="문서 조회 권한"
            />

            <BooleanInput
                source="can_write"
                label="쓰기 권한"
                defaultValue={false}
                helperText="문서 수정 권한"
            />

            <BooleanInput
                source="can_delete"
                label="삭제 권한"
                defaultValue={false}
                helperText="문서 삭제 권한"
            />
        </SimpleForm>
    </Create>
);
