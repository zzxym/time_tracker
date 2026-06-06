/** Sidebar navigation with tag filtering. */

import React, { useEffect } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import TimelineIcon from '@mui/icons-material/Timeline';
import BarChartIcon from '@mui/icons-material/BarChart';
import LabelIcon from '@mui/icons-material/Label';
import SettingsIcon from '@mui/icons-material/Settings';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '../../stores/uiStore';
import { useTagStore } from '../../stores/tagStore';

const DRAWER_WIDTH = 280;

const navItems = [
  { text: '首页', icon: <HomeIcon />, path: '/home' },
  { text: '时间线', icon: <TimelineIcon />, path: '/timeline' },
  { text: '统计', icon: <BarChartIcon />, path: '/stats' },
  { text: '标签', icon: <LabelIcon />, path: '/tags' },
  { text: '设置', icon: <SettingsIcon />, path: '/settings' },
];

const Sidebar: React.FC = () => {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const { tags, selectedTagIds, fetchTags, toggleTagFilter } = useTagStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={sidebarOpen}
      sx={{
        width: sidebarOpen ? DRAWER_WIDTH : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          marginTop: '64px',
          height: 'calc(100% - 64px)',
        },
      }}
    >
      {/* Navigation */}
      <List>
        {navItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      {/* Tag Filters */}
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
          按标签筛选
        </Typography>
        {tags.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            暂无标签
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            {tags.map((tag) => (
              <FormControlLabel
                key={tag.id}
                control={
                  <Checkbox
                    checked={selectedTagIds.includes(tag.id)}
                    onChange={() => toggleTagFilter(tag.id)}
                    size="small"
                    sx={{ color: tag.color, '&.Mui-checked': { color: tag.color } }}
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: tag.color,
                      }}
                    />
                    <Typography variant="body2">{tag.name}</Typography>
                  </Box>
                }
              />
            ))}
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;
