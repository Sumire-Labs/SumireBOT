'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardActionArea,
  CardContent,
  Avatar,
  Chip,
  CircularProgress,
  Toolbar,
  Alert,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout';
import { useAuthStore } from '@/lib/auth';
import { guildsApi } from '@/lib/api';
import { colors } from '@/theme/theme';
import type { GuildListItem } from '@/types';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const { data: guilds, isLoading: guildsLoading, error } = useQuery({
    queryKey: ['guilds'],
    queryFn: guildsApi.list,
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || guildsLoading) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <Header />
        <Toolbar />
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  // Split guilds into bot-joined and not-joined
  const joinedGuilds = guilds?.filter((g) => g.bot_joined) || [];
  const notJoinedGuilds = guilds?.filter((g) => !g.bot_joined) || [];

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Header />
      <Toolbar />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
          Select a Server
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to load servers. Please try again.
          </Alert>
        )}

        {/* Servers with Bot */}
        {joinedGuilds.length > 0 && (
          <>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
              Your Servers
            </Typography>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {joinedGuilds.map((guild) => (
                <Grid item xs={12} sm={6} md={4} key={guild.id}>
                  <GuildCard guild={guild} />
                </Grid>
              ))}
            </Grid>
          </>
        )}

        {/* Servers without Bot */}
        {notJoinedGuilds.length > 0 && (
          <>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
              Invite Bot to Server
            </Typography>
            <Grid container spacing={3}>
              {notJoinedGuilds.map((guild) => (
                <Grid item xs={12} sm={6} md={4} key={guild.id}>
                  <GuildCard guild={guild} />
                </Grid>
              ))}
            </Grid>
          </>
        )}

        {guilds?.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary">
              No servers found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              You need to have Manage Server permission to see servers here.
            </Typography>
          </Box>
        )}
      </Container>
    </Box>
  );
}

function GuildCard({ guild }: { guild: GuildListItem }) {
  const content = (
    <CardContent sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar
          src={guild.icon_url || undefined}
          alt={guild.name}
          sx={{
            width: 56,
            height: 56,
            bgcolor: colors.primary,
          }}
        >
          {guild.name.charAt(0).toUpperCase()}
        </Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            variant="subtitle1"
            fontWeight={600}
            noWrap
            sx={{ mb: 0.5 }}
          >
            {guild.name}
          </Typography>
          {guild.bot_joined ? (
            <Chip
              label="Bot Active"
              size="small"
              sx={{
                bgcolor: 'rgba(46, 204, 113, 0.2)',
                color: colors.success,
                fontWeight: 500,
              }}
            />
          ) : (
            <Chip
              label="Invite Bot"
              size="small"
              sx={{
                bgcolor: 'rgba(155, 89, 182, 0.2)',
                color: colors.primary,
                fontWeight: 500,
              }}
            />
          )}
        </Box>
      </Box>
    </CardContent>
  );

  if (guild.bot_joined) {
    return (
      <Card
        sx={{
          background: 'rgba(22, 33, 62, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'rgba(155, 89, 182, 0.3)',
            transform: 'translateY(-2px)',
          },
        }}
      >
        <CardActionArea component={Link} href={`/dashboard/${guild.id}`}>
          {content}
        </CardActionArea>
      </Card>
    );
  }

  // For servers without bot, link to invite
  return (
    <Card
      sx={{
        background: 'rgba(22, 33, 62, 0.3)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        opacity: 0.8,
        transition: 'all 0.2s ease',
        '&:hover': {
          opacity: 1,
          borderColor: 'rgba(155, 89, 182, 0.2)',
        },
      }}
    >
      <CardActionArea
        href={`https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot%20applications.commands&permissions=8&guild_id=${guild.id}`}
        target="_blank"
      >
        {content}
      </CardActionArea>
    </Card>
  );
}
