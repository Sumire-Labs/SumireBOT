'use client';

import { Box, Typography, Button, Paper } from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { colors } from '@/theme/theme';

interface ErrorDisplayProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
}: ErrorDisplayProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 300,
        p: 3,
      }}
    >
      <Paper
        sx={{
          p: 4,
          textAlign: 'center',
          maxWidth: 400,
          background: 'rgba(22, 33, 62, 0.8)',
          border: '1px solid rgba(231, 76, 60, 0.3)',
        }}
      >
        <ErrorIcon sx={{ fontSize: 64, color: colors.error, mb: 2 }} />
        <Typography variant="h5" sx={{ mb: 1, fontWeight: 600 }}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {message}
        </Typography>
        {onRetry && (
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
            sx={{ borderColor: colors.error, color: colors.error }}
          >
            Try Again
          </Button>
        )}
      </Paper>
    </Box>
  );
}
