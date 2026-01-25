'use client';

import { useParams } from 'next/navigation';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Skeleton,
} from '@mui/material';
import {
  TrendingUp as LevelIcon,
  Star as StarIcon,
  CardGiftcard as GiveawayIcon,
  Poll as PollIcon,
  MusicNote as MusicIcon,
  Forum as ForumIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { guildsApi, giveawaysApi, pollsApi } from '@/lib/api';
import { colors } from '@/theme/theme';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  enabled?: boolean;
}

function StatCard({ title, value, icon, color, enabled = true }: StatCardProps) {
  return (
    <Card
      sx={{
        background: 'rgba(22, 33, 62, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 1,
              borderRadius: 2,
              bgcolor: `${color}20`,
              color: color,
            }}
          >
            {icon}
          </Box>
        </Box>
        {!enabled && (
          <Chip
            label="Disabled"
            size="small"
            sx={{
              mt: 1,
              bgcolor: 'rgba(255, 255, 255, 0.1)',
              fontSize: '0.7rem',
            }}
          />
        )}
      </CardContent>
    </Card>
  );
}

export default function GuildOverviewPage() {
  const params = useParams();
  const guildId = params.guildId as string;

  const { data: guildData, isLoading: guildLoading } = useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId),
  });

  const { data: giveaways } = useQuery({
    queryKey: ['giveaways', guildId],
    queryFn: () => giveawaysApi.list(guildId),
    enabled: !!guildId,
  });

  const { data: polls } = useQuery({
    queryKey: ['polls', guildId],
    queryFn: () => pollsApi.list(guildId),
    enabled: !!guildId,
  });

  if (guildLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
          <Skeleton width={200} />
        </Typography>
        <Grid container spacing={3}>
          {[...Array(6)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rounded" height={120} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  const settings = guildData?.settings;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Overview
      </Typography>

      <Grid container spacing={3}>
        {/* Leveling */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Leveling System"
            value={settings?.leveling.enabled ? 'Active' : 'Disabled'}
            icon={<LevelIcon />}
            color={colors.primary}
            enabled={settings?.leveling.enabled}
          />
        </Grid>

        {/* Star Board */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Star Board"
            value={settings?.star.enabled ? 'Active' : 'Disabled'}
            icon={<StarIcon />}
            color={colors.warning}
            enabled={settings?.star.enabled}
          />
        </Grid>

        {/* Active Giveaways */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Active Giveaways"
            value={giveaways?.total_active || 0}
            icon={<GiveawayIcon />}
            color={colors.success}
          />
        </Grid>

        {/* Active Polls */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Active Polls"
            value={polls?.total_active || 0}
            icon={<PollIcon />}
            color={colors.secondary}
          />
        </Grid>

        {/* Word Counter */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Tracked Words"
            value={settings?.wordcounter.words.length || 0}
            icon={<ForumIcon />}
            color={colors.info}
            enabled={settings?.wordcounter.enabled}
          />
        </Grid>

        {/* Music */}
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Music"
            value={`Vol: ${settings?.music.default_volume || 50}%`}
            icon={<MusicIcon />}
            color={colors.error}
          />
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Typography variant="h5" sx={{ mt: 6, mb: 3, fontWeight: 600 }}>
        Recent Activity
      </Typography>

      <Grid container spacing={3}>
        {/* Active Giveaways List */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(22, 33, 62, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Active Giveaways
              </Typography>
              {giveaways?.active.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No active giveaways
                </Typography>
              ) : (
                giveaways?.active.slice(0, 3).map((g) => (
                  <Box
                    key={g.id}
                    sx={{
                      p: 1.5,
                      mb: 1,
                      bgcolor: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight={600}>
                      {g.prize}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {g.participant_count} participants
                    </Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Active Polls List */}
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              background: 'rgba(22, 33, 62, 0.5)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Active Polls
              </Typography>
              {polls?.active.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No active polls
                </Typography>
              ) : (
                polls?.active.slice(0, 3).map((p) => (
                  <Box
                    key={p.id}
                    sx={{
                      p: 1.5,
                      mb: 1,
                      bgcolor: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight={600}>
                      {p.question}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {p.total_votes} votes
                    </Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
