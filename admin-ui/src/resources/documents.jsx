/**
 * Documents Resource - 문서 관리
 * document-permissions에서 참조하기 위한 리소스
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    Show,
    SimpleShowLayout,
    Filter,
    TextInput,
    SelectInput,
    useRecordContext,
} from 'react-admin';
import { Chip, Box, Typography } from '@mui/material';

/**
 * 문서 상태 표시 필드
 */
const StatusField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const statusMap = {
        active: { label: '활성', color: 'success' },
        inactive: { label: '비활성', color: 'default' },
        archived: { label: '보관', color: 'warning' },
    };

    const status = statusMap[record.status] || { label: record.status, color: 'default' };

    return <Chip label={status.label} color={status.color} size="small" />;
};

/**
 * 문서 필터
 */
const documentFilters = [
    <TextInput key="search" source="search" label="검색 (제목/내용)" alwaysOn resettable />,
    <SelectInput
        key="status"
        source="status"
        label="상태"
        choices={[
            { id: 'active', name: '활성' },
            { id: 'inactive', name: '비활성' },
            { id: 'archived', name: '보관' },
        ]}
        alwaysOn
    />,
];

/**
 * Empty state
 */
const EmptyDocumentList = () => (
    <Box sx={{ textAlign: 'center', py: 8, px: 3 }}>
        <Typography variant="h4" sx={{ fontSize: 80, mb: 2 }}>📄</Typography>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
            문서가 없습니다
        </Typography>
        <Typography variant="body1" color="text.secondary">
            문서 업로드 후 여기에 표시됩니다.
        </Typography>
    </Box>
);

/**
 * 문서 목록
 */
export const DocumentList = () => (
    <List
        filters={documentFilters}
        sort={{ field: 'id', order: 'DESC' }}
        perPage={50}
        title="📄 문서 관리"
        empty={<EmptyDocumentList />}
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#0a2986',
                    color: 'white',
                    fontWeight: 'bold',
                },
            }}
        >
            <TextField source="id" label="ID" />
            <TextField source="title" label="제목" />
            <TextField source="document_type" label="문서 유형" />
            <StatusField source="status" label="상태" />
            <DateField source="created_at" label="생성일" showTime />
        </Datagrid>
    </List>
);

/**
 * 문서 상세
 */
export const DocumentShow = () => (
    <Show title="문서 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="title" label="제목" />
            <TextField source="document_type" label="문서 유형" />
            <StatusField source="status" label="상태" />
            <TextField source="file_name" label="파일명" />
            <TextField source="file_path" label="파일 경로" />
            <TextField source="summary" label="요약" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="updated_at" label="수정일" showTime />
        </SimpleShowLayout>
    </Show>
);
