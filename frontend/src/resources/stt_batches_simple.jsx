/**
 * STT Batches - Simplified Version
 * 음성 전사 배치 관리 (MUI 제거)
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
    FunctionField,
    required
} from 'react-admin';

/**
 * 상태 선택 옵션
 */
const statusChoices = [
    { id: 'pending', name: '대기 중' },
    { id: 'processing', name: '처리 중' },
    { id: 'completed', name: '완료' },
    { id: 'failed', name: '실패' },
    { id: 'paused', name: '일시정지' },
];

/**
 * 우선순위 선택 옵션
 */
const priorityChoices = [
    { id: 'low', name: '낮음' },
    { id: 'normal', name: '보통' },
    { id: 'high', name: '높음' },
    { id: 'urgent', name: '긴급' },
];

/**
 * 진행률 필드
 */
const ProgressField = ({ source }) => (
    <FunctionField
        source={source}
        render={record => {
            const progress = record.progress || 0;
            const processed = record.processed_count || 0;
            const total = record.total_count || 0;
            return `${progress}% (${processed}/${total})`;
        }}
    />
);

/**
 * 배치 목록
 */
export const STTBatchList = () => (
    <List title="🎙️ STT 음성 전사 배치">
        <Datagrid rowClick="show" bulkActionButtons={false}>
            <TextField source="id" label="ID" />
            <TextField source="batch_name" label="배치 이름" />
            <TextField source="status" label="상태" />
            <TextField source="priority" label="우선순위" />
            <ProgressField source="progress" label="진행률" />
            <NumberField source="total_count" label="총 파일 수" />
            <DateField source="created_at" label="생성일" showTime />
        </Datagrid>
    </List>
);

/**
 * 배치 상세
 */
export const STTBatchShow = () => (
    <Show title="STT 배치 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="batch_name" label="배치 이름" />
            <TextField source="description" label="설명" />
            <TextField source="status" label="상태" />
            <TextField source="priority" label="우선순위" />
            <NumberField source="progress" label="진행률 (%)" />
            <NumberField source="total_count" label="총 파일 수" />
            <NumberField source="processed_count" label="처리된 파일 수" />
            <NumberField source="success_count" label="성공 수" />
            <NumberField source="error_count" label="오류 수" />
            <TextField source="input_folder" label="입력 폴더" />
            <TextField source="output_folder" label="출력 폴더" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="started_at" label="시작 시간" showTime />
            <DateField source="completed_at" label="완료 시간" showTime />
        </SimpleShowLayout>
    </Show>
);

/**
 * 배치 생성
 */
export const STTBatchCreate = () => (
    <Create title="🎙️ STT 배치 생성">
        <SimpleForm>
            <TextInput 
                source="batch_name" 
                label="배치 이름" 
                fullWidth 
                validate={[required()]} 
                helperText="배치를 식별할 수 있는 이름"
            />
            <TextInput 
                source="description" 
                label="설명" 
                multiline 
                rows={3} 
                fullWidth 
                helperText="배치에 대한 설명 (선택 사항)"
            />
            <TextInput 
                source="input_folder" 
                label="입력 폴더 경로" 
                fullWidth 
                validate={[required()]} 
                helperText="음성 파일이 있는 폴더 경로 (예: /data/audio/input)"
                placeholder="/data/audio/input"
            />
            <TextInput 
                source="output_folder" 
                label="출력 폴더 경로" 
                fullWidth 
                helperText="전사 결과를 저장할 폴더 경로 (선택 사항)"
                placeholder="/data/audio/output"
            />
            <SelectInput 
                source="priority" 
                label="우선순위" 
                choices={priorityChoices} 
                defaultValue="normal" 
                validate={[required()]} 
            />
        </SimpleForm>
    </Create>
);
