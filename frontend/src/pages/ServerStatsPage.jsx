/**
 * 서버 현황 통계 페이지 - CoreUI 스타일
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid, Box, CircularProgress, Paper } from '@mui/material';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
    Memory as MemoryIcon,
    Storage as StorageIcon,
    Computer as ComputerIcon,
    CheckCircle as CheckCircleIcon,
    ArrowUpward as ArrowUpwardIcon,
    Refresh as RefreshIcon,
} from '@mui/icons-material';
import {
    getServerSummary,
    getHistoricalCpuUsage,
    getHistoricalMemoryUsage,
    getDiskUsage,
    getGpuUsage,
    getDockerInfo,
} from '../utils/api';

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
    warning: '#f59e0b',
    warningLight: '#fbbf24',
};

// CoreUI 스타일 그라데이션 카드
const GradientStatCard = ({ title, value, unit, icon: Icon, gradient, trend, trendValue, loading }) => (
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
                                <Typography component="span" variant="h6" sx={{ ml: 0.5, opacity: 0.9 }}>
                                    {unit}
                                </Typography>
                            </Typography>
                            {trend && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <ArrowUpwardIcon sx={{ fontSize: 16 }} />
                                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                                        {trendValue} vs 어제
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

export default function ServerStatsPage() {
    const [summary, setSummary] = useState(null);
    const [cpuUsage, setCpuUsage] = useState([]);
    const [memoryUsage, setMemoryUsage] = useState([]);
    const [diskUsage, setDiskUsage] = useState([]);
    const [gpuData, setGpuData] = useState(null);
    const [dockerData, setDockerData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [summaryData, cpuData, memoryData, diskData, gpu, docker] = await Promise.all([
                getServerSummary(),
                getHistoricalCpuUsage(),
                getHistoricalMemoryUsage(),
                getDiskUsage(),
                getGpuUsage(),
                getDockerInfo(),
            ]);
            setSummary(summaryData);
            setCpuUsage(cpuData);
            setMemoryUsage(memoryData);
            setDiskUsage(diskData);
            setGpuData(gpu);
            setDockerData(docker);
            setLastUpdate(new Date());
        } catch (err) {
            console.error('서버 통계 데이터 로드 실패:', err);
            setError(err.response?.data?.detail || '서버 통계 데이터를 불러올 수 없습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();

        // 1분마다 자동 갱신
        const interval = setInterval(() => {
            loadData();
        }, 60000);

        return () => clearInterval(interval);
    }, []);

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
            <Box sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                        <Typography
                            variant="h4"
                            component="h1"
                            gutterBottom
                            sx={{ color: colors.primary, fontWeight: 'bold', mb: 1 }}
                        >
                            서버 현황 통계
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            서버 자원 사용 현황 및 분석 (1분마다 자동 갱신)
                        </Typography>
                    </Box>
                    {lastUpdate && (
                        <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            backgroundColor: '#f0fdf4',
                            px: 2,
                            py: 1,
                            borderRadius: 2,
                            border: `1px solid ${colors.success}33`,
                        }}>
                            <RefreshIcon
                                sx={{
                                    fontSize: 20,
                                    color: colors.success,
                                    animation: 'spin 2s linear infinite',
                                    '@keyframes spin': {
                                        '0%': { transform: 'rotate(0deg)' },
                                        '100%': { transform: 'rotate(360deg)' },
                                    },
                                }}
                            />
                            <Box>
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                    마지막 업데이트
                                </Typography>
                                <Typography variant="body2" sx={{ color: colors.success, fontWeight: 'bold' }}>
                                    {lastUpdate.toLocaleTimeString('ko-KR')}
                                </Typography>
                            </Box>
                        </Box>
                    )}
                </Box>
            </Box>

            {/* 요약 카드 - 그라데이션 */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="CPU 사용량"
                        value={summary?.cpu_usage?.toFixed(1) || 0}
                        unit="%"
                        icon={ComputerIcon}
                        gradient={[colors.primary, colors.primaryLight]}
                        trend="up"
                        trendValue="+2%"
                        loading={isLoading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="메모리 사용량"
                        value={summary?.memory_usage?.toFixed(1) || 0}
                        unit="%"
                        icon={MemoryIcon}
                        gradient={[colors.accent, colors.accentLight]}
                        trend="up"
                        trendValue="+1%"
                        loading={isLoading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="디스크 사용량"
                        value={summary?.disk_usage?.toFixed(1) || 0}
                        unit="%"
                        icon={StorageIcon}
                        gradient={[colors.warning, colors.warningLight]}
                        trend="up"
                        trendValue="+0.5%"
                        loading={isLoading}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <GradientStatCard
                        title="서버 상태"
                        value={summary?.status || '정상'}
                        unit=""
                        icon={CheckCircleIcon}
                        gradient={[colors.success, colors.successLight]}
                        loading={isLoading}
                    />
                </Grid>
            </Grid>

            {/* 차트 시각화 */}
            <Grid container spacing={3}>
                {/* CPU 사용량 추이 - Area Chart */}
                <Grid item xs={12} md={6}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 3,
                            borderRadius: 2,
                            boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <ComputerIcon sx={{ fontSize: 28, color: colors.primary, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                CPU 사용량 추이
                            </Typography>
                        </Box>
                        {isLoading ? (
                            <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                                <CircularProgress />
                            </Box>
                        ) : cpuUsage.length > 0 ? (
                            <ResponsiveContainer width="100%" height={350}>
                                <AreaChart data={cpuUsage}>
                                    <defs>
                                        <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={colors.primary} stopOpacity={0.8} />
                                            <stop offset="95%" stopColor={colors.primary} stopOpacity={0.1} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="timestamp"
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                    />
                                    <YAxis
                                        domain={[0, 100]}
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                        label={{ value: '사용량 (%)', angle: -90, position: 'insideLeft' }}
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
                                        type="monotone"
                                        dataKey="usage"
                                        stroke={colors.primary}
                                        strokeWidth={3}
                                        fill="url(#colorCpu)"
                                        name="CPU 사용량 (%)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <Typography variant="body2" color="text.secondary" align="center">
                                데이터가 없습니다.
                            </Typography>
                        )}
                    </Paper>
                </Grid>

                {/* 메모리 사용량 추이 - Area Chart */}
                <Grid item xs={12} md={6}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 3,
                            borderRadius: 2,
                            boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <MemoryIcon sx={{ fontSize: 28, color: colors.accent, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                메모리 사용량 추이
                            </Typography>
                        </Box>
                        {isLoading ? (
                            <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                                <CircularProgress />
                            </Box>
                        ) : memoryUsage.length > 0 ? (
                            <ResponsiveContainer width="100%" height={350}>
                                <AreaChart data={memoryUsage}>
                                    <defs>
                                        <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={colors.accent} stopOpacity={0.8} />
                                            <stop offset="95%" stopColor={colors.accent} stopOpacity={0.1} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="timestamp"
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                    />
                                    <YAxis
                                        domain={[0, 100]}
                                        tick={{ fontSize: 12, fill: '#64748b' }}
                                        stroke="#cbd5e1"
                                        label={{ value: '사용량 (%)', angle: -90, position: 'insideLeft' }}
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
                                        type="monotone"
                                        dataKey="usage"
                                        stroke={colors.accent}
                                        strokeWidth={3}
                                        fill="url(#colorMemory)"
                                        name="메모리 사용량 (%)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <Typography variant="body2" color="text.secondary" align="center">
                                데이터가 없습니다.
                            </Typography>
                        )}
                    </Paper>
                </Grid>

                {/* 디스크 사용량 - Table */}
                <Grid item xs={12}>
                    <Paper
                        elevation={0}
                        sx={{
                            p: 3,
                            borderRadius: 2,
                            boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                            <StorageIcon sx={{ fontSize: 28, color: colors.warning, mr: 1.5 }} />
                            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                디스크 사용량
                            </Typography>
                        </Box>
                        {isLoading ? (
                            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
                                <CircularProgress />
                            </Box>
                        ) : diskUsage.length > 0 ? (
                            <Box sx={{ overflowX: 'auto' }}>
                                <table style={{
                                    width: '100%',
                                    borderCollapse: 'collapse',
                                    fontSize: '0.875rem',
                                }}>
                                    <thead>
                                        <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>마운트 지점</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>총 용량</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>사용 용량</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>남은 용량</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>사용률</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {diskUsage.map((disk, idx) => (
                                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                <td style={{ padding: '12px' }}>{disk.mount_point}</td>
                                                <td style={{ padding: '12px', textAlign: 'right' }}>
                                                    {(disk.total / (1024 ** 3)).toFixed(2)} GB
                                                </td>
                                                <td style={{ padding: '12px', textAlign: 'right' }}>
                                                    {(disk.used / (1024 ** 3)).toFixed(2)} GB
                                                </td>
                                                <td style={{ padding: '12px', textAlign: 'right' }}>
                                                    {(disk.free / (1024 ** 3)).toFixed(2)} GB
                                                </td>
                                                <td style={{
                                                    padding: '12px',
                                                    textAlign: 'right',
                                                    color: disk.percent > 80 ? colors.accent : disk.percent > 60 ? colors.warning : colors.success,
                                                    fontWeight: disk.percent > 80 ? 'bold' : 'normal',
                                                }}>
                                                    {disk.percent.toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </Box>
                        ) : (
                            <Typography variant="body2" color="text.secondary" align="center">
                                데이터가 없습니다.
                            </Typography>
                        )}
                    </Paper>
                </Grid>

                {/* GPU 사용량 - Table */}
                {gpuData && gpuData.has_gpu && (
                    <Grid item xs={12}>
                        <Paper
                            elevation={0}
                            sx={{
                                p: 3,
                                borderRadius: 2,
                                boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                            }}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <ComputerIcon sx={{ fontSize: 28, color: colors.info, mr: 1.5 }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                    GPU 사용량 ({gpuData.gpu_count}대)
                                </Typography>
                            </Box>
                            <Box sx={{ overflowX: 'auto' }}>
                                <table style={{
                                    width: '100%',
                                    borderCollapse: 'collapse',
                                    fontSize: '0.875rem',
                                }}>
                                    <thead>
                                        <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>GPU</th>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>모델명</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>사용률</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>메모리</th>
                                            <th style={{ padding: '12px', textAlign: 'right', color: colors.primary }}>온도</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {gpuData.gpus.map((gpu, idx) => (
                                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                <td style={{ padding: '12px' }}>GPU {gpu.index}</td>
                                                <td style={{ padding: '12px' }}>{gpu.name}</td>
                                                <td style={{
                                                    padding: '12px',
                                                    textAlign: 'right',
                                                    color: gpu.utilization > 80 ? colors.accent : colors.success,
                                                    fontWeight: gpu.utilization > 80 ? 'bold' : 'normal',
                                                }}>
                                                    {gpu.utilization.toFixed(1)}%
                                                </td>
                                                <td style={{ padding: '12px', textAlign: 'right' }}>
                                                    {gpu.memory_used.toFixed(0)} / {gpu.memory_total.toFixed(0)} MB
                                                </td>
                                                <td style={{
                                                    padding: '12px',
                                                    textAlign: 'right',
                                                    color: gpu.temperature > 80 ? colors.accent : colors.success,
                                                }}>
                                                    {gpu.temperature.toFixed(0)}°C
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </Box>
                        </Paper>
                    </Grid>
                )}

                {/* Docker 컨테이너 - Table */}
                {dockerData && dockerData.total_count > 0 && (
                    <Grid item xs={12}>
                        <Paper
                            elevation={0}
                            sx={{
                                p: 3,
                                borderRadius: 2,
                                boxShadow: '0 2px 10px 0 rgba(0,0,0,0.08)',
                            }}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <CheckCircleIcon sx={{ fontSize: 28, color: colors.success, mr: 1.5 }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold', color: colors.primary }}>
                                    Docker 컨테이너 ({dockerData.running_count}/{dockerData.total_count} 실행 중)
                                </Typography>
                            </Box>
                            <Box sx={{ overflowX: 'auto' }}>
                                <table style={{
                                    width: '100%',
                                    borderCollapse: 'collapse',
                                    fontSize: '0.875rem',
                                }}>
                                    <thead>
                                        <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>ID</th>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>이름</th>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>이미지</th>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>상태</th>
                                            <th style={{ padding: '12px', textAlign: 'left', color: colors.primary }}>포트</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dockerData.containers.map((container, idx) => (
                                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                <td style={{ padding: '12px', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                                                    {container.id}
                                                </td>
                                                <td style={{ padding: '12px', fontWeight: 500 }}>{container.name}</td>
                                                <td style={{ padding: '12px', fontSize: '0.85rem' }}>{container.image}</td>
                                                <td style={{
                                                    padding: '12px',
                                                    color: container.status.includes('Up') ? colors.success : colors.accent,
                                                    fontWeight: 500,
                                                }}>
                                                    {container.status}
                                                </td>
                                                <td style={{ padding: '12px', fontSize: '0.85rem' }}>{container.ports || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </Box>
                        </Paper>
                    </Grid>
                )}
            </Grid>
        </Box>
    );
}
