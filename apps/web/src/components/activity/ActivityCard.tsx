/** Activity card component with timer display and action buttons. */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import StopIcon from '@mui/icons-material/Stop';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { Activity } from '@time-tracker/shared';
import { useActivityStore } from '../../stores/activityStore';
import { useTimer } from '../../hooks/useTimer';
import TimerDisplay from './TimerDisplay';
import ConfirmDialog from '../common/ConfirmDialog';

interface ActivityCardProps {
  activity: Activity;
  onEdit?: (activity: Activity) => void;
}

const ActivityCard: React.FC<ActivityCardProps> = ({ activity, onEdit }) => {
  const { startActivity, pauseActivity, stopActivity, deleteActivity } =
    useActivityStore();
  const { display, isRunning } = useTimer(activity);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmStop, setConfirmStop] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const statusText = {
    RUNNING: '运行中',
    PAUSED: '已暂停',
    ENDED: '已结束',
  };

  const handleStart = async () => {
    setIsProcessing(true);
    try {
      await startActivity(activity.id, activity.is_parallel);
    } catch (error) {
      console.error('Failed to start activity:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePause = async () => {
    setIsProcessing(true);
    try {
      await pauseActivity(activity.id);
    } catch (error) {
      console.error('Failed to pause activity:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStop = async () => {
    setConfirmStop(false);
    setIsProcessing(true);
    try {
      await stopActivity(activity.id);
    } catch (error) {
      console.error('Failed to stop activity:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async () => {
    setConfirmDelete(false);
    try {
      await deleteActivity(activity.id);
    } catch (error) {
      console.error('Failed to delete activity:', error);
    }
  };

  const statusColor = activity.status === 'RUNNING'
    ? 'success'
    : activity.status === 'PAUSED'
    ? 'warning'
    : 'default';

  return (
    <>
      <Card
        sx={{
          mb: 1.5,
          borderLeft: `4px solid ${activity.color}`,
          opacity: isProcessing ? 0.6 : 1,
          transition: 'opacity 0.2s',
        }}
      >
        <CardContent sx={{ pb: '12px !important' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
              <Typography variant="subtitle1" noWrap sx={{ fontWeight: 600 }}>
                {activity.name}
              </Typography>
              <Chip
                label={statusText[activity.status]}
                size="small"
                color={statusColor}
                variant="outlined"
              />
              {activity.is_parallel && (
                <Chip label="并行" size="small" color="info" variant="outlined" />
              )}
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {/* Action buttons based on status */}
              {activity.status === 'PAUSED' && (
                <IconButton
                  color="primary"
                  onClick={handleStart}
                  disabled={isProcessing}
                  size="small"
                >
                  <PlayArrowIcon />
                </IconButton>
              )}
              {activity.status === 'RUNNING' && (
                <IconButton
                  color="warning"
                  onClick={handlePause}
                  disabled={isProcessing}
                  size="small"
                >
                  <PauseIcon />
                </IconButton>
              )}
              {activity.status !== 'ENDED' && (
                <IconButton
                  color="error"
                  onClick={() => setConfirmStop(true)}
                  disabled={isProcessing}
                  size="small"
                >
                  <StopIcon />
                </IconButton>
              )}
              {activity.status === 'ENDED' && (
                <CheckCircleIcon color="disabled" fontSize="small" />
              )}

              <IconButton
                onClick={(e) => setMenuAnchor(e.currentTarget)}
                size="small"
              >
                <MoreVertIcon />
              </IconButton>
            </Box>
          </Box>

          {/* Timer display */}
          <Box sx={{ mt: 1 }}>
            <TimerDisplay display={display} isRunning={isRunning} color={activity.color} />
          </Box>

          {/* Tags */}
          {activity.tags && activity.tags.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, mt: 1, flexWrap: 'wrap' }}>
              {activity.tags.map((tag) => (
                <Chip
                  key={tag.id}
                  label={tag.name}
                  size="small"
                  sx={{ backgroundColor: tag.color, color: 'white', fontSize: '0.7rem' }}
                />
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Context menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem
          onClick={() => {
            setMenuAnchor(null);
            onEdit?.(activity);
          }}
        >
          <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            setMenuAnchor(null);
            setConfirmDelete(true);
          }}
        >
          <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
          <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Confirm dialogs */}
      <ConfirmDialog
        open={confirmDelete}
        title="删除活动"
        message={`确定要删除 "${activity.name}" 吗？此操作无法撤销。`}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      />
      <ConfirmDialog
        open={confirmStop}
        title="停止活动"
        message={`确定要停止 "${activity.name}" 吗？`}
        onConfirm={handleStop}
        onCancel={() => setConfirmStop(false)}
      />
    </>
  );
};

export default ActivityCard;
