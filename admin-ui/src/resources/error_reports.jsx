/**
 * 오류 보고 관리 리소스
 * 서비스 관리 > 오류 보고
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

const ErrorReportListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="오류 추가" />
        <ExportButton label="엑셀 다운로드" />
    </TopToolbar>
);

export const ErrorReportList = () => (
    <List
        sort={{ field: 'id', order: 'DESC' }}
        perPage={50}
        title="🚨 오류 보고"
    >
        <Datagrid>
            <TextField source="id" label="ID" />
            <TextField source="error_type" label="오류 유형" />
            <TextField source="error_message" label="오류 메시지" />
            <TextField source="severity" label="심각도" />
        </Datagrid>
    </List>
);

export const ErrorReportShow = () => (
    <Show title="🚨 오류 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="error_type" label="오류 유형" />
            <TextField source="error_message" label="오류 메시지" />
            <TextField source="stack_trace" label="스택 트레이스" />
            <TextField source="user_id" label="사용자 ID" />
            <TextField source="session_id" label="세션 ID" />
            <TextField source="severity" label="심각도" />
            <TextField source="resolution_notes" label="해결 노트" />
            <BooleanField source="is_resolved" label="해결 여부" />
            <DateField source="created_at" label="발생일" showTime />
            <DateField source="resolved_at" label="해결일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const ErrorReportEdit = () => (
    <Edit title="🚨 오류 수정">
        <SimpleForm>
            <TextInput source="error_type" label="오류 유형" validate={[required()]} fullWidth />
            <TextInput source="error_message" label="오류 메시지" validate={[required()]} fullWidth multiline rows={3} />
            <TextInput source="stack_trace" label="스택 트레이스" fullWidth multiline rows={5} />
            <TextInput source="severity" label="심각도" fullWidth />
            <TextInput source="resolution_notes" label="해결 노트" fullWidth multiline rows={3} />
            <BooleanInput source="is_resolved" label="해결 여부" />
        </SimpleForm>
    </Edit>
);

export const ErrorReportCreate = () => (
    <Create title="🚨 오류 추가" redirect="list">
        <SimpleForm>
            <TextInput source="error_type" label="오류 유형" validate={[required()]} fullWidth />
            <TextInput source="error_message" label="오류 메시지" validate={[required()]} fullWidth multiline rows={3} />
            <TextInput source="stack_trace" label="스택 트레이스" fullWidth multiline rows={5} />
            <TextInput source="user_id" label="사용자 ID" fullWidth />
            <TextInput source="session_id" label="세션 ID" fullWidth />
            <TextInput source="severity" label="심각도" fullWidth />
            <BooleanInput source="is_resolved" label="해결 여부" defaultValue={false} />
        </SimpleForm>
    </Create>
);
