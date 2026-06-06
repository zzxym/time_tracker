/** Timer display component with animated indicator. */

import React from 'react';
import { Box, Typography } from '@mui/material';

interface TimerDisplayProps {
  display: string;
  isRunning: boolean;
  color?: string;
  size?: 'small' | 'medium' | 'large';
}

const fontSizes = {
  small: '1.5rem',
  medium: '2rem',
  large: '3rem',
};

const TimerDisplay: React.FC<TimerDisplayProps> = ({
  display,
  isRunning,
  color = '#4CAF50',
  size = 'medium',
}) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {/* Pulsing dot indicator when running */}
      {isRunning && (
        <Box
          sx={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: color,
            animation: 'pulse 1s ease-in-out infinite',
          }}
        />
      )}

      <Typography
        variant="body1"
        sx={{
          fontFamily: '"Roboto Mono", monospace',
          fontSize: fontSizes[size],
          fontWeight: 600,
          color: isRunning ? color : 'text.primary',
          letterSpacing: '0.05em',
        }}
      >
        {display}
      </Typography>

      <style>{`
        @keyframes pulse {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
          100% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </Box>
  );
};

export default TimerDisplay;
