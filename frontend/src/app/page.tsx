'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Leaderboard as LeaderboardIcon,
  CardGiftcard as GiveawayIcon,
  MusicNote as MusicIcon,
  Star as StarIcon,
  Forum as ForumIcon,
} from '@mui/icons-material';
import { Header } from '@/components/layout';
import { useAuthStore } from '@/lib/auth';
import { colors } from '@/theme/theme';

const features = [
  {
    icon: <LeaderboardIcon sx={{ fontSize: 40 }} />,
    title: 'Leveling System',
    description: 'Track XP and levels for text and voice activity with customizable rewards.',
  },
  {
    icon: <StarIcon sx={{ fontSize: 40 }} />,
    title: 'Star Board',
    description: 'Highlight popular messages with community-driven star reactions.',
  },
  {
    icon: <GiveawayIcon sx={{ fontSize: 40 }} />,
    title: 'Giveaways',
    description: 'Create and manage giveaways with easy entry and automatic winner selection.',
  },
  {
    icon: <MusicIcon sx={{ fontSize: 40 }} />,
    title: 'Music Player',
    description: 'High-quality music playback with queue management and DJ controls.',
  },
  {
    icon: <ForumIcon sx={{ fontSize: 40 }} />,
    title: 'Polls & Voting',
    description: 'Create interactive polls to gather community feedback.',
  },
  {
    icon: <SettingsIcon sx={{ fontSize: 40 }} />,
    title: 'Easy Configuration',
    description: 'Manage all settings through an intuitive web dashboard.',
  },
];

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth, login } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Header />

      {/* Hero Section */}
      <Box
        sx={{
          pt: 16,
          pb: 10,
          background: `linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%)`,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(circle at 30% 40%, rgba(155, 89, 182, 0.1) 0%, transparent 50%)`,
          },
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography
              variant="h1"
              sx={{
                fontWeight: 800,
                fontSize: { xs: '2.5rem', md: '4rem' },
                mb: 2,
                background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              SumireBot
            </Typography>
            <Typography
              variant="h5"
              color="text.secondary"
              sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
            >
              A powerful Discord bot with leveling, giveaways, music, and more.
              Manage everything from an intuitive web dashboard.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                onClick={login}
                sx={{
                  background: colors.discord,
                  px: 4,
                  py: 1.5,
                  fontSize: '1.1rem',
                  '&:hover': {
                    background: '#4752C4',
                  },
                }}
              >
                Login with Discord
              </Button>
              <Button
                variant="outlined"
                size="large"
                href="https://discord.com/oauth2/authorize"
                target="_blank"
                sx={{
                  borderColor: colors.primary,
                  color: colors.primary,
                  px: 4,
                  py: 1.5,
                  fontSize: '1.1rem',
                  '&:hover': {
                    borderColor: colors.primary,
                    background: 'rgba(155, 89, 182, 0.1)',
                  },
                }}
              >
                Invite Bot
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography
          variant="h3"
          textAlign="center"
          sx={{ mb: 6, fontWeight: 700 }}
        >
          Features
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  background: 'rgba(22, 33, 62, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    borderColor: 'rgba(155, 89, 182, 0.3)',
                    boxShadow: '0 8px 24px rgba(155, 89, 182, 0.15)',
                  },
                }}
              >
                <CardContent sx={{ p: 3, textAlign: 'center' }}>
                  <Box
                    sx={{
                      color: colors.primary,
                      mb: 2,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 4,
          textAlign: 'center',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          &copy; {new Date().getFullYear()} SumireBot. All rights reserved.
        </Typography>
      </Box>
    </Box>
  );
}
