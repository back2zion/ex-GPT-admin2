/**
 * Training Datasets - Simplified Version (MUI 제거)
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
    FileInput,
    FileField,
    required
} from 'react-admin';

const formatOptions = [
    { id: 'jsonl', name: 'JSONL' },
    { id: 'json', name: 'JSON' },
    { id: 'zip', name: 'ZIP (여러 JSON 파일)' },
    { id: 'csv', name: 'CSV' },
    { id: 'parquet', name: 'Parquet' }
];

export const TrainingDatasetList = () => (
    <List title="📊 학습 데이터셋">
        <Datagrid rowClick="show" bulkActionButtons={false}>
            <TextField source="id" label="ID" />
            <TextField source="name" label="데이터셋 이름" />
            <TextField source="version" label="버전" />
            <TextField source="format" label="형식" />
            <NumberField source="total_samples" label="총 샘플 수" />
            <TextField source="status" label="상태" />
            <DateField source="created_at" label="생성일" showTime />
        </Datagrid>
    </List>
);

export const TrainingDatasetShow = () => (
    <Show title="데이터셋 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="name" label="데이터셋 이름" />
            <TextField source="version" label="버전" />
            <TextField source="format" label="형식" />
            <TextField source="description" label="설명" />
            <NumberField source="total_samples" label="총 샘플 수" />
            <NumberField source="train_samples" label="학습 샘플" />
            <NumberField source="val_samples" label="검증 샘플" />
            <NumberField source="test_samples" label="테스트 샘플" />
            <TextField source="status" label="상태" />
            <TextField source="file_path" label="파일 경로" />
            <DateField source="created_at" label="생성일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const TrainingDatasetCreate = () => (
    <Create title="📤 데이터셋 업로드">
        <SimpleForm>
            <TextInput
                source="name"
                label="데이터셋 이름"
                fullWidth
                validate={[required()]}
                helperText="데이터셋을 식별할 수 있는 이름 (예: legal_qa_v1)"
            />
            <TextInput
                source="version"
                label="버전"
                defaultValue="v1.0"
                fullWidth
                validate={[required()]}
                helperText="데이터셋 버전 (예: v1.0, v2.1)"
            />
            <SelectInput
                source="format"
                label="파일 형식"
                choices={formatOptions}
                defaultValue="jsonl"
                validate={[required()]}
                fullWidth
                helperText="JSONL 권장 (대용량 데이터 처리에 최적화)"
            />
            <FileInput
                source="file"
                label="데이터셋 파일"
                accept=".jsonl,.json,.csv,.parquet,.zip"
                validate={[required()]}
                helperText="최대 1GB. 여러 JSON 파일은 ZIP으로 압축하여 업로드하세요. (폴더 구조 유지 가능)"
            >
                <FileField source="src" title="title" />
            </FileInput>
            <TextInput
                source="description"
                label="설명"
                multiline
                rows={3}
                fullWidth
                helperText="데이터셋에 대한 설명 (선택 사항)"
            />
        </SimpleForm>
    </Create>
);
