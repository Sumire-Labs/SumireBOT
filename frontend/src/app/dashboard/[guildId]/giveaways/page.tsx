'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  Alert,
  Skeleton,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Stop as StopIcon,
  Refresh as RerollIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { giveawaysApi, guildsApi } from '@/lib/api';
import { colors } from '@/theme/theme';
import { formatDistanceToNow, format } from 'date-fns';
import type { GiveawayListItem, GiveawayCreate } from '@/types';

export default function GiveawaysPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const { data: guildData } = useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId),
  });

  const { data: giveaways, isLoading } = useQuery({
    queryKey: ['giveaways', guildId],
    queryFn: () => giveawaysApi.list(guildId),
  });

  const createMutation = useMutation({
    mutationFn: (data: GiveawayCreate) => giveawaysApi.create(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
      setCreateOpen(false);
      setSnackbar({ open: true, message: 'Giveaway created!', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: 'Failed to create giveaway', severity: 'error' }),
  });

  const endMutation = useMutation({
    mutationFn: (giveawayId: number) => giveawaysApi.end(guildId, giveawayId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
      setSnackbar({ open: true, message: 'Giveaway ended!', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: 'Failed to end giveaway', severity: 'error' }),
  });

  const rerollMutation = useMutation({
    mutationFn: (giveawayId: number) => giveawaysApi.reroll(guildId, giveawayId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
      setSnackbar({ open: true, message: 'Rerolled winners!', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: 'Failed to reroll', severity: 'error' }),
  });

  const textChannels = guildData?.channels.filter((c) => c.type === 'text') || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Giveaways
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          Create Giveaway
        </Button>
      </Box>

      {/* Active Giveaways */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Active ({giveaways?.total_active || 0})
      </Typography>
      {isLoading ? (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {[...Array(3)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={180} />
            </Grid>
          ))}
        </Grid>
      ) : giveaways?.active.length === 0 ? (
        <Typography color="text.secondary" sx={{ mb: 4 }}>
          No active giveaways
        </Typography>
      ) : (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {giveaways?.active.map((g) => (
            <Grid item xs={12} sm={6} md={4} key={g.id}>
              <GiveawayCard
                giveaway={g}
                onEnd={() => endMutation.mutate(g.id)}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Ended Giveaways */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Ended ({giveaways?.total_ended || 0})
      </Typography>
      {isLoading ? (
        <Grid container spacing={3}>
          {[...Array(3)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={180} />
            </Grid>
          ))}
        </Grid>
      ) : giveaways?.ended.length === 0 ? (
        <Typography color="text.secondary">
          No ended giveaways
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {giveaways?.ended.map((g) => (
            <Grid item xs={12} sm={6} md={4} key={g.id}>
              <GiveawayCard
                giveaway={g}
                onReroll={() => rerollMutation.mutate(g.id)}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Dialog */}
      <CreateGiveawayDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        channels={textChannels}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

function GiveawayCard({
  giveaway,
  onEnd,
  onReroll,
}: {
  giveaway: GiveawayListItem;
  onEnd?: () => void;
  onReroll?: () => void;
}) {
  return (
    <Card
      sx={{
        background: 'rgba(22, 33, 62, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" fontWeight={600} noWrap sx={{ flex: 1 }}>
            {giveaway.prize}
          </Typography>
          {!giveaway.ended && onEnd && (
            <IconButton size="small" onClick={onEnd} sx={{ color: colors.error }}>
              <StopIcon />
            </IconButton>
          )}
          {giveaway.ended && onReroll && (
            <IconButton size="small" onClick={onReroll} sx={{ color: colors.primary }}>
              <RerollIcon />
            </IconButton>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            label={giveaway.ended ? 'Ended' : 'Active'}
            size="small"
            sx={{
              bgcolor: giveaway.ended
                ? 'rgba(255, 255, 255, 0.1)'
                : 'rgba(46, 204, 113, 0.2)',
              color: giveaway.ended ? 'text.secondary' : colors.success,
            }}
          />
          <Chip
            label={`${giveaway.winner_count} winner${giveaway.winner_count > 1 ? 's' : ''}`}
            size="small"
            sx={{ bgcolor: 'rgba(155, 89, 182, 0.2)', color: colors.primary }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary">
          {giveaway.participant_count} participants
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {giveaway.ended
            ? `Ended ${formatDistanceToNow(new Date(giveaway.end_time), { addSuffix: true })}`
            : `Ends ${formatDistanceToNow(new Date(giveaway.end_time), { addSuffix: true })}`}
        </Typography>
      </CardContent>
    </Card>
  );
}

function CreateGiveawayDialog({
  open,
  onClose,
  channels,
  onSubmit,
  isLoading,
}: {
  open: boolean;
  onClose: () => void;
  channels: { id: string; name: string }[];
  onSubmit: (data: GiveawayCreate) => void;
  isLoading: boolean;
}) {
  const [channelId, setChannelId] = useState('');
  const [prize, setPrize] = useState('');
  const [winnerCount, setWinnerCount] = useState(1);
  const [duration, setDuration] = useState(3600); // 1 hour default

  const handleSubmit = () => {
    if (!channelId || !prize) return;
    onSubmit({
      channel_id: channelId,
      prize,
      winner_count: winnerCount,
      duration_seconds: duration,
    });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Giveaway</DialogTitle>
      <DialogContent>
        <FormControl fullWidth sx={{ mt: 2 }}>
          <InputLabel>Channel</InputLabel>
          <Select
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            label="Channel"
          >
            {channels.map((channel) => (
              <MenuItem key={channel.id} value={channel.id}>
                #{channel.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="Prize"
          value={prize}
          onChange={(e) => setPrize(e.target.value)}
          sx={{ mt: 2 }}
        />

        <TextField
          fullWidth
          label="Winner Count"
          type="number"
          value={winnerCount}
          onChange={(e) => setWinnerCount(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
          inputProps={{ min: 1, max: 20 }}
          sx={{ mt: 2 }}
        />

        <FormControl fullWidth sx={{ mt: 2 }}>
          <InputLabel>Duration</InputLabel>
          <Select
            value={duration}
            onChange={(e) => setDuration(e.target.value as number)}
            label="Duration"
          >
            <MenuItem value={3600}>1 hour</MenuItem>
            <MenuItem value={21600}>6 hours</MenuItem>
            <MenuItem value={43200}>12 hours</MenuItem>
            <MenuItem value={86400}>1 day</MenuItem>
            <MenuItem value={259200}>3 days</MenuItem>
            <MenuItem value={604800}>1 week</MenuItem>
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!channelId || !prize || isLoading}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}
