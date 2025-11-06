/**
 * 통계 대시보드 - CoreUI 스타일 적용
 * 한국도로공사 브랜드 컬러 + 그라데이션 디자인
 * TDD 기반 실시간 통계 + 시각화
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, Box, Grid, Typography, CircularProgress, Paper, Tabs, Tab } from '@mui/material';
import { Title } from 'react-admin';
import {
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
    QuestionAnswer as QuestionAnswerIcon,
    People as PeopleIcon,
    Star as StarIcon,
    Description as DescriptionIcon,
    Speed as SpeedIcon,
    ArrowUpward as ArrowUpwardIcon,
} from '@mui/icons-material';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, Area, AreaChart, PieChart, Pie, Cell
} from 'recharts';

// 한국도로공사 브랜드 컬러 + 그라데이션
const colors = {
    primary: '#0a2986',
    primaryLight: '#1e3a8a',
    accent: '#e64701',
    accentLight: '#f97316',
    success: '#10b981',
    successLight: '#34d399',
    info: '#3b82f6',
    infoLight: '#60a5fa',
    warning: '#f59e0b',
    warningLight: '#fbbf24',
};

// CoreUI 스타일의 그라데이션 카드
const GradientStatCard = ({ title, value, icon: Icon, gradient, trend, trendValue, loading }) => (
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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ opacity: 0.9, mb: 1, fontWeight: 500 }}>
                        {title}
                    </Typography>
                    {loading ? (
                        <CircularProgress size={32} sx={{ color: 'white' }} />
                    ) : (
                        <>
                            <Typography variant="h3" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                                {value}
                            </Typography>
                            {trend && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    {trend === 'up' ? (
                                        <ArrowUpwardIcon sx={{ fontSize: 16 }} />
                                    ) : (
                                        <TrendingDownIcon sx={{ fontSize: 16 }} />
                                    )}
                                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                                        {trendValue} vs 지난주
                                    </Typography>
                                </Box>
                            )}
                        </>
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
                        backdropFilter: 'blur(10px)',
                    }}
                >
                    <Icon sx={{ fontSize: 40 }} />
                </Box>
            </Box>
        </CardContent>
    </Card>
);

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [systemInfo, setSystemInfo] = useState(null);
    const [dailyTrend, setDailyTrend] = useState([]);
    const [hourlyPattern, setHourlyPattern] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [periodTab, setPeriodTab] = useState(0); // 0: 일별, 1: 주별, 2: 월별
    const [weeklyData, setWeeklyData] = useState([]);
    const [monthlyData, setMonthlyData] = useState([]);
    // 배포 관련 상태
    const [gpuStatus, setGpuStatus] = useState(null);
    const [services, setServices] = useState([]);
    const [containers, setContainers] = useState([]);
    // 부서별/분야별 통계
    const [departmentStats, setDepartmentStats] = useState([]);
    const [categoryStats, setCategoryStats] = useState([]);

    useEffect(() => {
        fetchDashboardStats();
    }, []);

    const fetchDashboardStats = async () => {
        try {
            setLoading(true);

            const end = new Date().toISOString().split('T')[0];
            const start = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const weekStart = new Date(Date.now() - 8 * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const monthStart = new Date(Date.now() - 6 * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const today = new Date().toISOString().split('T')[0];
            // 부서별/분야별 통계는 30일 데이터 사용
            const statsStart = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

            const headers = {
                'Accept': 'application/json',
                'X-Test-Auth': 'admin'
            };

            const [dashboardRes, dailyRes, weeklyRes, monthlyRes, hourlyRes, systemRes, gpuRes, servicesRes, containersRes, deptRes, catRes] = await Promise.all([
                fetch(`/api/v1/admin/stats/dashboard?start=${start}&end=${end}`, { headers }),
                fetch(`/api/v1/admin/stats/daily-trend?start=${start}&end=${end}`, { headers }),
                fetch(`/api/v1/admin/stats/weekly-trend?start=${weekStart}&end=${end}`, { headers }),
                fetch(`/api/v1/admin/stats/monthly-trend?start=${monthStart}&end=${end}`, { headers }),
                fetch(`/api/v1/admin/stats/hourly-pattern?date=${today}`, { headers }),
                fetch(`/api/v1/admin/stats/system`, { headers }),
                fetch(`/api/v1/admin/deployment/gpu/status`, { headers }),
                fetch(`/api/v1/admin/deployment/bentos`, { headers }),
                fetch(`/api/v1/admin/deployment/docker/containers`, { headers }),
                fetch(`/api/v1/admin/stats/by-department?start=${statsStart}&end=${end}`, { headers }),
                fetch(`/api/v1/admin/stats/by-category?start=${statsStart}&end=${end}`, { headers })
            ]);

            if (!dashboardRes.ok || !dailyRes.ok || !hourlyRes.ok || !systemRes.ok) {
                throw new Error('Failed to fetch statistics');
            }

            const dashboardData = await dashboardRes.json();
            const dailyData = await dailyRes.json();
            const weeklyDataRes = weeklyRes.ok ? await weeklyRes.json() : { items: [] };
            const monthlyDataRes = monthlyRes.ok ? await monthlyRes.json() : { items: [] };
            const hourlyData = await hourlyRes.json();
            const systemData = await systemRes.json();
            const gpuData = gpuRes.ok ? await gpuRes.json() : { gpus: [] };
            const servicesData = servicesRes.ok ? await servicesRes.json() : { bentos: [] };
            const containersData = containersRes.ok ? await containersRes.json() : { containers: [] };
            const deptData = deptRes.ok ? await deptRes.json() : { items: [] };
            const catData = catRes.ok ? await catRes.json() : { categories: [] };

            setStats(dashboardData);
            setDailyTrend(dailyData.items || []);
            setWeeklyData(weeklyDataRes.items || []);
            setMonthlyData(monthlyDataRes.items || []);
            setHourlyPattern(hourlyData.items || []);
            setSystemInfo(systemData);
            setGpuStatus(gpuData);
            setServices(servicesData.bentos || []);
            setContainers(containersData.containers || []);
            setDepartmentStats(deptData.items || []);
            setCategoryStats(catData.categories || []);
        } catch (err) {
            console.error('Failed to fetch dashboard stats:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num) => {
        if (num === null || num === undefined) return '0';
        return num.toLocaleString('ko-KR');
    };

    const formatTime = (ms) => {
        if (!ms) return '0ms';
        if (ms < 1000) return `${Math.round(ms)}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatRating = (rating) => {
        if (!rating) return '0.0';
        return rating.toFixed(1);
    };

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Title title="통계 대시보드" />
                <Card>
                    <CardContent>
                        <Typography color="error">
                            통계를 불러오는데 실패했습니다: {error}
                        </Typography>
                    </CardContent>
                </Card>
            </Box>
        );
    }

    return (
        <Box sx={{
            py: 0,
            px: 0,
            m: 0,
            maxWidth: 'none !important',
            width: '100% !important',
            boxSizing: 'border-box',
            '& *': {
                boxSizing: 'border-box',
            },
            '& .MuiContainer-root, & .MuiContainer-maxWidthLg, & .MuiContainer-maxWidthMd, & .MuiContainer-maxWidthSm': {
                maxWidth: 'none !important',
                width: '100% !important',
                padding: '0 !important',
                margin: '0 !important',
            }
        }}>
            <Title title="통계 대시보드" />

            {/* 상단 타이틀 */}
            <Box sx={{ mb: 4 }}>
                <Typography
                    variant="h4"
                    component="h1"
                    gutterBottom
                    sx={{
                        color: colors.primary,
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                    }}
                >
                    통계 대시보드
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    최근 7일간의 ex-GPT 사용 통계 및 시스템 현황
                </Typography>
            </Box>

            {/* 주요 지표 카드 - 그라데이션 */}
            <Paper
                elevation={0}
                sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: 'transparent',
                    border: 'none',
                    maxWidth: 'none !important',
                    width: '100% !important',
                }}
            >
            <Grid container spacing={2} sx={{ maxWidth: 'none !important', width: '100% !important' }}>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="총 질문 수"
                        value={formatNumber(stats?.total_questions)}
                        icon={QuestionAnswerIcon}
                        gradient={[colors.primary, colors.primaryLight]}
                        trend="up"
                        trendValue="+12%"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="총 사용자 수"
                        value={formatNumber(stats?.total_users)}
                        icon={PeopleIcon}
                        gradient={[colors.success, colors.successLight]}
                        trend="up"
                        trendValue="+8%"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="평균 응답 시간"
                        value={formatTime(stats?.average_response_time)}
                        icon={SpeedIcon}
                        gradient={[colors.info, colors.infoLight]}
                        trend="down"
                        trendValue="-5%"
                        loading={loading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="평균 만족도"
                        value={`${formatRating(stats?.average_satisfaction)} / 5.0`}
                        icon={StarIcon}
                        gradient={[colors.accent, colors.accentLight]}
                        trend="up"
                        trendValue="+3%"
                        loading={loading}
                    />
                </Grid>
            </Grid>
            </Paper>

            {/* 배포 현황 통계 */}
            <Paper
                elevation={0}
                sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: 'white',
                    borderRadius: 2,
                    boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                    maxWidth: 'none !important',
                    width: '100% !important',
                }}
            >
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    🚀 배포 현황
                </Typography>

                <Grid container spacing={2} sx={{ maxWidth: 'none !important', width: '100% !important' }}>
                    {/* vLLM 서비스 */}
                    <Grid item xs={12} md={3}>
                        <Box sx={{ p: 2, borderRadius: 2, backgroundColor: '#f8fafc', border: `2px solid ${colors.primary}` }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: colors.primary, mb: 2 }}>
                                💬 vLLM 서비스 ({services.filter(s => s.status === 'serving').length}/{services.length})
                            </Typography>
                            {services.length > 0 ? (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                    {services.map((service, idx) => (
                                        <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
                                            <Typography variant="body2">{service.model}</Typography>
                                            <Box sx={{
                                                px: 1.5,
                                                py: 0.5,
                                                borderRadius: 1,
                                                backgroundColor: service.status === 'serving' ? '#dcfce7' : '#fee2e2',
                                                color: service.status === 'serving' ? '#16a34a' : '#dc2626',
                                                fontWeight: 'bold',
                                                fontSize: '0.75rem'
                                            }}>
                                                {service.status === 'serving' ? '● 실행중' : '○ 중지'}
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            ) : (
                                <Typography variant="body2" color="text.secondary">서비스 없음</Typography>
                            )}
                        </Box>
                    </Grid>

                    {/* Docker 컨테이너 */}
                    <Grid item xs={12} md={3}>
                        <Box sx={{ p: 2, borderRadius: 2, backgroundColor: '#f8fafc', border: `2px solid ${colors.success}` }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: colors.success, mb: 2 }}>
                                🐳 Docker 컨테이너 ({containers.filter(c => c.state === 'running').length}/{containers.length})
                            </Typography>
                            {containers.length > 0 ? (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: '200px', overflowY: 'auto' }}>
                                    {containers.slice(0, 6).map((container, idx) => (
                                        <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
                                            <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '70%' }}>
                                                {container.name}
                                            </Typography>
                                            <Box sx={{
                                                px: 1.5,
                                                py: 0.5,
                                                borderRadius: 1,
                                                backgroundColor: container.state === 'running' ? '#dcfce7' : '#fee2e2',
                                                color: container.state === 'running' ? '#16a34a' : '#dc2626',
                                                fontWeight: 'bold',
                                                fontSize: '0.75rem'
                                            }}>
                                                {container.state === 'running' ? '● RUN' : '○ STOP'}
                                            </Box>
                                        </Box>
                                    ))}
                                    {containers.length > 6 && (
                                        <Typography variant="caption" color="text.secondary">+ {containers.length - 6}개 더</Typography>
                                    )}
                                </Box>
                            ) : (
                                <Typography variant="body2" color="text.secondary">컨테이너 없음</Typography>
                            )}
                        </Box>
                    </Grid>

                    {/* GPU 현황 */}
                    <Grid item xs={12} md={3}>
                        <Box sx={{ p: 2, borderRadius: 2, backgroundColor: '#f8fafc', border: `2px solid ${colors.accent}` }}>
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: colors.accent, mb: 2 }}>
                                ⚡ GPU 현황 ({gpuStatus?.gpus?.filter(gpu => gpu.utilization > 10).length || 0}/{gpuStatus?.gpus?.length || 0} 활성)
                            </Typography>
                            {gpuStatus?.gpus?.length > 0 ? (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                    {gpuStatus.gpus.map((gpu, idx) => (
                                        <Box key={idx}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>GPU {gpu.id}</Typography>
                                                <Typography variant="body2" sx={{ fontWeight: 'bold', color: colors.accent }}>{gpu.utilization}%</Typography>
                                            </Box>
                                            <Box sx={{
                                                height: 8,
                                                backgroundColor: '#e5e7eb',
                                                borderRadius: 1,
                                                overflow: 'hidden'
                                            }}>
                                                <Box sx={{
                                                    height: '100%',
                                                    width: `${gpu.utilization}%`,
                                                    backgroundColor: gpu.utilization >= 90 ? '#ff4d4f' : gpu.utilization >= 70 ? '#faad14' : gpu.utilization >= 50 ? '#52c41a' : '#1890ff',
                                                    transition: 'width 0.5s ease'
                                                }} />
                                            </Box>
                                        </Box>
                                    ))}
                                </Box>
                            ) : (
                                <Typography variant="body2" color="text.secondary">GPU 정보 없음</Typography>
                            )}
                        </Box>
                    </Grid>
                </Grid>
            </Paper>

            {/* 시스템 정보 & 빠른 링크 */}
            <Paper
                elevation={0}
                sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: 'white',
                    borderRadius: 2,
                    boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                    maxWidth: 'none !important',
                    width: '100% !important',
                }}
            >
            <Grid container spacing={2} sx={{ maxWidth: 'none !important', width: '100% !important' }}>
                <Grid item xs={12} md={6}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2,
                            borderRadius: 2,
                            boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                            height: '100%',
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <DescriptionIcon sx={{ fontSize: 28, color: colors.primary, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                시스템 정보
                            </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    p: 2,
                                    backgroundColor: '#f8fafc',
                                    borderRadius: 2,
                                    borderLeft: `4px solid ${colors.primary}`,
                                }}
                            >
                                <Box>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        원본 문서 수
                                    </Typography>
                                    {loading ? (
                                        <CircularProgress size={20} />
                                    ) : (
                                        <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                            {formatNumber(systemInfo?.unique_documents || 0)}
                                        </Typography>
                                    )}
                                </Box>
                                <DescriptionIcon sx={{ fontSize: 40, color: colors.primary, opacity: 0.3 }} />
                            </Box>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    p: 2,
                                    backgroundColor: '#f8fafc',
                                    borderRadius: 2,
                                    borderLeft: `4px solid ${colors.info}`,
                                }}
                            >
                                <Box>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        벡터화된 청크 수
                                    </Typography>
                                    {loading ? (
                                        <CircularProgress size={20} />
                                    ) : (
                                        <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.info }}>
                                            {formatNumber(systemInfo?.vector_chunks || 0)}
                                        </Typography>
                                    )}
                                </Box>
                                <DescriptionIcon sx={{ fontSize: 40, color: colors.info, opacity: 0.3 }} />
                            </Box>
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    p: 2,
                                    backgroundColor: '#f8fafc',
                                    borderRadius: 2,
                                    borderLeft: `4px solid ${colors.success}`,
                                }}
                            >
                                <Box>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        총 공지사항 수
                                    </Typography>
                                    {loading ? (
                                        <CircularProgress size={20} />
                                    ) : (
                                        <Typography variant="h5" sx={{ fontWeight: 'bold', color: colors.success }}>
                                            {formatNumber(systemInfo?.total_notices || 0)}
                                        </Typography>
                                    )}
                                </Box>
                                <QuestionAnswerIcon sx={{ fontSize: 40, color: colors.success, opacity: 0.3 }} />
                            </Box>
                        </Box>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 2,
                            borderRadius: 2,
                            boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                            height: '100%',
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <TrendingUpIcon sx={{ fontSize: 28, color: colors.accent, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                빠른 링크
                            </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Box
                                component="a"
                                href="https://ui.datastreams.co.kr:20443/admin/#/conversations"
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    p: 2,
                                    borderRadius: 2,
                                    textDecoration: 'none',
                                    color: 'inherit',
                                    backgroundColor: '#f8fafc',
                                    border: '1px solid #e2e8f0',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        backgroundColor: colors.primary,
                                        borderColor: colors.primary,
                                        color: 'white',
                                        transform: 'translateX(8px)',
                                        boxShadow: '0 4px 12px rgba(10, 41, 134, 0.2)',
                                    },
                                }}
                            >
                                <QuestionAnswerIcon sx={{ mr: 2, fontSize: 24 }} />
                                <Typography sx={{ fontWeight: 500 }}>대화내역 조회</Typography>
                            </Box>
                            <Box
                                component="a"
                                href="https://ui.datastreams.co.kr:20443/admin/#/notices"
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    p: 2,
                                    borderRadius: 2,
                                    textDecoration: 'none',
                                    color: 'inherit',
                                    backgroundColor: '#f8fafc',
                                    border: '1px solid #e2e8f0',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        backgroundColor: colors.primary,
                                        borderColor: colors.primary,
                                        color: 'white',
                                        transform: 'translateX(8px)',
                                        boxShadow: '0 4px 12px rgba(10, 41, 134, 0.2)',
                                    },
                                }}
                            >
                                <DescriptionIcon sx={{ mr: 2, fontSize: 24 }} />
                                <Typography sx={{ fontWeight: 500 }}>공지사항 관리</Typography>
                            </Box>
                            <Box
                                component="a"
                                href="https://ui.datastreams.co.kr:20443/admin/#/satisfaction"
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    p: 2,
                                    borderRadius: 2,
                                    textDecoration: 'none',
                                    color: 'inherit',
                                    backgroundColor: '#f8fafc',
                                    border: '1px solid #e2e8f0',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        backgroundColor: colors.primary,
                                        borderColor: colors.primary,
                                        color: 'white',
                                        transform: 'translateX(8px)',
                                        boxShadow: '0 4px 12px rgba(10, 41, 134, 0.2)',
                                    },
                                }}
                            >
                                <StarIcon sx={{ mr: 2, fontSize: 24 }} />
                                <Typography sx={{ fontWeight: 500 }}>만족도 조사 결과</Typography>
                            </Box>
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
            </Paper>

            {/* 차트 시각화 섹션 - 전체 너비 사용 */}
            <Box sx={{ width: '100%', maxWidth: 'none !important' }}>
                {/* 사용 추이 - Area Chart with Tabs */}
                <Paper
                    elevation={0}
                    sx={{
                        p: 2,
                        mb: 3,
                        borderRadius: 2,
                        boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        width: '100% !important',
                        maxWidth: 'none !important',
                    }}
                >
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <TrendingUpIcon sx={{ fontSize: 28, color: colors.primary, mr: 1.5 }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                    사용 추이
                                </Typography>
                            </Box>
                            <Tabs
                                value={periodTab}
                                onChange={(e, v) => setPeriodTab(v)}
                                sx={{
                                    minHeight: 36,
                                    '& .MuiTab-root': {
                                        minHeight: 36,
                                        minWidth: 70,
                                        fontSize: '0.875rem',
                                        fontWeight: 500,
                                    },
                                }}
                            >
                                <Tab label="일별" />
                                <Tab label="주별" />
                                <Tab label="월별" />
                            </Tabs>
                        </Box>
                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                <CircularProgress />
                            </Box>
                        ) : (
                            (() => {
                                const data = periodTab === 0 ? dailyTrend : periodTab === 1 ? weeklyData : monthlyData;
                                const dateKey = periodTab === 0 ? 'date' : periodTab === 1 ? 'week' : 'month';

                                return data.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={450}>
                                        <AreaChart data={data}>
                                            <defs>
                                                <linearGradient id="colorQuestions" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={colors.primary} stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor={colors.primary} stopOpacity={0.1} />
                                                </linearGradient>
                                                <linearGradient id="colorResponseTime" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={colors.accent} stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor={colors.accent} stopOpacity={0.1} />
                                                </linearGradient>
                                                <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={colors.success} stopOpacity={0.8} />
                                                    <stop offset="95%" stopColor={colors.success} stopOpacity={0.1} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                            <XAxis
                                                dataKey={dateKey}
                                                tick={{ fontSize: 12, fill: '#64748b' }}
                                                stroke="#cbd5e1"
                                            />
                                            <YAxis
                                                yAxisId="left"
                                                tick={{ fontSize: 12, fill: '#64748b' }}
                                                stroke="#cbd5e1"
                                            />
                                            <YAxis
                                                yAxisId="right"
                                                orientation="right"
                                                tick={{ fontSize: 12, fill: '#64748b' }}
                                                stroke="#cbd5e1"
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'white',
                                                    border: 'none',
                                                    borderRadius: '8px',
                                                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                                }}
                                            />
                                            <Legend />
                                            <Area
                                                yAxisId="left"
                                                type="monotone"
                                                dataKey="question_count"
                                                stroke={colors.primary}
                                                strokeWidth={3}
                                                fill="url(#colorQuestions)"
                                                name="질문 수"
                                            />
                                            <Area
                                                yAxisId="left"
                                                type="monotone"
                                                dataKey="unique_users"
                                                stroke={colors.success}
                                                strokeWidth={3}
                                                fill="url(#colorUsers)"
                                                name="사용자 수"
                                            />
                                            <Area
                                                yAxisId="right"
                                                type="monotone"
                                                dataKey="avg_response_time"
                                                stroke={colors.accent}
                                                strokeWidth={3}
                                                fill="url(#colorResponseTime)"
                                                name="평균 응답시간 (ms)"
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                                        데이터가 없습니다
                                    </Typography>
                                );
                            })()
                        )}
                </Paper>

                {/* 시간대별 사용 패턴 - Bar Chart */}
                <Paper
                    elevation={0}
                    sx={{
                        p: 2,
                        borderRadius: 2,
                        boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        width: '100% !important',
                        maxWidth: 'none !important',
                    }}
                >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <SpeedIcon sx={{ fontSize: 28, color: colors.info, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                시간대별 사용 패턴 (오늘)
                            </Typography>
                        </Box>
                        {loading ? (
                            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                                <CircularProgress />
                            </Box>
                        ) : hourlyPattern.length > 0 ? (
                            <ResponsiveContainer width="100%" height={450}>
                                <BarChart data={hourlyPattern}>
                                    <defs>
                                        <linearGradient id="colorBar" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={colors.info} stopOpacity={1} />
                                            <stop offset="100%" stopColor={colors.infoLight} stopOpacity={0.8} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                    />
                                    <YAxis
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'white',
                                            border: 'none',
                                            borderRadius: '8px',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                        }}
                                    />
                                    <Bar
                                        dataKey="question_count"
                                        fill="url(#colorBar)"
                                        name="질문 수"
                                        radius={[8, 8, 0, 0]}
                                    />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                                데이터가 없습니다
                            </Typography>
                        )}
                </Paper>

                {/* 부서별 이용 통계 (방문자 현황) - Bar Chart */}
                <Paper
                    elevation={0}
                    sx={{
                        p: 2,
                        mt: 3,
                        borderRadius: 2,
                        boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        width: '100% !important',
                        maxWidth: 'none !important',
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <PeopleIcon sx={{ fontSize: 28, color: colors.success, mr: 1.5 }} />
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                            방문자 현황 (부서별 이용 통계 - 최근 30일)
                        </Typography>
                    </Box>
                    {loading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : departmentStats.length > 0 ? (
                        <ResponsiveContainer width="100%" height={450}>
                            <BarChart data={departmentStats}>
                                <defs>
                                    <linearGradient id="colorDept" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor={colors.success} stopOpacity={1} />
                                        <stop offset="100%" stopColor={colors.successLight} stopOpacity={0.8} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis
                                    dataKey="team"
                                    tick={{ fontSize: 11, fill: '#64748b' }}
                                    stroke="#cbd5e1"
                                    angle={-15}
                                    textAnchor="end"
                                    height={80}
                                />
                                <YAxis
                                    tick={{ fontSize: 12, fill: '#64748b' }}
                                    stroke="#cbd5e1"
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'white',
                                        border: 'none',
                                        borderRadius: '8px',
                                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                    }}
                                />
                                <Legend />
                                <Bar
                                    dataKey="question_count"
                                    fill="url(#colorDept)"
                                    name="질문 수"
                                    radius={[8, 8, 0, 0]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                            데이터가 없습니다
                        </Typography>
                    )}
                </Paper>

                {/* 분야별 질의 통계 (활용 현황) - 카드 형식 */}
                <Paper
                    elevation={0}
                    sx={{
                        p: 2,
                        mt: 3,
                        borderRadius: 2,
                        boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        width: '100% !important',
                        maxWidth: 'none !important',
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <QuestionAnswerIcon sx={{ fontSize: 28, color: colors.accent, mr: 1.5 }} />
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                            활용 현황 (분야별 질의 통계 - 최근 30일)
                        </Typography>
                    </Box>
                    {loading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : categoryStats.length > 0 ? (
                        <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
                            {categoryStats
                                .sort((a, b) => {
                                    // 미분류를 맨 마지막으로
                                    if (a.main_category === '미분류') return 1;
                                    if (b.main_category === '미분류') return -1;
                                    return b.total_count - a.total_count;
                                })
                                .map((category, index) => {
                                    const cardColors = [
                                        { bg: '#f0f9ff', border: colors.primary, text: colors.primary },
                                        { bg: '#fff7ed', border: colors.accent, text: colors.accent },
                                        { bg: '#f0fdf4', border: colors.success, text: colors.success },
                                        { bg: '#fef2f2', border: '#ef4444', text: '#ef4444' }
                                    ];
                                    const cardColor = cardColors[index % cardColors.length];

                                    return (
                                        <Paper
                                            key={index}
                                            elevation={0}
                                            sx={{
                                                p: 2.5,
                                                borderRadius: 2,
                                                backgroundColor: cardColor.bg,
                                                border: `2px solid ${cardColor.border}`,
                                                flex: '1 1 0',
                                                minWidth: 0,
                                                minHeight: 200,
                                                display: 'flex',
                                                flexDirection: 'column',
                                            }}
                                        >
                                            <Typography
                                                variant="h6"
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: cardColor.text,
                                                    mb: 1,
                                                    fontSize: '1.1rem'
                                                }}
                                            >
                                                {category.main_category}
                                            </Typography>
                                            <Typography
                                                variant="h4"
                                                sx={{
                                                    fontWeight: 'bold',
                                                    color: cardColor.text,
                                                    mb: 2
                                                }}
                                            >
                                                {formatNumber(category.total_count)}건
                                            </Typography>

                                            {category.sub_items.length > 0 && (
                                                <Box sx={{ mt: 2, pt: 2, borderTop: `1px solid ${cardColor.border}40` }}>
                                                    <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 'bold', mb: 1, display: 'block' }}>
                                                        세부 항목
                                                    </Typography>
                                                    {category.sub_items.map((item, idx) => (
                                                        <Box
                                                            key={idx}
                                                            sx={{
                                                                display: 'flex',
                                                                justifyContent: 'space-between',
                                                                alignItems: 'center',
                                                                py: 0.5,
                                                                fontSize: '0.875rem'
                                                            }}
                                                        >
                                                            <Typography variant="body2" sx={{ color: '#475569' }}>
                                                                • {item.sub_category}
                                                            </Typography>
                                                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: cardColor.text }}>
                                                                {formatNumber(item.count)}
                                                            </Typography>
                                                        </Box>
                                                    ))}
                                                </Box>
                                            )}
                                        </Paper>
                                    );
                                })}
                        </Box>
                    ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                            데이터가 없습니다
                        </Typography>
                    )}
                </Paper>
            </Box>
        </Box>
    );
};

export default Dashboard;
