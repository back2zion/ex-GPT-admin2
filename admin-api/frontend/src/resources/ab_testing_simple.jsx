/**
 * A/B Testing - Simplified Version
 */
import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    Show,
    SimpleShowLayout,
    Create,
    SimpleForm,
    TextInput,
    ReferenceInput,
    SelectInput,
    NumberInput,
    required,
    minValue,
    maxValue
} from 'react-admin';

export const ABTestingList = () => (
    <List title="🧪 A/B 테스트">
        <Datagrid rowClick="show" bulkActionButtons={false}>
            <TextField source="id" label="ID" />
            <TextField source="test_name" label="테스트 이름" />
            <TextField source="status" label="상태" />
            <NumberField source="traffic_split_a" label="A 트래픽 (%)" />
            <NumberField source="traffic_split_b" label="B 트래픽 (%)" />
            <NumberField source="total_requests" label="총 요청 수" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="started_at" label="시작일" showTime />
        </Datagrid>
    </List>
);

export const ABTestingShow = () => (
    <Show title="A/B 테스트 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="test_name" label="테스트 이름" />
            <TextField source="description" label="설명" />
            <TextField source="status" label="상태" />
            <NumberField source="model_a_id" label="모델 A ID" />
            <NumberField source="model_b_id" label="모델 B ID" />
            <NumberField source="traffic_split_a" label="A 트래픽 (%)" />
            <NumberField source="traffic_split_b" label="B 트래픽 (%)" />
            <NumberField source="total_requests" label="총 요청 수" />
            <NumberField source="model_a_requests" label="모델 A 요청" />
            <NumberField source="model_b_requests" label="모델 B 요청" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="started_at" label="시작일" showTime />
            <DateField source="ended_at" label="종료일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const ABTestingCreate = () => (
    <Create title="🧪 A/B 테스트 생성">
        <SimpleForm>
            <TextInput source="test_name" label="테스트 이름" fullWidth validate={[required()]} />
            <TextInput source="description" label="설명" multiline rows={3} fullWidth />
            <ReferenceInput source="model_a_id" reference="model_registry" label="모델 A" validate={[required()]}>
                <SelectInput optionText="model_name" fullWidth />
            </ReferenceInput>
            <ReferenceInput source="model_b_id" reference="model_registry" label="모델 B" validate={[required()]}>
                <SelectInput optionText="model_name" fullWidth />
            </ReferenceInput>
            <NumberInput 
                source="traffic_split_a" 
                label="모델 A 트래픽 비율 (%)" 
                defaultValue={50} 
                validate={[required(), minValue(0), maxValue(100)]} 
            />
            <NumberInput 
                source="traffic_split_b" 
                label="모델 B 트래픽 비율 (%)" 
                defaultValue={50} 
                validate={[required(), minValue(0), maxValue(100)]} 
            />
        </SimpleForm>
    </Create>
);
