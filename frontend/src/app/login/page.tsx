'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Container, Typography, Button, Paper, CircularProgress } from '@mui/material';
import { Header } from '@/components/layout';
import { useAuthStore } from '@/lib/auth';
import { colors } from '@/theme/theme';

export default function LoginPage() {
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
      <Container maxWidth="sm" sx={{ pt: 16 }}>
        <Paper
          sx={{
            p: 4,
            textAlign: 'center',
            background: 'rgba(22, 33, 62, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <Typography variant="h4" sx={{ mb: 2, fontWeight: 700 }}>
            Login to Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Sign in with your Discord account to manage your servers.
          </Typography>
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
            Continue with Discord
          </Button>
        </Paper>
      </Container>
    </Box>
  );
}
