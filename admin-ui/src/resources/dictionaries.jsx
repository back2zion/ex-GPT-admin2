/**
 * 사전 관리 리소스
 * 학습 데이터 > 사전 관리
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    BooleanField,
    Show,
    SimpleShowLayout,
    Edit,
    Create,
    SimpleForm,
    TextInput,
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

const DictionaryListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="용어 추가" />
        <ExportButton />
    </TopToolbar>
);

export const DictionaryList = () => (
    <List
        sort={{ field: 'dict_id', order: 'DESC' }}
        perPage={50}
        title="📖 사전 관리"
    >
        <Datagrid>
            <TextField source="dict_id" label="ID" />
            <TextField source="dict_name" label="사전명" />
            <TextField source="dict_type" label="유형" />
            <TextField source="dict_desc" label="설명" />
        </Datagrid>
    </List>
);

export const DictionaryShow = () => (
    <Show title="📖 사전 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="term" label="용어" />
            <TextField source="definition" label="정의" />
            <TextField source="category" label="카테고리" />
            <TextField source="synonyms" label="동의어" />
            <BooleanField source="is_active" label="활성화" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="updated_at" label="수정일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const DictionaryEdit = () => (
    <Edit title="📖 사전 수정">
        <SimpleForm>
            <TextInput source="term" label="용어" validate={[required()]} fullWidth />
            <TextInput source="definition" label="정의" validate={[required()]} fullWidth multiline rows={3} />
            <TextInput source="category" label="카테고리" fullWidth />
            <TextInput source="synonyms" label="동의어 (쉼표로 구분)" fullWidth />
            <BooleanInput source="is_active" label="활성화" />
        </SimpleForm>
    </Edit>
);

export const DictionaryCreate = () => (
    <Create title="📖 사전 추가" redirect="list">
        <SimpleForm>
            <TextInput source="term" label="용어" validate={[required()]} fullWidth />
            <TextInput source="definition" label="정의" validate={[required()]} fullWidth multiline rows={3} />
            <TextInput source="category" label="카테고리" fullWidth />
            <TextInput source="synonyms" label="동의어 (쉼표로 구분)" fullWidth />
            <BooleanInput source="is_active" label="활성화" defaultValue={true} />
        </SimpleForm>
    </Create>
);
