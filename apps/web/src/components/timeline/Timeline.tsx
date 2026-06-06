/** Timeline view component showing activities as time blocks. */

import React, { useMemo } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import type { Activity } from '@time-tracker/shared';
import { useActivityStore } from '../../stores/activityStore';
import { formatDurationHuman } from '@time-tracker/shared';

const HOUR_HEIGHT = 60; // pixels per hour

const Timeline: React.FC = () => {
  const { activities } = useActivityStore();

  // Filter activities that have time segments for today
  const timelineBlocks = useMemo(() => {
    const blocks: Array<{
      activity: Activity;
      startHour: number;
      durationHours: number;
      segmentIndex: number;
    }> = [];

    for (const activity of activities) {
      if (!activity.time_segments) continue;

      for (let i = 0; i < activity.time_segments.length; i++) {
        const segment = activity.time_segments[i];
        if (!segment.start_time) continue;

        const startTime = new Date(segment.start_time);
        const endTime = segment.end_time ? new Date(segment.end_time) : new Date();

        const startHour = startTime.getHours() + startTime.getMinutes() / 60;
        const durationMs = endTime.getTime() - startTime.getTime();
        const durationHours = Math.max(durationMs / (1000 * 60 * 60), 0.1);

        blocks.push({
          activity,
          startHour,
          durationHours,
          segmentIndex: i,
        });
      }
    }

    return blocks.sort((a, b) => a.startHour - b.startHour);
  }, [activities]);

  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>Timeline</Typography>

      <Paper sx={{ p: 2, position: 'relative', overflow: 'auto', maxHeight: '80vh' }}>
        {/* Hour grid lines */}
        <Box sx={{ position: 'relative', minHeight: 24 * HOUR_HEIGHT }}>
          {hours.map((hour) => (
            <Box
              key={hour}
              sx={{
                position: 'absolute',
                top: hour * HOUR_HEIGHT,
                left: 60,
                right: 0,
                borderBottom: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ position: 'absolute', left: -55, top: -8 }}
              >
                {String(hour).padStart(2, '0')}:00
              </Typography>
            </Box>
          ))}

          {/* Activity blocks */}
          {timelineBlocks.map((block, index) => (
            <Box
              key={`${block.activity.id}-${block.segmentIndex}-${index}`}
              sx={{
                position: 'absolute',
                top: block.startHour * HOUR_HEIGHT,
                left: 70,
                right: 10,
                minHeight: Math.max(block.durationHours * HOUR_HEIGHT, 20),
                backgroundColor: block.activity.color,
                opacity: 0.85,
                borderRadius: 1,
                padding: '2px 8px',
                overflow: 'hidden',
                cursor: 'pointer',
                '&:hover': { opacity: 1 },
              }}
            >
              <Typography variant="caption" sx={{ color: 'white', fontWeight: 600 }}>
                {block.activity.name}
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)', display: 'block' }}>
                {formatDurationHuman(block.durationHours * 3600)}
              </Typography>
            </Box>
          ))}

          {/* Current time indicator */}
          <Box
            sx={{
              position: 'absolute',
              top: (new Date().getHours() + new Date().getMinutes() / 60) * HOUR_HEIGHT,
              left: 55,
              right: 0,
              height: 2,
              backgroundColor: 'error.main',
              zIndex: 10,
            }}
          />
        </Box>
      </Paper>

      {timelineBlocks.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            今天还没有记录活动。开始追踪来查看你的时间线吧！
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default Timeline;
