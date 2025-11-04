/**
 * 추천 질문 관리 리소스
 * 서비스 관리 > 추천 질문
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
    EditButton,
    ShowButton,
    CreateButton,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    useUpdate,
    useNotify,
    useRefresh,
    Button,
} from 'react-admin';
import { Block as BlockIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';

// 사용중지/재사용 토글 버튼
const ToggleActiveButton = () => {
    const record = useRecordContext();
    const notify = useNotify();
    const refresh = useRefresh();
    const [update, { isLoading }] = useUpdate();

    if (!record) return null;

    const handleClick = (e) => {
        e.stopPropagation(); // 행 클릭 이벤트 방지

        const newIsActive = !record.is_active;
        const actionLabel = newIsActive ? '재사용' : '사용중지';

        update(
            'recommended_questions',
            {
                id: record.id,
                data: { is_active: newIsActive },
                previousData: record
            },
            {
                onSuccess: () => {
                    notify(`${actionLabel} 처리되었습니다.`, { type: 'success' });
                    refresh();
                },
                onError: (error) => {
                    notify(`${actionLabel} 처리 실패: ${error.message}`, { type: 'error' });
                }
            }
        );
    };

    return (
        <Button
            label={record.is_active ? '사용중지' : '재사용'}
            onClick={handleClick}
            disabled={isLoading}
            sx={{
                color: record.is_active ? '#d32f2f' : '#2e7d32',
                '&:hover': {
                    backgroundColor: record.is_active ? 'rgba(211, 47, 47, 0.04)' : 'rgba(46, 125, 50, 0.04)'
                }
            }}
        >
            {record.is_active ? <BlockIcon /> : <CheckCircleIcon />}
        </Button>
    );
};

const RecommendedQuestionListActions = () => (
    <TopToolbar>
        <FilterButton />
        <CreateButton label="질문 추가" />
        <ExportButton />
    </TopToolbar>
);

export const RecommendedQuestionList = () => (
    <List
        sort={{ field: 'id', order: 'DESC' }}
        perPage={50}
        title="💡 추천 질문"
    >
        <Datagrid>
            <TextField source="id" label="ID" />
            <TextField source="question" label="추천 질문" />
            <TextField source="category" label="카테고리" />
        </Datagrid>
    </List>
);

export const RecommendedQuestionShow = () => (
    <Show title="💡 추천 질문 상세">
        <SimpleShowLayout>
            <TextField source="id" label="ID" />
            <TextField source="question" label="추천 질문" />
            <TextField source="category" label="카테고리" />
            <TextField source="description" label="설명" />
            <NumberField source="display_order" label="표시 순서" />
            <BooleanField source="is_active" label="활성화" />
            <DateField source="created_at" label="생성일" showTime />
            <DateField source="updated_at" label="수정일" showTime />
        </SimpleShowLayout>
    </Show>
);

export const RecommendedQuestionEdit = () => (
    <Edit title="💡 추천 질문 수정">
        <SimpleForm>
            <TextInput source="question" label="추천 질문" validate={[required()]} fullWidth multiline rows={2} />
            <TextInput source="category" label="카테고리" fullWidth />
            <TextInput source="description" label="설명" fullWidth multiline rows={3} />
            <NumberInput source="display_order" label="표시 순서" />
            <BooleanInput source="is_active" label="활성화" />
        </SimpleForm>
    </Edit>
);

export const RecommendedQuestionCreate = () => (
    <Create title="💡 추천 질문 추가" redirect="list">
        <SimpleForm>
            <TextInput source="question" label="추천 질문" validate={[required()]} fullWidth multiline rows={2} />
            <TextInput source="category" label="카테고리" fullWidth />
            <TextInput source="description" label="설명" fullWidth multiline rows={3} />
            <NumberInput source="display_order" label="표시 순서" defaultValue={0} />
            <BooleanInput source="is_active" label="활성화" defaultValue={true} />
        </SimpleForm>
    </Create>
);
