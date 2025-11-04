/**
 * 사용자 관리 리소스
 * PRD P0: 문서 권한 관리 - 사용자-부서 할당, 개별 사용자 권한
 *
 * Security:
 * - XSS 방지: react-admin의 자동 sanitization
 * - CSRF 방지: dataProvider에서 처리
 * - 비밀번호 해싱: 백엔드에서 처리
 */

import {
    List,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    DateField,
    FunctionField,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    BooleanInput,
    PasswordInput,
    ReferenceField,
    ReferenceInput,
    SelectInput,
    required,
    email,
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
// 사용자 목록
// ============================================

const UserListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="사용자 추가" />
        <ExportButton />
    </TopToolbar>
);

const userFilters = [
    <TextInput key="search" source="search" label="검색 (이름/이메일)" alwaysOn resettable />,
    <ReferenceInput key="department_id" source="department_id" reference="departments" label="부서">
        <SelectInput optionText="name" />
    </ReferenceInput>,
];

// Custom field for GPT access status
const GPTAccessField = () => {
    const record = useRecordContext();
    if (!record) return null;

    return record.gpt_access_granted ? (
        <Chip label="허용" size="small" color="success" />
    ) : (
        <Chip label="미허용" size="small" color="default" />
    );
};

export const UserList = () => (
    <List
        filters={userFilters}
        actions={<UserListActions />}
        sort={{ field: 'username', order: 'ASC' }}
        perPage={50}
        title="사용자 관리"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-table': {
                    tableLayout: 'fixed !important',
                    width: '1420px !important',
                    minWidth: '1420px !important',
                    maxWidth: '1420px !important'
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
                    backgroundColor: '#f8f8f8'
                }
            }}
        >
            <TextField source="id" label="ID" sortable={false} sx={{ width: '70px !important', minWidth: '70px !important', maxWidth: '70px !important' }} />
            <TextField source="username" label="사용자명" sortable={false} sx={{ width: '120px !important', minWidth: '120px !important', maxWidth: '120px !important' }} />
            <EmailField source="email" label="이메일" sortable={false} sx={{ width: '240px !important', minWidth: '240px !important', maxWidth: '240px !important' }} />
            <TextField source="full_name" label="이름" sortable={false} sx={{ width: '120px !important', minWidth: '120px !important', maxWidth: '120px !important' }} />
            <ReferenceField source="department_id" reference="departments" label="부서" link="show" sortable={false} sx={{ width: '150px !important', minWidth: '150px !important', maxWidth: '150px !important' }}>
                <TextField source="name" />
            </ReferenceField>
            <FunctionField label="GPT 접근" render={record => <GPTAccessField />} sortable={false} sx={{ width: '100px !important', minWidth: '100px !important', maxWidth: '100px !important' }} />
            <BooleanField source="is_active" label="활성" sortable={false} sx={{ width: '80px !important', minWidth: '80px !important', maxWidth: '80px !important' }} />
            <DateField source="created_at" label="생성일" showTime sortable={false} sx={{ width: '180px !important', minWidth: '180px !important', maxWidth: '180px !important' }} />
            <ShowButton label="상세" sx={{ width: '90px' }} />
            <EditButton label="수정" sx={{ width: '90px' }} />
            <DeleteButton label="삭제" sx={{ width: '90px' }} />
        </Datagrid>
    </List>
);

// ============================================
// 사용자 상세
// ============================================

const UserShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                👤 기본 정보
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
                            사용자명
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="h6" color="primary">
                                <TextField source="username" />
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            이름
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="full_name" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            마지막 로그인
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <DateField source="last_login_at" showTime />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            이메일
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <EmailField source="email" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            소속 부서
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <ReferenceField source="department_id" reference="departments" label="부서" link="show">
                                <TextField source="name" />
                            </ReferenceField>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                🔐 권한 및 접근
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            활성 상태
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="is_active" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            관리자 권한
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="is_superuser" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            GPT 접근 허용
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <BooleanField source="gpt_access_granted" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            허용된 모델
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="allowed_model" />
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

