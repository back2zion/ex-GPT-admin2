/**
 * ex-GPT 통계 대시보드 - 대폭 개선 버전
 * 사용자 요구사항:
 * 1. 기간 조회에 조회/초기화 버튼 추가
 * 2. 각 섹션에 엑셀 다운로드 버튼 추가
 * 3. 오류신고수 섹션 및 그래프 추가
 * 4. 질문수/오류신고수 통합 그래프 (토글)
 * 5. 문서 등록현황 섹션 추가
 * 6. 카테고리별 자동분류 섹션 추가
 * 7. 분야별 질문수 원 그래프 추가
 */

import { useState, useEffect } from 'react';
import {
    Card, CardContent, Typography, Grid, Box, CircularProgress, Paper,
    TextField, Button, IconButton, ToggleButtonGroup, ToggleButton, Table,
    TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import 'dayjs/locale/ko';
import {
    AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
    QuestionAnswer as QuestionAnswerIcon,
    Speed as SpeedIcon,
    People as PeopleIcon,
    TrendingUp as TrendingUpIcon,
    Download as DownloadIcon,
    CalendarToday as CalendarIcon,
    Error as ErrorIcon,
    Description as DescriptionIcon,
    Category as CategoryIcon,
    PieChart as PieChartIcon,
    Refresh as RefreshIcon,
    Search as SearchIcon,
} from '@mui/icons-material';
import {
    getStatisticsSummary,
    getDailyStatistics,
    getErrorReportsDaily,
    getDocumentsByCategory,
    getQuestionsByField,
} from '../utils/api';
import * as XLSX from 'xlsx';

// dayjs 한국어 설정
dayjs.locale('ko');

// 한국도로공사 브랜드 컬러
const colors = {
    primary: '#0a2986',
    primaryLight: '#1e3a8a',
    accent: '#e64701',
    accentLight: '#f97316',
    success: '#10b981',
    successLight: '#34d399',
    info: '#3b82f6',
    infoLight: '#60a5fa',
    error: '#ef4444',
    errorLight: '#f87171',
    warning: '#f59e0b',
};

// 그라데이션 통계 카드 컴포넌트
const GradientStatCard = ({ title, value, unit, icon: Icon, gradient, loading }) => (
    <Card
        sx={{
            height: '100%',
            background: `linear-gradient(135deg, ${gradient[0]} 0%, ${gradient[1]} 100%)`,
            color: 'white',
            boxShadow: '0 4px 20px 0 rgba(0,0,0,0.12)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 30px 0 rgba(0,0,0,0.18)',
            },
        }}
    >
        <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1, fontWeight: 500 }}>
                        {title}
                    </Typography>
                    {loading ? (
                        <CircularProgress size={32} sx={{ color: 'white' }} />
                    ) : (
                        <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                            {value}
                            <Typography component="span" variant="h6" sx={{ ml: 0.5, opacity: 0.9 }}>
                                {unit}
                            </Typography>
                        </Typography>
                    )}
                </Box>
                <Box
                    sx={{
                        backgroundColor: 'rgba(255, 255, 255, 0.2)',
                        borderRadius: '12px',
                        p: 1.5,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Icon sx={{ fontSize: 40 }} />
                </Box>
            </Box>
        </CardContent>
    </Card>
);

// 섹션 타이틀 with 엑셀 다운로드 버튼
const SectionTitle = ({ icon: Icon, title, color, onDownload }) => (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Icon sx={{ fontSize: 28, color, mr: 1.5 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                {title}
            </Typography>
        </Box>
        {onDownload && (
            <IconButton
                onClick={onDownload}
                sx={{
                    backgroundColor: colors.success,
                    color: 'white',
                    '&:hover': { backgroundColor: colors.successLight },
                }}
                size="small"
            >
                <DownloadIcon />
            </IconButton>
        )}
    </Box>
);

// 날짜 포맷 함수
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 엑셀 다운로드 함수
const downloadExcel = (data, filename) => {
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    XLSX.writeFile(wb, `${filename}_${formatDate(new Date())}.xlsx`);
};

export default function ExGPTStatsPage() {
    // 날짜 범위 (기본값: 최근 30일)
    const getDefaultDateRange = () => ({
        start: formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
        end: formatDate(new Date()),
    });

    const defaultRange = getDefaultDateRange();
    const [dateRange, setDateRange] = useState(defaultRange);
    const [tempStartDate, setTempStartDate] = useState(dayjs(defaultRange.start));
    const [tempEndDate, setTempEndDate] = useState(dayjs(defaultRange.end));

    // 데이터 상태
    const [summary, setSummary] = useState(null);
    const [dailyStats, setDailyStats] = useState([]);
    const [errorReports, setErrorReports] = useState([]);
    const [documentsByCategory, setDocumentsByCategory] = useState(null);
    const [questionsByField, setQuestionsByField] = useState(null);

    // 그래프 토글 상태 (질문수/오류신고수)
    const [chartView, setChartView] = useState('both'); // 'both', 'questions', 'errors'

    // 로딩 상태
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // 데이터 로드
    const loadData = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const [summaryData, dailyData, errorData, docData, fieldData] = await Promise.all([
                getStatisticsSummary({ start_date: dateRange.start, end_date: dateRange.end }),
                getDailyStatistics(dateRange.start, dateRange.end),
                getErrorReportsDaily(dateRange.start, dateRange.end),
                getDocumentsByCategory(),
                getQuestionsByField({ start_date: dateRange.start, end_date: dateRange.end }),
            ]);

            setSummary(summaryData);
            setDailyStats(dailyData);
            setErrorReports(errorData);
            setDocumentsByCategory(docData);
            setQuestionsByField(fieldData);
        } catch (err) {
            console.error('통계 데이터 로드 실패:', err);
            setError(err.response?.data?.detail || '통계 데이터를 불러올 수 없습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    // 초기 로드
    useEffect(() => {
        loadData();
    }, [dateRange]);

    // 조회 버튼 핸들러
    const handleSearch = () => {
        setDateRange({
            start: tempStartDate.format('YYYY-MM-DD'),
            end: tempEndDate.format('YYYY-MM-DD'),
        });
    };

    // 초기화 버튼 핸들러
    const handleReset = () => {
        const defaultRange = getDefaultDateRange();
        setTempStartDate(dayjs(defaultRange.start));
        setTempEndDate(dayjs(defaultRange.end));
        setDateRange(defaultRange);
    };

    // 엑셀 다운로드 핸들러들
    const downloadSummary = () => {
        if (!summary) return;
        downloadExcel([summary], 'ex-GPT_요약통계');
    };

    const downloadDailyStats = () => {
        if (!dailyStats || dailyStats.length === 0) return;
        downloadExcel(dailyStats, 'ex-GPT_일별사용량');
    };

    const downloadCombinedChart = () => {
        // 질문수와 오류신고수를 하나의 데이터로 합침
        const combinedData = dailyStats.map(day => {
            const error = errorReports.find(e => e.date === day.date);
            return {
                날짜: day.date,
                질문수: day.count,
                오류신고수: error ? error.count : 0,
            };
        });
        downloadExcel(combinedData, 'ex-GPT_질문수_오류신고수');
    };

    const downloadDocumentStats = () => {
        if (!documentsByCategory) return;
        const data = [
            { 카테고리: '전체', 문서수: documentsByCategory.total },
            ...documentsByCategory.categories.map(cat => ({
                카테고리: cat.category_name,
                문서수: cat.document_count,
            })),
        ];
        downloadExcel(data, 'ex-GPT_문서등록현황');
    };

    const downloadFieldStats = () => {
        if (!questionsByField) return;
        const data = [
            { 분야: '전체', 질문수: questionsByField.total },
            { 분야: '경영분야 - 관리/홍보', 질문수: questionsByField.management?.subcategories?.admin_pr || 0 },
            { 분야: '경영분야 - 기획/감사', 질문수: questionsByField.management?.subcategories?.planning_audit || 0 },
            { 분야: '경영분야 - 영업/디지털', 질문수: questionsByField.management?.subcategories?.sales_digital || 0 },
            { 분야: '기술분야 - 도로/안전', 질문수: questionsByField.technical?.subcategories?.road_safety || 0 },
            { 분야: '기술분야 - 건설', 질문수: questionsByField.technical?.subcategories?.construction || 0 },
            { 분야: '기술분야 - 교통', 질문수: questionsByField.technical?.subcategories?.traffic || 0 },
            { 분야: '기술분야 - 신사업', 질문수: questionsByField.technical?.subcategories?.new_business || 0 },
            { 분야: '경영/기술 외 - 기타', 질문수: questionsByField.other?.total || 0 },
        ];
        downloadExcel(data, 'ex-GPT_분야별질문수');
    };

    // 통합 차트 데이터 준비
    const getCombinedChartData = () => {
        return dailyStats.map(day => {
            const error = errorReports.find(e => e.date === day.date);
            return {
                date: day.date,
                questions: day.count,
                errors: error ? error.count : 0,
            };
        });
    };

    // 파이 차트 데이터 준비
    const getPieChartData = () => {
        if (!questionsByField) return [];

        return [
            {
                name: '경영 - 관리/홍보',
                value: questionsByField.management?.subcategories?.admin_pr || 0,
                color: colors.primary,
            },
            {
                name: '경영 - 기획/감사',
                value: questionsByField.management?.subcategories?.planning_audit || 0,
                color: colors.primaryLight,
            },
            {
                name: '경영 - 영업/디지털',
                value: questionsByField.management?.subcategories?.sales_digital || 0,
                color: colors.info,
            },
            {
                name: '기술 - 도로/안전',
                value: questionsByField.technical?.subcategories?.road_safety || 0,
                color: colors.accent,
            },
            {
                name: '기술 - 건설',
                value: questionsByField.technical?.subcategories?.construction || 0,
                color: colors.accentLight,
            },
            {
                name: '기술 - 교통',
                value: questionsByField.technical?.subcategories?.traffic || 0,
                color: colors.success,
            },
            {
                name: '기술 - 신사업',
                value: questionsByField.technical?.subcategories?.new_business || 0,
                color: colors.successLight,
            },
            {
                name: '기타',
                value: questionsByField.other?.total || 0,
                color: colors.warning,
            },
        ].filter(item => item.value > 0);
    };

    if (error) {
        return (
            <Box sx={{ px: 0, py: 3 }}>
                <Paper sx={{ p: 3, backgroundColor: '#fee', color: '#c00' }}>
                    <Typography variant="h6">오류</Typography>
                    <Typography>{error}</Typography>
                </Paper>
            </Box>
        );
    }

    return (
        <Box sx={{ py: 0 }}>
            {/* 헤더 */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom sx={{ color: colors.primary, fontWeight: 'bold' }}>
                    ex-GPT 통계
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    AI 서비스 사용 현황 및 분석
                </Typography>
            </Box>

            {/* 기간 조회 (조회/초기화 버튼 추가) */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                    <CalendarIcon sx={{ color: colors.primary }} />
                    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ko">
                        <DatePicker
                            label="시작 날짜"
                            value={tempStartDate}
                            onChange={(newValue) => setTempStartDate(newValue)}
                            slotProps={{
                                textField: {
                                    size: 'small',
                                    sx: { minWidth: 160 }
                                }
                            }}
                        />
                        <Typography variant="body2" color="text.secondary">~</Typography>
                        <DatePicker
                            label="종료 날짜"
                            value={tempEndDate}
                            onChange={(newValue) => setTempEndDate(newValue)}
                            slotProps={{
                                textField: {
                                    size: 'small',
                                    sx: { minWidth: 160 }
                                }
                            }}
                        />
                    </LocalizationProvider>
                    <Button
                        variant="contained"
                        startIcon={<SearchIcon />}
                        onClick={handleSearch}
                        sx={{ backgroundColor: colors.primary, '&:hover': { backgroundColor: colors.primaryLight } }}
                    >
                        조회
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={handleReset}
                        sx={{ borderColor: colors.primary, color: colors.primary }}
                    >
                        초기화
                    </Button>
                </Box>
            </Paper>

            {/* 요약 카드 - 일일방문자수 */}
            <Box sx={{ mb: 3 }}>
                <SectionTitle
                    icon={TrendingUpIcon}
                    title="일일방문자수"
                    color={colors.primary}
                    onDownload={downloadSummary}
                />
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                        <GradientStatCard
                            title="총 질문 수"
                            value={summary?.total_questions?.toLocaleString() || 0}
                            unit=""
                            icon={QuestionAnswerIcon}
                            gradient={[colors.primary, colors.primaryLight]}
                            loading={isLoading}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <GradientStatCard
                            title="평균 응답 시간"
                            value={summary?.average_response_time?.toFixed(0) || 0}
                            unit="ms"
                            icon={SpeedIcon}
                            gradient={[colors.accent, colors.accentLight]}
                            loading={isLoading}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <GradientStatCard
                            title="사용자 수"
                            value={summary?.unique_users?.toLocaleString() || 0}
                            unit="명"
                            icon={PeopleIcon}
                            gradient={[colors.success, colors.successLight]}
                            loading={isLoading}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <GradientStatCard
                            title="일평균 사용량"
                            value={summary?.daily_average?.toFixed(1) || 0}
                            unit=""
                            icon={TrendingUpIcon}
                            gradient={[colors.info, colors.infoLight]}
                            loading={isLoading}
                        />
                    </Grid>
                </Grid>
            </Box>

            {/* 일별 사용량 */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <SectionTitle
                    icon={CalendarIcon}
                    title="일별 사용량"
                    color={colors.primary}
                    onDownload={downloadDailyStats}
                />
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                        <CircularProgress />
                    </Box>
                ) : dailyStats.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                        <AreaChart data={dailyStats}>
                            <defs>
                                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={colors.primary} stopOpacity={0.8} />
                                    <stop offset="95%" stopColor={colors.primary} stopOpacity={0.1} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} stroke="#cbd5e1" />
                            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} stroke="#cbd5e1" />
                            <Tooltip contentStyle={{ backgroundColor: 'white', border: 'none', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                            <Legend />
                            <Area type="monotone" dataKey="count" stroke={colors.primary} strokeWidth={3} fill="url(#colorCount)" name="질문 수" />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <Typography variant="body2" color="text.secondary" align="center">
                        데이터가 없습니다.
                    </Typography>
                )}
            </Paper>

            {/* 질문수 발생추이 및 오류신고수 그래프 (통합, 토글) */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <QuestionAnswerIcon sx={{ fontSize: 28, color: colors.primary, mr: 1.5 }} />
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                            질문수 발생추이 / 오류신고수
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                        <ToggleButtonGroup
                            value={chartView}
                            exclusive
                            onChange={(e, newView) => newView && setChartView(newView)}
                            size="small"
                        >
                            <ToggleButton value="both">전체</ToggleButton>
                            <ToggleButton value="questions">질문수</ToggleButton>
                            <ToggleButton value="errors">오류신고수</ToggleButton>
                        </ToggleButtonGroup>
                        <IconButton
                            onClick={downloadCombinedChart}
                            sx={{ backgroundColor: colors.success, color: 'white', '&:hover': { backgroundColor: colors.successLight } }}
                            size="small"
                        >
                            <DownloadIcon />
                        </IconButton>
                    </Box>
                </Box>
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                        <CircularProgress />
                    </Box>
                ) : (
                    <ResponsiveContainer width="100%" height={350}>
                        <LineChart data={getCombinedChartData()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} stroke="#cbd5e1" />
                            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} stroke="#cbd5e1" />
                            <Tooltip contentStyle={{ backgroundColor: 'white', border: 'none', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                            <Legend />
                            {(chartView === 'both' || chartView === 'questions') && (
                                <Line type="monotone" dataKey="questions" stroke={colors.primary} strokeWidth={3} name="질문 수" dot={{ r: 4 }} />
                            )}
                            {(chartView === 'both' || chartView === 'errors') && (
                                <Line type="monotone" dataKey="errors" stroke={colors.error} strokeWidth={3} name="오류신고 수" dot={{ r: 4 }} />
                            )}
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </Paper>

            {/* 문서 등록현황 */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <SectionTitle
                    icon={DescriptionIcon}
                    title="문서 등록현황"
                    color={colors.success}
                    onDownload={downloadDocumentStats}
                />
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                        <CircularProgress />
                    </Box>
                ) : documentsByCategory ? (
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card sx={{ backgroundColor: colors.primary, color: 'white' }}>
                                <CardContent>
                                    <Typography variant="h6">전체</Typography>
                                    <Typography variant="h4">{documentsByCategory.total?.toLocaleString()}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                        {documentsByCategory.categories?.map((cat, idx) => (
                            <Grid item xs={12} sm={6} md={3} key={cat.category_id}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="body2" color="text.secondary">{cat.category_name}</Typography>
                                        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{cat.document_count.toLocaleString()}</Typography>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                ) : (
                    <Typography variant="body2" color="text.secondary" align="center">
                        데이터가 없습니다.
                    </Typography>
                )}
            </Paper>

            {/* 카테고리별 자동분류 */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <SectionTitle
                    icon={CategoryIcon}
                    title="카테고리별 자동분류"
                    color={colors.accent}
                    onDownload={downloadFieldStats}
                />
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                        <CircularProgress />
                    </Box>
                ) : questionsByField ? (
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card sx={{ backgroundColor: colors.primary, color: 'white' }}>
                                <CardContent>
                                    <Typography variant="h6">전체</Typography>
                                    <Typography variant="h4">{questionsByField.total?.toLocaleString()}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card sx={{ backgroundColor: colors.info, color: 'white' }}>
                                <CardContent>
                                    <Typography variant="h6">경영분야</Typography>
                                    <Typography variant="h4">{questionsByField.management?.total?.toLocaleString()}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card sx={{ backgroundColor: colors.accent, color: 'white' }}>
                                <CardContent>
                                    <Typography variant="h6">기술분야</Typography>
                                    <Typography variant="h4">{questionsByField.technical?.total?.toLocaleString()}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Card sx={{ backgroundColor: colors.warning, color: 'white' }}>
                                <CardContent>
                                    <Typography variant="h6">경영/기술 외</Typography>
                                    <Typography variant="h4">{questionsByField.other?.total?.toLocaleString()}</Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    </Grid>
                ) : (
                    <Typography variant="body2" color="text.secondary" align="center">
                        데이터가 없습니다.
                    </Typography>
                )}
            </Paper>

            {/* 분야별 질문수 원 그래프 */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 2, boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)' }}>
                <SectionTitle
                    icon={PieChartIcon}
                    title="분야별 질문수 분포"
                    color={colors.success}
                    onDownload={downloadFieldStats}
                />
                {isLoading ? (
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                        <CircularProgress />
                    </Box>
                ) : getPieChartData().length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                        <PieChart>
                            <Pie
                                data={getPieChartData()}
                                cx="50%"
                                cy="50%"
                                labelLine={true}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={120}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {getPieChartData().map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                ) : (
                    <Typography variant="body2" color="text.secondary" align="center">
                        데이터가 없습니다.
                    </Typography>
                )}
            </Paper>
        </Box>
    );
}
