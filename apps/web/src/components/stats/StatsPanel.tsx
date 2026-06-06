/** Statistics panel component with charts and summary. */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Paper,
  Card,
  CardContent,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { useActivityStore } from '../../stores/activityStore';
import { formatDurationHuman, formatPercentage } from '@time-tracker/shared';
import type { ActivityStat } from '@time-tracker/shared';

const StatsPanel: React.FC = () => {
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day');
  const [stats, setStats] = useState<{
    total_duration_seconds: number;
    activity_count: number;
    activities: ActivityStat[];
  } | null>(null);
  const { activities } = useActivityStore();

  useEffect(() => {
    // Calculate stats from local activities
    const totalDuration = activities.reduce(
      (sum, a) => sum + a.total_duration_seconds,
      0
    );

    const activityStats: ActivityStat[] = activities.map((a) => ({
      activity_id: a.id,
      activity_name: a.name,
      activity_color: a.color,
      total_duration_seconds: a.total_duration_seconds,
      percentage: totalDuration > 0
        ? Math.round((a.total_duration_seconds / totalDuration) * 1000) / 10
        : 0,
    }));

    setStats({
      total_duration_seconds: totalDuration,
      activity_count: activities.length,
      activities: activityStats,
    });
  }, [activities, period]);

  const pieData = stats?.activities.map((a) => ({
    name: a.activity_name,
    value: a.total_duration_seconds,
    color: a.activity_color,
  })) || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">统计</Typography>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={(_, v) => v && setPeriod(v)}
          size="small"
        >
          <ToggleButton value="day">今日</ToggleButton>
          <ToggleButton value="week">本周</ToggleButton>
          <ToggleButton value="month">本月</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Summary cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">总时长</Typography>
            <Typography variant="h5">
              {stats ? formatDurationHuman(stats.total_duration_seconds) : '--'}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">活动数</Typography>
            <Typography variant="h5">{stats?.activity_count ?? '--'}</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Pie chart */}
      {pieData.length > 0 ? (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>时间分布</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => formatDurationHuman(value)}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            此时间段暂无活动数据。
          </Typography>
        </Box>
      )}

      {/* Activity breakdown list */}
      {stats && stats.activities.length > 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>活动详情</Typography>
          {stats.activities.map((a) => (
            <Box
              key={a.activity_id}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                py: 1,
                borderBottom: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: a.activity_color,
                  flexShrink: 0,
                }}
              />
              <Typography variant="body2" sx={{ flex: 1 }}>
                {a.activity_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatDurationHuman(a.total_duration_seconds)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 50, textAlign: 'right' }}>
                {formatPercentage(a.percentage / 100)}
              </Typography>
            </Box>
          ))}
        </Paper>
      )}
    </Box>
  );
};

export default StatsPanel;
