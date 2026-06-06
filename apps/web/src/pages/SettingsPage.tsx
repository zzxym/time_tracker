/** Settings page with theme and user preferences. */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  SelectChangeEvent,
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { useAuthStore } from '../stores/authStore';
import { useUIStore } from '../stores/uiStore';
import { downloadExport } from '../services/exportService';
import type { ExportFormat } from '@time-tracker/shared';

const SettingsPage: React.FC = () => {
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useUIStore();
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await downloadExport(exportFormat);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>设置</Typography>

      {/* User info */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>账号</Typography>
        <Typography variant="body2" color="text.secondary">
          用户名：{user?.username || '无'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          邮箱：{user?.email || '无'}
        </Typography>
        <Button
          variant="outlined"
          color="error"
          startIcon={<LogoutIcon />}
          onClick={logout}
          sx={{ mt: 2 }}
        >
          退出登录
        </Button>
      </Paper>

      {/* Theme */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>外观</Typography>
        <FormControl fullWidth size="small">
          <InputLabel>主题</InputLabel>
          <Select
            value={theme}
            label="主题"
            onChange={(e: SelectChangeEvent) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
          >
            <MenuItem value="light">浅色</MenuItem>
            <MenuItem value="dark">深色</MenuItem>
            <MenuItem value="system">跟随系统</MenuItem>
          </Select>
        </FormControl>
      </Paper>

      {/* Data export */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>数据导出</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>格式</InputLabel>
            <Select
              value={exportFormat}
              label="格式"
              onChange={(e: SelectChangeEvent) => setExportFormat(e.target.value as ExportFormat)}
            >
              <MenuItem value="csv">CSV</MenuItem>
              <MenuItem value="excel">Excel</MenuItem>
              <MenuItem value="json">JSON</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<FileDownloadIcon />}
            onClick={handleExport}
            disabled={isExporting}
          >
            {isExporting ? '导出中...' : '导出'}
          </Button>
        </Box>
      </Paper>

      {/* About */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>关于</Typography>
        <Typography variant="body2" color="text.secondary">
          时间追踪器 v1.0.0
        </Typography>
        <Typography variant="body2" color="text.secondary">
          跨平台活动时间追踪系统
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
