'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Box, CircularProgress, Toolbar, useMediaQuery, useTheme } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Header, Sidebar } from '@/components/layout';
import { useAuthStore } from '@/lib/auth';
import { guildsApi } from '@/lib/api';

const DRAWER_WIDTH = 260;

export default function GuildLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);

  const guildId = params.guildId as string;
  const { isAuthenticated, isLoading: authLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const { data: guildData, isLoading: guildLoading, error } = useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId),
    enabled: isAuthenticated && !!guildId,
    retry: false, // Don't retry on error
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      console.error('Guild fetch error:', error);
      // Show error for debugging instead of redirecting
      // router.push('/dashboard');
    }
  }, [error, router]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  if (error) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <Header showMenuButton={isMobile} onMenuClick={handleDrawerToggle} />
        <Toolbar />
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 'calc(100vh - 64px)',
            gap: 2,
            p: 3,
          }}
        >
          <Box sx={{ color: 'error.main', fontSize: '3rem' }}>⚠️</Box>
          <Box sx={{ textAlign: 'center' }}>
            <Box sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 1 }}>Failed to load server</Box>
            <Box sx={{ color: 'text.secondary', mb: 2 }}>
              {(error as Error)?.message || 'Unknown error'}
            </Box>
            <Box
              component="button"
              onClick={() => router.push('/dashboard')}
              sx={{
                px: 3,
                py: 1,
                border: '1px solid',
                borderColor: 'primary.main',
                borderRadius: 1,
                bgcolor: 'transparent',
                color: 'primary.main',
                cursor: 'pointer',
                '&:hover': { bgcolor: 'rgba(155, 89, 182, 0.1)' },
              }}
            >
              Back to Server List
            </Box>
          </Box>
        </Box>
      </Box>
    );
  }

  if (authLoading || guildLoading || !guildData) {
    return (
      <Box sx={{ minHeight: '100vh' }}>
        <Header showMenuButton={isMobile} onMenuClick={handleDrawerToggle} />
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

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Header showMenuButton={isMobile} onMenuClick={handleDrawerToggle} />

      {/* Mobile Sidebar */}
      {isMobile && (
        <Sidebar
          guild={guildData.info}
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
        />
      )}

      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sidebar guild={guildData.info} variant="permanent" />
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          ml: { md: `${DRAWER_WIDTH}px` },
          width: { xs: '100%', md: `calc(100% - ${DRAWER_WIDTH}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
