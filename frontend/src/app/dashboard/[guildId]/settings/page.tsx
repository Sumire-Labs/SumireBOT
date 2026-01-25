'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Divider,
  Snackbar,
  Alert,
  Skeleton,
  Button,
  TextField,
  Slider,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guildsApi } from '@/lib/api';
import type { ChannelInfo, RoleInfo } from '@/types';

export default function SettingsPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  const queryClient = useQueryClient();
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const { data: guildData, isLoading } = useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId),
  });

  const textChannels = guildData?.channels.filter((c) => c.type === 'text') || [];
  const roles = guildData?.roles || [];

  const showSuccess = (message: string) => {
    setSnackbar({ open: true, message, severity: 'success' });
  };

  const showError = (message: string) => {
    setSnackbar({ open: true, message, severity: 'error' });
  };

  // Mutations
  const levelingMutation = useMutation({
    mutationFn: (data: Parameters<typeof guildsApi.updateLeveling>[1]) =>
      guildsApi.updateLeveling(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
      showSuccess('Leveling settings updated');
    },
    onError: () => showError('Failed to update leveling settings'),
  });

  const starMutation = useMutation({
    mutationFn: (data: Parameters<typeof guildsApi.updateStar>[1]) =>
      guildsApi.updateStar(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
      showSuccess('Star settings updated');
    },
    onError: () => showError('Failed to update star settings'),
  });

  const loggerMutation = useMutation({
    mutationFn: (data: Parameters<typeof guildsApi.updateLogger>[1]) =>
      guildsApi.updateLogger(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
      showSuccess('Logger settings updated');
    },
    onError: () => showError('Failed to update logger settings'),
  });

  const autoroleMutation = useMutation({
    mutationFn: (data: Parameters<typeof guildsApi.updateAutorole>[1]) =>
      guildsApi.updateAutorole(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
      showSuccess('Autorole settings updated');
    },
    onError: () => showError('Failed to update autorole settings'),
  });

  const musicMutation = useMutation({
    mutationFn: (data: Parameters<typeof guildsApi.updateMusic>[1]) =>
      guildsApi.updateMusic(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
      showSuccess('Music settings updated');
    },
    onError: () => showError('Failed to update music settings'),
  });

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
          Settings
        </Typography>
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} variant="rounded" height={200} sx={{ mb: 3 }} />
        ))}
      </Box>
    );
  }

  const settings = guildData?.settings;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Settings
      </Typography>

      <Stack spacing={3}>
        {/* Leveling Settings */}
        <SettingsCard title="Leveling System">
          <FormControlLabel
            control={
              <Switch
                checked={settings?.leveling.enabled}
                onChange={(e) => levelingMutation.mutate({ enabled: e.target.checked })}
              />
            }
            label="Enable Leveling"
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            Track XP and levels for text activity
          </Typography>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>Ignored Channels</InputLabel>
            <Select
              multiple
              value={settings?.leveling.ignored_channels || []}
              onChange={(e) => levelingMutation.mutate({ ignored_channels: e.target.value as string[] })}
              label="Ignored Channels"
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value) => {
                    const channel = textChannels.find((c) => c.id === value);
                    return <Chip key={value} label={`#${channel?.name || value}`} size="small" />;
                  })}
                </Box>
              )}
            >
              {textChannels.map((channel) => (
                <MenuItem key={channel.id} value={channel.id}>
                  #{channel.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </SettingsCard>

        {/* Star Settings */}
        <SettingsCard title="Star Board">
          <FormControlLabel
            control={
              <Switch
                checked={settings?.star.enabled}
                onChange={(e) => starMutation.mutate({ enabled: e.target.checked })}
              />
            }
            label="Enable Star Board"
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            Highlight popular messages with star reactions
          </Typography>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>Weekly Report Channel</InputLabel>
            <Select
              value={settings?.star.weekly_report_channel_id || ''}
              onChange={(e) => starMutation.mutate({ weekly_report_channel_id: e.target.value || null })}
              label="Weekly Report Channel"
            >
              <MenuItem value="">None</MenuItem>
              {textChannels.map((channel) => (
                <MenuItem key={channel.id} value={channel.id}>
                  #{channel.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </SettingsCard>

        {/* Logger Settings */}
        <SettingsCard title="Activity Logger">
          <FormControlLabel
            control={
              <Switch
                checked={settings?.logger.enabled}
                onChange={(e) => loggerMutation.mutate({ enabled: e.target.checked })}
              />
            }
            label="Enable Logger"
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            Log server activity to a channel
          </Typography>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>Log Channel</InputLabel>
            <Select
              value={settings?.logger.channel_id || ''}
              onChange={(e) => loggerMutation.mutate({ channel_id: e.target.value || null })}
              label="Log Channel"
              disabled={!settings?.logger.enabled}
            >
              <MenuItem value="">Select a channel</MenuItem>
              {textChannels.map((channel) => (
                <MenuItem key={channel.id} value={channel.id}>
                  #{channel.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </SettingsCard>

        {/* Autorole Settings */}
        <SettingsCard title="Auto Role">
          <FormControlLabel
            control={
              <Switch
                checked={settings?.autorole.enabled}
                onChange={(e) => autoroleMutation.mutate({ enabled: e.target.checked })}
              />
            }
            label="Enable Auto Role"
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            Automatically assign roles to new members
          </Typography>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>Human Role</InputLabel>
            <Select
              value={settings?.autorole.human_role_id || ''}
              onChange={(e) => autoroleMutation.mutate({ human_role_id: e.target.value || null })}
              label="Human Role"
              disabled={!settings?.autorole.enabled}
            >
              <MenuItem value="">None</MenuItem>
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>Bot Role</InputLabel>
            <Select
              value={settings?.autorole.bot_role_id || ''}
              onChange={(e) => autoroleMutation.mutate({ bot_role_id: e.target.value || null })}
              label="Bot Role"
              disabled={!settings?.autorole.enabled}
            >
              <MenuItem value="">None</MenuItem>
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </SettingsCard>

        {/* Music Settings */}
        <SettingsCard title="Music">
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Configure music playback settings
          </Typography>

          <Typography gutterBottom>Default Volume: {settings?.music.default_volume}%</Typography>
          <Slider
            value={settings?.music.default_volume || 50}
            onChange={(_, value) => musicMutation.mutate({ default_volume: value as number })}
            min={0}
            max={100}
            valueLabelDisplay="auto"
            sx={{ mb: 3 }}
          />

          <FormControl fullWidth size="small" sx={{ mt: 2 }}>
            <InputLabel>DJ Role</InputLabel>
            <Select
              value={settings?.music.dj_role_id || ''}
              onChange={(e) => musicMutation.mutate({ dj_role_id: e.target.value || null })}
              label="DJ Role"
            >
              <MenuItem value="">None (Everyone can use)</MenuItem>
              {roles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </SettingsCard>
      </Stack>

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

function SettingsCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card
      sx={{
        background: 'rgba(22, 33, 62, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          {title}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {children}
      </CardContent>
    </Card>
  );
}