export const UserShow = () => (
    <Show title="사용자 상세">
        <UserShowContent />
    </Show>
);

// ============================================
// 사용자 수정
// ============================================

export const UserEdit = () => (
    <Edit title="사용자 수정" mutationMode="pessimistic">
        <SimpleForm>
            <Box sx={{ width: '100%', maxWidth: 1200 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                    👤 기본 정보
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <TextInput
                                source="username"
                                label="사용자명"
                                validate={[required()]}
                                fullWidth
                                disabled
                                helperText="생성 후 변경 불가"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextInput
                                source="full_name"
                                label="이름"
                                fullWidth
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextInput
                                source="email"
                                label="이메일"
                                validate={[required(), email()]}
                                fullWidth
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <ReferenceInput
                                source="department_id"
                                reference="departments"
                                label="부서"
                            >
                                <SelectInput
                                    optionText="name"
                                    fullWidth
                                    helperText="사용자가 소속된 부서 (기본 문서 접근 권한 결정)"
                                />
                            </ReferenceInput>
                        </Grid>
                    </Grid>
                </Paper>

                <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                    🔐 권한 및 접근
                </Typography>
                <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                            <BooleanInput
                                source="is_active"
                                label="활성 상태"
                                helperText="비활성 사용자는 로그인할 수 없습니다"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <BooleanInput
                                source="is_superuser"
                                label="관리자 권한"
                                helperText="⚠️ 관리자는 모든 권한을 가집니다"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <BooleanInput
                                source="gpt_access_granted"
                                label="GPT 접근 허용"
                                helperText="ex-GPT 서비스 사용 가능 여부"
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextInput
                                source="allowed_model"
                                label="허용된 모델"
                                fullWidth
                                helperText="접근 가능한 모델명 (예: gpt-4, ex-gpt)"
                            />
                        </Grid>
                    </Grid>
                </Paper>
            </Box>
        </SimpleForm>
    </Edit>
);

// ============================================
// 사용자 생성
// ============================================

export const UserCreate = () => (
    <Create title="사용자 생성" redirect="list">
        <SimpleForm
            sx={{
                '& .MuiFormControl-root': { marginBottom: '16px' }
            }}
        >
            <TextInput
                source="username"
                label="사용자명"
                validate={[required()]}
                fullWidth
                helperText="고유한 사용자명 (로그인 ID)"
            />

            <TextInput
                source="email"
                label="이메일"
                validate={[required(), email()]}
                fullWidth
            />

            <PasswordInput
                source="password"
                label="비밀번호"
                validate={[required()]}
                fullWidth
                helperText="최소 8자 이상 권장"
            />

            <TextInput
                source="full_name"
                label="이름"
                fullWidth
            />

            <ReferenceInput
                source="department_id"
                reference="departments"
                label="부서"
            >
                <SelectInput
                    optionText="name"
                    fullWidth
                    helperText="사용자가 소속된 부서 (기본 문서 접근 권한 결정)"
                />
            </ReferenceInput>

            <BooleanInput
                source="gpt_access_granted"
                label="GPT 접근 허용"
                defaultValue={false}
                helperText="ex-GPT 서비스 사용 가능 여부"
            />

            <TextInput
                source="allowed_model"
                label="허용된 모델"
                fullWidth
                helperText="접근 가능한 모델명 (예: gpt-4, ex-gpt)"
            />

            <BooleanInput
                source="is_active"
                label="활성 상태"
                defaultValue={true}
                helperText="비활성 사용자는 로그인할 수 없습니다"
            />

            <BooleanInput
                source="is_superuser"
                label="관리자 권한"
                defaultValue={false}
                helperText="⚠️ 관리자는 모든 권한을 가집니다"
            />
        </SimpleForm>
    </Create>
);
