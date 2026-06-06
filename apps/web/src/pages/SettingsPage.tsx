/** Settings page with theme and user preferences. */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Switch,
  FormControlLabel,
  Button,
  Divider,
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
      <Typography variant="h5" sx={{ mb: 3 }}>Settings</Typography>

      {/* User info */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>Account</Typography>
        <Typography variant="body2" color="text.secondary">
          Username: {user?.username || 'N/A'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Email: {user?.email || 'N/A'}
        </Typography>
        <Button
          variant="outlined"
          color="error"
          startIcon={<LogoutIcon />}
          onClick={logout}
          sx={{ mt: 2 }}
        >
          Sign Out
        </Button>
      </Paper>

      {/* Theme */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>Appearance</Typography>
        <FormControl fullWidth size="small">
          <InputLabel>Theme</InputLabel>
          <Select
            value={theme}
            label="Theme"
            onChange={(e: SelectChangeEvent) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
          >
            <MenuItem value="light">Light</MenuItem>
            <MenuItem value="dark">Dark</MenuItem>
            <MenuItem value="system">System Default</MenuItem>
          </Select>
        </FormControl>
      </Paper>

      {/* Data export */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>Data Export</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Format</InputLabel>
            <Select
              value={exportFormat}
              label="Format"
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
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </Box>
      </Paper>

      {/* About */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>About</Typography>
        <Typography variant="body2" color="text.secondary">
          Time Tracker v1.0.0
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Multi-platform activity time tracking system
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
