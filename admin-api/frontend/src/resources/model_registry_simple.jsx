/**
 * Model Registry - Simplified Version
 */
import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    Show,
    SimpleShowLayout
} from 'react-admin';

export const ModelRegistryList = () => (
    <List title="📦 모델 레지스트리">
        <Datagrid rowClick="show" bulkActionButtons={false}>
            <TextField source="id" label="ID" />
            <TextField source="model_name" label="모델 이름" />
            <TextField source="version" label="버전" />
            <TextField source="base_model" label="기본 모델" />
            <TextField source="status" label="상태" />
            <NumberField source="model_size_mb" label="크기 (MB)" />
            <DateField source="created_at" label="생성일" showTime />
        </Datagrid>
    </List>
);

export const ModelRegistryShow = () => (
    <Show title="모델 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="model_name" label="모델 이름" />
            <TextField source="version" label="버전" />
            <TextField source="base_model" label="기본 모델" />
            <TextField source="description" label="설명" />
            <TextField source="status" label="상태" />
            <TextField source="model_path" label="모델 경로" />
            <NumberField source="model_size_mb" label="크기 (MB)" />
            <TextField source="mlflow_model_uri" label="MLflow URI" />
            <NumberField source="finetuning_job_id" label="Fine-tuning 작업 ID" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="registered_at" label="등록일" showTime />
        </SimpleShowLayout>
    </Show>
);
