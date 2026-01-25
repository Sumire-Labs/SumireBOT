'use client';

import { useParams } from 'next/navigation';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { colors } from '@/theme/theme';

export default function StatisticsPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Statistics
      </Typography>

      <Card
        sx={{
          background: 'rgba(22, 33, 62, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          textAlign: 'center',
          py: 6,
        }}
      >
        <CardContent>
          <TrendingUpIcon sx={{ fontSize: 64, color: colors.primary, mb: 2 }} />
          <Typography variant="h5" sx={{ mb: 1 }}>
            Coming Soon
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Detailed server statistics and analytics will be available here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
