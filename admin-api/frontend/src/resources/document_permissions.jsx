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
    AutocompleteInput,
    BooleanInput,
    FunctionField,
    required,
    DeleteButton,
    EditButton,
    ShowButton,
    CreateButton,
    SaveButton,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    Toolbar,
    Button
} from 'react-admin';
import { Chip, Paper, Grid, Typography, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';

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
    <ReferenceInput
        key="document_id"
        source="document_id"
        reference="vector-documents"
        label="문서"
        alwaysOn
    >
        <AutocompleteInput optionText="title" />
    </ReferenceInput>,
    <ReferenceInput
        key="department_id"
        source="department_id"
        reference="departments"
        label="부서"
    >
        <AutocompleteInput optionText="name" />
    </ReferenceInput>,
    <ReferenceInput
        key="approval_line_id"
        source="approval_line_id"
        reference="approval-lines"
        label="결재라인"
    >
        <AutocompleteInput optionText="name" />
    </ReferenceInput>,
];

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
    if (record.can_read) permissions.push({ label: '읽기', color: 'success', icon: '✓' });
    if (record.can_write) permissions.push({ label: '쓰기', color: 'warning', icon: '✓' });
    if (record.can_delete) permissions.push({ label: '삭제', color: 'error', icon: '✓' });

    if (permissions.length === 0) {
        return <Chip label="권한 없음" size="small" color="default" />;
    }

    return (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {permissions.map(perm => (
                <Chip
                    key={perm.label}
                    label={perm.label}
                    size="small"
                    color={perm.color}
                    sx={{
                        fontWeight: 500,
                        '& .MuiChip-label': {
                            paddingLeft: '8px',
                            paddingRight: '8px'
                        }
                    }}
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
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-table': {
                    tableLayout: 'fixed !important',
                    width: '1300px !important',
                    minWidth: '1300px !important',
                    maxWidth: '1300px !important'
                },
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#0a2986',
                    color: 'white !important',
                    fontWeight: 'bold',
                    padding: '12px 8px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    boxSizing: 'border-box',
                    '& .MuiTableSortLabel-root': {
                        color: 'white !important',
                        '&:hover': {
                            color: 'white !important'
                        },
                        '&.Mui-active': {
                            color: 'white !important',
                            '& .MuiTableSortLabel-icon': {
                                color: 'white !important'
                            }
                        }
                    },
                    '& .MuiTableSortLabel-icon': {
                        color: 'white !important'
                    }
                },
                '& .RaDatagrid-rowCell': {
                    padding: '12px 8px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    boxSizing: 'border-box'
                },
                '& .RaDatagrid-row:hover': {
                    backgroundColor: '#f8f8f8',
                    cursor: 'pointer'
                }
            }}
        >
            <TextField source="id" label="ID" sortable={false} sx={{ width: '80px !important', minWidth: '80px !important', maxWidth: '80px !important' }} />
            <FunctionField
                label="문서"
                sortable={false}
                sx={{ width: '400px !important', minWidth: '400px !important', maxWidth: '400px !important' }}
                render={record => record.document?.title || '-'}
            />
            <FunctionField label="권한 대상" render={record => <PermissionTargetField />} sortable={false} sx={{ width: '250px !important', minWidth: '250px !important', maxWidth: '250px !important' }} />
            <FunctionField label="권한" render={record => <PermissionSummaryField />} sortable={false} sx={{ width: '250px !important', minWidth: '250px !important', maxWidth: '250px !important' }} />
            <DateField source="created_at" label="생성일" showTime sortable={false} sx={{ width: '180px !important', minWidth: '180px !important', maxWidth: '180px !important' }} />
            <ShowButton label="상세" sx={{ width: '90px' }} />
            <EditButton label="수정" sx={{ width: '90px' }} />
            <DeleteButton label="삭제" sx={{ width: '90px' }} />
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
                                <FunctionField render={record => record.document?.title || `문서 ID: ${record.document_id}`} />
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
                        reference="vector-documents"
                        label="문서"
                        validate={[required()]}
                    >
                        <AutocompleteInput
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
                                <AutocompleteInput
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
                                <AutocompleteInput
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

// Custom Toolbar with Save and Cancel buttons
const CreateEditToolbar = () => {
    const navigate = useNavigate();

    return (
        <Toolbar>
            <SaveButton label="저장" />
            <Button
                label="취소"
                onClick={() => navigate('/document-permissions')}
                sx={{ marginLeft: 2 }}
            />
        </Toolbar>
    );
};

export const DocumentPermissionCreate = () => (
    <Create title="문서 권한 생성" redirect="list">
        <SimpleForm
            toolbar={<CreateEditToolbar />}
            sx={{
                maxWidth: '800px',
                margin: '0 auto',
                '& .MuiFormControl-root': { marginBottom: '16px' }
            }}
        >
            <Box sx={{ width: '100%', maxWidth: 800 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    📄 문서 선택
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                    <ReferenceInput
                        source="document_id"
                        reference="vector-documents"
                        label="문서"
                        validate={[required()]}
                    >
                        <AutocompleteInput
                            optionText="title"
                            fullWidth
                            helperText="권한을 부여할 문서 선택 (검색 가능)"
                        />
                    </ReferenceInput>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    👥 권한 대상 (부서 또는 결재라인 중 하나 선택)
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <ReferenceInput
                                source="department_id"
                                reference="departments"
                                label="부서"
                            >
                                <AutocompleteInput
                                    optionText="name"
                                    fullWidth
                                    helperText="부서 선택 시 결재라인은 비워두세요 (검색 가능)"
                                />
                            </ReferenceInput>
                        </Grid>
                        <Grid item xs={12}>
                            <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', my: 1, color: 'text.secondary' }}>
                                또는
                            </Typography>
                        </Grid>
                        <Grid item xs={12}>
                            <ReferenceInput
                                source="approval_line_id"
                                reference="approval-lines"
                                label="결재라인"
                            >
                                <AutocompleteInput
                                    optionText="name"
                                    fullWidth
                                    helperText="결재라인 선택 시 부서는 비워두세요 (검색 가능)"
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
    </Create>
);
