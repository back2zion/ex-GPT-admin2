/**
 * Fine-tuning Jobs - Simplified Version
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
    SelectInput,
    ReferenceInput,
    NumberInput,
    required,
    minValue,
    maxValue
} from 'react-admin';

const statusLabels = {
    'pending': '대기 중',
    'running': '실행 중',
    'completed': '완료',
    'failed': '실패',
    'cancelled': '취소됨'
};

export const FinetuningJobList = () => (
    <List title="🔧 Fine-tuning 작업">
        <Datagrid rowClick="show" bulkActionButtons={false}>
            <TextField source="id" label="ID" />
            <TextField source="job_name" label="작업 이름" />
            <ReferenceInput source="dataset_id" reference="training_datasets" label="데이터셋">
                <TextField source="name" />
            </ReferenceInput>
            <TextField source="base_model" label="기본 모델" />
            <TextField source="status" label="상태" />
            <NumberField source="progress" label="진행률 (%)" />
            <DateField source="created_at" label="생성일" showTime />
        </Datagrid>
    </List>
);

export const FinetuningJobShow = () => (
    <Show title="Fine-tuning 작업 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="job_name" label="작업 이름" />
            <TextField source="base_model" label="기본 모델" />
            <TextField source="status" label="상태" />
            <NumberField source="progress" label="진행률 (%)" />
            <TextField source="mlflow_run_id" label="MLflow Run ID" />
            <NumberField source="learning_rate" label="학습률" />
            <NumberField source="num_epochs" label="에포크 수" />
            <NumberField source="batch_size" label="배치 크기" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="started_at" label="시작 시간" showTime />
            <DateField source="completed_at" label="완료 시간" showTime />
        </SimpleShowLayout>
    </Show>
);

const baseModelOptions = [
    { id: 'Qwen/Qwen3-32B', name: 'Qwen3-32B (32.8B 파라미터)' },
    { id: 'Qwen/Qwen3-235B-A22B-GPTQ-Int4', name: 'Qwen3-235B-A22B (GPTQ Int4)' },
    { id: 'Qwen/Qwen2.5-7B-Instruct', name: 'Qwen2.5-7B-Instruct (Legacy)' },
];

const finetuningMethodOptions = [
    { id: 'lora', name: 'LoRA (권장 - 메모리 효율적)' },
    { id: 'qlora', name: 'QLoRA (메모리 최적화)' },
    { id: 'full', name: 'Full Fine-tuning (고성능 GPU 필요)' },
];

export const FinetuningJobCreate = () => (
    <Create title="🔧 Fine-tuning 작업 생성">
        <SimpleForm>
            <TextInput source="job_name" label="작업 이름" fullWidth validate={[required()]} />
            <ReferenceInput source="dataset_id" reference="training_datasets" label="데이터셋" validate={[required()]}>
                <SelectInput optionText="name" fullWidth />
            </ReferenceInput>
            <SelectInput
                source="base_model"
                label="기본 모델"
                choices={baseModelOptions}
                defaultValue="Qwen/Qwen3-32B"
                fullWidth
                validate={[required()]}
            />
            <SelectInput
                source="method"
                label="Fine-tuning 방법"
                choices={finetuningMethodOptions}
                defaultValue="lora"
                fullWidth
                validate={[required()]}
                helperText="LoRA 권장: 32B 모델은 Full fine-tuning 시 80GB+ GPU 메모리 필요"
            />
            <NumberInput
                source="learning_rate"
                label="학습률"
                defaultValue={0.0002}
                step={0.00001}
                validate={[required(), minValue(0)]}
                helperText="LoRA/QLoRA: 1e-4 ~ 3e-4 (0.0001 ~ 0.0003)"
            />
            <NumberInput
                source="num_epochs"
                label="에포크 수"
                defaultValue={3}
                validate={[required(), minValue(1), maxValue(100)]}
                helperText="8,000개 샘플: 3-5 에포크 권장"
            />
            <NumberInput
                source="batch_size"
                label="배치 크기"
                defaultValue={4}
                validate={[required(), minValue(1), maxValue(128)]}
                helperText="GPU 메모리에 따라 조정 (4-8 권장)"
            />
            <NumberInput
                source="warmup_steps"
                label="Warmup 스텝"
                defaultValue={500}
                validate={[minValue(0)]}
                helperText="전체 스텝의 5-10% 권장 (8,000샘플 기준: 300-600)"
            />
            <NumberInput
                source="max_length"
                label="최대 토큰 길이"
                defaultValue={2048}
                validate={[minValue(128), maxValue(8192)]}
                helperText="판결문은 2048-4096 권장 (메모리 허용 시)"
            />
        </SimpleForm>
    </Create>
);
