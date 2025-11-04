/**
 * 벡터 문서 관리 리소스
 * 학습 데이터 > 대상 문서 관리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    BooleanField,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    TextInput,
    NumberInput,
    BooleanInput,
    required,
    DeleteButton,
    EditButton,
    ShowButton,
    CreateButton,
    TopToolbar,
    FilterButton,
    ExportButton,
} from 'react-admin';

const VectorDocumentListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="문서 추가" />
        <ExportButton />
    </TopToolbar>
);

export const VectorDocumentList = () => (
    <List
        sort={{ field: 'id', order: 'DESC' }}
        perPage={50}
        title="📚 대상 문서 관리"
    >
        <Datagrid>
            <TextField source="id" label="ID" />
            <TextField source="title" label="문서 제목" />
            <TextField source="doctype_name" label="문서 유형" />
        </Datagrid>
    </List>
);

export const VectorDocumentShow = () => (
    <Show title="📚 문서 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="title" label="문서 제목" />
            <TextField source="doctype_name" label="문서 유형" />
            <TextField source="doctype" label="문서 코드" />
            <TextField source="metadata_uri" label="메타데이터 URI" />
            <NumberField source="token_count" label="토큰 수" />
            <BooleanField source="is_active" label="활성화" />
            <DateField source="created_at" label="생성일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const VectorDocumentEdit = () => (
    <Edit title="📚 문서 수정">
        <SimpleForm>
            <TextInput source="title" label="문서 제목" validate={[required()]} fullWidth />
            <TextInput source="category" label="카테고리" fullWidth />
            <BooleanInput source="is_active" label="활성화" />
        </SimpleForm>
    </Edit>
);

export const VectorDocumentCreate = () => (
    <Create title="📚 문서 생성">
        <SimpleForm>
            <TextInput source="title" label="문서 제목" validate={[required()]} fullWidth />
            <TextInput source="category" label="카테고리" fullWidth />
            <TextInput source="file_path" label="파일 경로" validate={[required()]} fullWidth />
            <NumberInput source="chunk_count" label="청크 수" defaultValue={0} />
            <BooleanInput source="is_active" label="활성화" defaultValue={true} />
        </SimpleForm>
    </Create>
);
