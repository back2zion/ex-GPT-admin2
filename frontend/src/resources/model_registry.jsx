/**
 * Model Registry 리소스 (간소화 버전)
 *
 * Features:
 * - 모델 목록 및 검색
 * - 모델 상세 정보
 * - 프로모션 (staging → production)
 * - 벤치마크 결과 표시
 */

import {
    List,
    Datagrid,
    TextField,
    DateField,
    NumberField,
    Show,
    SimpleShowLayout,
    TopToolbar,
    FilterButton,
    ExportButton,
    useRecordContext,
    FunctionField,
    ChipField
} from 'react-admin';
import {
    Chip,
    Paper,
    Grid,
    Typography,
    Box,
    Card,
    CardContent
} from '@mui/material';
import {
    Star as StarIcon,
    Archive as ArchiveIcon,
    Science as ScienceIcon
} from '@mui/icons-material';

// Status colors
const statusColors = {
    'staging': 'warning',
    'production': 'success',
    'archived': 'default'
};

const statusIcons = {
    'staging': <ScienceIcon fontSize="small" />,
    'production': <StarIcon fontSize="small" />,
    'archived': <ArchiveIcon fontSize="small" />
};

// Custom Fields
const ModelStatusField = () => {
    const record = useRecordContext();
    if (!record) return null;

    const color = statusColors[record.status] || 'default';
    const icon = statusIcons[record.status];

    return (
        <Chip
            label={record.status?.toUpperCase()}
            size="small"
            color={color}
            icon={icon}
        />
    );
};

const TagsField = () => {
    const record = useRecordContext();
    if (!record || !record.tags) return null;

    return (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {record.tags.map((tag, index) => (
                <Chip key={index} label={tag} size="small" variant="outlined" />
            ))}
        </Box>
    );
};

// List View
const ModelListActions = () => (
    <TopToolbar>
        <FilterButton />
        <ExportButton />
    </TopToolbar>
);

export const ModelRegistryList = () => (
    <List
        actions={<ModelListActions />}
        sort={{ field: 'created_at', order: 'DESC' }}
        perPage={25}
        title="📦 모델 레지스트리"
    >
        <Datagrid
            rowClick="show"
            bulkActionButtons={false}
            sx={{
                '& .RaDatagrid-headerCell': {
                    backgroundColor: '#6a1b9a',
                    color: 'white',
                    fontWeight: 'bold'
                }
            }}
        >
            <TextField source="id" label="ID" sx={{ width: '60px' }} />
            <TextField source="model_name" label="모델 이름" sx={{ width: '200px' }} />
            <TextField source="version" label="버전" sx={{ width: '80px' }} />
            <TextField source="base_model" label="베이스 모델" sx={{ width: '200px' }} />
            <ModelStatusField label="상태" sx={{ width: '120px' }} />
            <NumberField source="model_size_gb" label="크기(GB)" options={{ maximumFractionDigits: 1 }} sx={{ width: '100px' }} />
            <TagsField label="태그" sx={{ width: '200px' }} />
            <DateField source="created_at" label="생성일" showTime sx={{ width: '160px' }} />
        </Datagrid>
    </List>
);

// Show View
export const ModelRegistryShow = () => (
    <Show title="모델 상세">
        <SimpleShowLayout>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>📦 모델 정보</Typography>
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <TextField source="model_name" label="모델 이름" />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField source="version" label="버전" />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField source="base_model" label="베이스 모델" />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <ModelStatusField label="상태" />
                    </Grid>
                    <Grid item xs={12}>
                        <TextField source="description" label="설명" />
                    </Grid>
                    <Grid item xs={12}>
                        <TextField source="model_path" label="모델 경로" />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <NumberField source="model_size_gb" label="모델 크기(GB)" />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField source="model_format" label="포맷" />
                    </Grid>
                    <Grid item xs={12}>
                        <TagsField label="태그" />
                    </Grid>
                </Grid>
            </Paper>

            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>⏱️ 생성 정보</Typography>
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                        <DateField source="created_at" label="생성일" showTime />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <DateField source="updated_at" label="수정일" showTime />
                    </Grid>
                </Grid>
            </Paper>
        </SimpleShowLayout>
    </Show>
);
