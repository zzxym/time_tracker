/** Top navigation header. */

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SyncIcon from '@mui/icons-material/Sync';
import { useUIStore } from '../../stores/uiStore';
import { useSyncStore, type WSConnectionStatus } from '../../stores/syncStore';
import { useAuthStore } from '../../stores/authStore';

const statusConfig: Record<WSConnectionStatus, { label: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
  connected: { label: 'Connected', color: 'success' },
  connecting: { label: 'Connecting', color: 'warning' },
  disconnected: { label: 'Offline', color: 'error' },
  reconnecting: { label: 'Reconnecting', color: 'warning' },
};

const Header: React.FC = () => {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const connectionStatus = useSyncStore((s) => s.connectionStatus);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const config = statusConfig[connectionStatus];

  return (
    <AppBar
      position="fixed"
      sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={toggleSidebar}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
          Time Tracker
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            icon={connectionStatus === 'connected' ? <WifiIcon /> : <WifiOffIcon />}
            label={config.label}
            color={config.color}
            size="small"
            variant="outlined"
            sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)' }}
          />

          {connectionStatus === 'reconnecting' && (
            <SyncIcon sx={{ animation: 'spin 1s linear infinite', color: 'white' }} />
          )}

          {user && (
            <Chip
              label={user.username}
              size="small"
              sx={{ color: 'white' }}
              onClick={logout}
            />
          )}
        </Box>
      </Toolbar>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </AppBar>
  );
};

export default Header;
