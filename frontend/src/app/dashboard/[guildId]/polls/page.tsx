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
  FormControlLabel,
  Switch,
  Snackbar,
  Alert,
  Skeleton,
  IconButton,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pollsApi, guildsApi } from '@/lib/api';
import { colors } from '@/theme/theme';
import { formatDistanceToNow } from 'date-fns';
import type { PollListItem, PollCreate } from '@/types';

export default function PollsPage() {
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

  const { data: polls, isLoading } = useQuery({
    queryKey: ['polls', guildId],
    queryFn: () => pollsApi.list(guildId),
  });

  const createMutation = useMutation({
    mutationFn: (data: PollCreate) => pollsApi.create(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['polls', guildId] });
      setCreateOpen(false);
      setSnackbar({ open: true, message: 'Poll created!', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: 'Failed to create poll', severity: 'error' }),
  });

  const endMutation = useMutation({
    mutationFn: (pollId: number) => pollsApi.end(guildId, pollId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['polls', guildId] });
      setSnackbar({ open: true, message: 'Poll ended!', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: 'Failed to end poll', severity: 'error' }),
  });

  const textChannels = guildData?.channels.filter((c) => c.type === 'text') || [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Polls
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          Create Poll
        </Button>
      </Box>

      {/* Active Polls */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Active ({polls?.total_active || 0})
      </Typography>
      {isLoading ? (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {[...Array(3)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={200} />
            </Grid>
          ))}
        </Grid>
      ) : polls?.active.length === 0 ? (
        <Typography color="text.secondary" sx={{ mb: 4 }}>
          No active polls
        </Typography>
      ) : (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {polls?.active.map((p) => (
            <Grid item xs={12} sm={6} md={4} key={p.id}>
              <PollCard poll={p} onEnd={() => endMutation.mutate(p.id)} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Ended Polls */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Ended ({polls?.total_ended || 0})
      </Typography>
      {isLoading ? (
        <Grid container spacing={3}>
          {[...Array(3)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={200} />
            </Grid>
          ))}
        </Grid>
      ) : polls?.ended.length === 0 ? (
        <Typography color="text.secondary">
          No ended polls
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {polls?.ended.map((p) => (
            <Grid item xs={12} sm={6} md={4} key={p.id}>
              <PollCard poll={p} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Dialog */}
      <CreatePollDialog
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

function PollCard({
  poll,
  onEnd,
}: {
  poll: PollListItem;
  onEnd?: () => void;
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
          <Typography variant="h6" fontWeight={600} sx={{ flex: 1, pr: 1 }}>
            {poll.question}
          </Typography>
          {!poll.ended && onEnd && (
            <IconButton size="small" onClick={onEnd} sx={{ color: colors.error }}>
              <StopIcon />
            </IconButton>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            label={poll.ended ? 'Ended' : 'Active'}
            size="small"
            sx={{
              bgcolor: poll.ended
                ? 'rgba(255, 255, 255, 0.1)'
                : 'rgba(46, 204, 113, 0.2)',
              color: poll.ended ? 'text.secondary' : colors.success,
            }}
          />
          {poll.multi_select && (
            <Chip
              label="Multi-select"
              size="small"
              sx={{ bgcolor: 'rgba(52, 152, 219, 0.2)', color: colors.secondary }}
            />
          )}
        </Box>

        <Typography variant="body2" color="text.secondary">
          {poll.option_count} options • {poll.total_votes} votes
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {poll.end_time
            ? poll.ended
              ? `Ended ${formatDistanceToNow(new Date(poll.end_time), { addSuffix: true })}`
              : `Ends ${formatDistanceToNow(new Date(poll.end_time), { addSuffix: true })}`
            : 'No end time'}
        </Typography>
      </CardContent>
    </Card>
  );
}

function CreatePollDialog({
  open,
  onClose,
  channels,
  onSubmit,
  isLoading,
}: {
  open: boolean;
  onClose: () => void;
  channels: { id: string; name: string }[];
  onSubmit: (data: PollCreate) => void;
  isLoading: boolean;
}) {
  const [channelId, setChannelId] = useState('');
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [multiSelect, setMultiSelect] = useState(false);
  const [duration, setDuration] = useState<number | null>(null);

  const handleAddOption = () => {
    if (options.length < 10) {
      setOptions([...options, '']);
    }
  };

  const handleRemoveOption = (index: number) => {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== index));
    }
  };

  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const handleSubmit = () => {
    if (!channelId || !question || options.some((o) => !o.trim())) return;
    onSubmit({
      channel_id: channelId,
      question,
      options: options.filter((o) => o.trim()),
      multi_select: multiSelect,
      duration_seconds: duration,
    });
  };

  const handleClose = () => {
    setChannelId('');
    setQuestion('');
    setOptions(['', '']);
    setMultiSelect(false);
    setDuration(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Poll</DialogTitle>
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
          label="Question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          sx={{ mt: 2 }}
        />

        <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
          Options
        </Typography>
        {options.map((option, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <TextField
              fullWidth
              size="small"
              label={`Option ${index + 1}`}
              value={option}
              onChange={(e) => handleOptionChange(index, e.target.value)}
            />
            {options.length > 2 && (
              <IconButton onClick={() => handleRemoveOption(index)} size="small">
                <DeleteIcon />
              </IconButton>
            )}
          </Box>
        ))}
        {options.length < 10 && (
          <Button size="small" onClick={handleAddOption}>
            Add Option
          </Button>
        )}

        <FormControlLabel
          control={
            <Switch
              checked={multiSelect}
              onChange={(e) => setMultiSelect(e.target.checked)}
            />
          }
          label="Allow multiple selections"
          sx={{ mt: 2, display: 'block' }}
        />

        <FormControl fullWidth sx={{ mt: 2 }}>
          <InputLabel>Duration</InputLabel>
          <Select
            value={duration || ''}
            onChange={(e) => setDuration(e.target.value ? (e.target.value as number) : null)}
            label="Duration"
          >
            <MenuItem value="">No end time</MenuItem>
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
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!channelId || !question || options.some((o) => !o.trim()) || isLoading}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}
