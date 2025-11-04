/**
 * 문서 관리 리소스
 * PRD: 문서 조회 및 기본 관리
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
    ReferenceField,
    FunctionField,
    ChipField,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext
} from 'react-admin';
import { Chip, Paper, Grid, Typography, Box } from '@mui/material';

// ============================================
// 문서 목록
// ============================================

const DocumentListActions = () => (
    <TopToolbar>
        <FilterButton />
        <ExportButton />
    </TopToolbar>
);

// Document type labels
const documentTypeLabels = {
    'LAW': '법률',
    'REGULATION': '규정',
    'STANDARD': '기준',
    'GUIDELINE': '지침',
    'MANUAL': '매뉴얼',
    'REPORT': '보고서',
    'OTHER': '기타'
};

// Document status labels
const documentStatusLabels = {
    'ACTIVE': '활성',
    'INACTIVE': '비활성',
    'DRAFT': '초안',
    'ARCHIVED': '보관'
};

// Custom field for document type
const DocumentTypeField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const label = documentTypeLabels[record.document_type] || record.document_type;
    const color = record.document_type === 'LAW' ? 'primary' :
                  record.document_type === 'REGULATION' ? 'secondary' :
                  'default';

    return <Chip label={label} size="small" color={color} />;
};

// Custom field for document status
const DocumentStatusField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const label = documentStatusLabels[record.status] || record.status;
    const color = record.status === 'ACTIVE' ? 'success' :
                  record.status === 'DRAFT' ? 'warning' :
                  record.status === 'ARCHIVED' ? 'default' :
                  'error';

    return <Chip label={label} size="small" color={color} />;
};

export const DocumentList = () => (
    <List
        actions={<DocumentListActions />}
        sort={{ field: 'updated_at', order: 'DESC' }}
        perPage={50}
        title="문서 관리"
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
            <TextField source="title" label="문서 제목" sx={{ width: '300px' }} />
            <DocumentTypeField label="문서 유형" sx={{ width: '120px' }} />
            <DocumentStatusField label="상태" sx={{ width: '100px' }} />
            <TextField source="current_version" label="버전" sx={{ width: '100px' }} />
            <DateField source="updated_at" label="수정일" showTime sx={{ width: '180px' }} />
        </Datagrid>
    </List>
);

// ============================================
// 문서 상세
// ============================================

const DocumentShowContent = () => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Box sx={{ width: '100%', maxWidth: 1200 }}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 2 }}>
                📄 문서 기본 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f8f9fa' }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            문서 ID
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="id" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            문서 번호
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="document_id" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            문서 유형
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <DocumentTypeField />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <Typography variant="caption" color="text.secondary">
                            상태
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <DocumentStatusField />
                        </Box>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">
                            문서 제목
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <Typography variant="h6" color="primary">
                                <TextField source="title" />
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📝 문서 내용
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff' }}>
                <Grid container spacing={2}>
                    {record.summary && (
                        <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                                요약
                            </Typography>
                            <Box sx={{ mt: 1, p: 2, backgroundColor: '#f0f7ff', borderRadius: 1 }}>
                                <Typography variant="body1">
                                    {record.summary}
                                </Typography>
                            </Box>
                        </Grid>
                    )}
                    {record.content && (
                        <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                                내용
                            </Typography>
                            <Box sx={{ mt: 1, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1, maxHeight: '400px', overflow: 'auto' }}>
                                <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                                    {record.content}
                                </Typography>
                            </Box>
                        </Grid>
                    )}
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                📎 파일 정보
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#fff9e6' }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            파일명
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="file_name" emptyText="-" />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                        <Typography variant="caption" color="text.secondary">
                            파일 크기
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <FunctionField
                                render={record => record.file_size
                                    ? `${(record.file_size / 1024).toFixed(2)} KB`
                                    : '-'
                                }
                            />
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                        <Typography variant="caption" color="text.secondary">
                            MIME 타입
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="mime_type" emptyText="-" />
                        </Box>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="caption" color="text.secondary">
                            파일 경로
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="file_path" emptyText="-" />
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3, mb: 2 }}>
                🔖 분류 및 버전
            </Typography>
            <Paper elevation={2} sx={{ mb: 3, p: 3, backgroundColor: '#f0f7ff' }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            카테고리
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            {record.category_id ? (
                                <ReferenceField source="category_id" reference="categories" link={false}>
                                    <TextField source="name" />
                                </ReferenceField>
                            ) : (
                                <Typography variant="body2">-</Typography>
                            )}
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="caption" color="text.secondary">
                            현재 버전
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                            <TextField source="current_version" emptyText="-" />
                        </Box>
                    </Grid>
                    {record.legacy_id && (
                        <Grid item xs={12} sm={6}>
                            <Typography variant="caption" color="text.secondary">
                                레거시 ID
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                                <TextField source="legacy_id" />
                            </Box>
                        </Grid>
                    )}
                    {record.legacy_updated_at && (
                        <Grid item xs={12} sm={6}>
                            <Typography variant="caption" color="text.secondary">
                                레거시 업데이트 일시
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                                <TextField source="legacy_updated_at" />
                            </Box>
                        </Grid>
                    )}
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
                {record.doc_metadata && (
                    <Grid item xs={12}>
                        <Paper elevation={1} sx={{ p: 2 }}>
                            <Typography variant="caption" color="text.secondary">
                                문서 메타데이터 (JSON)
                            </Typography>
                            <Box sx={{ mt: 1, p: 2, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
                                <pre style={{ margin: 0, fontSize: '12px', overflow: 'auto' }}>
                                    {JSON.stringify(record.doc_metadata, null, 2)}
                                </pre>
                            </Box>
                        </Paper>
                    </Grid>
                )}
            </Grid>
        </Box>
    );
};

export const DocumentShow = () => (
    <Show title="문서 상세">
        <DocumentShowContent />
    </Show>
);
