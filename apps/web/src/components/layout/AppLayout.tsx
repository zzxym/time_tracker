/** Main application layout with header, sidebar, and content area. */

import React from 'react';
import { Box } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';
import { useUIStore } from '../../stores/uiStore';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Header />
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          marginTop: '64px',
          marginLeft: sidebarOpen ? '280px' : 0,
          padding: 3,
          overflow: 'auto',
          transition: 'margin-left 0.2s ease',
          backgroundColor: 'background.default',
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default AppLayout;
