'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Divider,
  Typography,
  Avatar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Leaderboard as LeaderboardIcon,
  CardGiftcard as GiveawayIcon,
  Poll as PollIcon,
  BarChart as StatsIcon,
} from '@mui/icons-material';
import type { GuildInfo } from '@/types';

const DRAWER_WIDTH = 260;

interface SidebarProps {
  guild: GuildInfo;
  open?: boolean;
  onClose?: () => void;
  variant?: 'permanent' | 'temporary';
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

export default function Sidebar({ guild, open = true, onClose, variant = 'permanent' }: SidebarProps) {
  const pathname = usePathname();
  const basePath = `/dashboard/${guild.id}`;

  const navItems: NavItem[] = [
    { label: 'Overview', href: basePath, icon: <DashboardIcon /> },
    { label: 'Settings', href: `${basePath}/settings`, icon: <SettingsIcon /> },
    { label: 'Leaderboard', href: `${basePath}/leaderboard`, icon: <LeaderboardIcon /> },
    { label: 'Giveaways', href: `${basePath}/giveaways`, icon: <GiveawayIcon /> },
    { label: 'Polls', href: `${basePath}/polls`, icon: <PollIcon /> },
    { label: 'Statistics', href: `${basePath}/statistics`, icon: <StatsIcon /> },
  ];

  const isActive = (href: string) => {
    if (href === basePath) {
      return pathname === basePath;
    }
    return pathname.startsWith(href);
  };

  const drawerContent = (
    <Box sx={{ overflow: 'auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar />

      {/* Guild Info */}
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            src={guild.icon_url || undefined}
            alt={guild.name}
            sx={{ width: 48, height: 48 }}
          >
            {guild.name.charAt(0)}
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight={600} noWrap sx={{ maxWidth: 150 }}>
              {guild.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {guild.member_count?.toLocaleString()} members
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider />

      {/* Navigation */}
      <List sx={{ flex: 1, py: 1 }}>
        {navItems.map((item) => (
          <ListItem key={item.href} disablePadding>
            <ListItemButton
              component={Link}
              href={item.href}
              selected={isActive(item.href)}
              onClick={onClose}
            >
              <ListItemIcon
                sx={{
                  color: isActive(item.href) ? 'primary.main' : 'text.secondary',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActive(item.href) ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />

      {/* Back to guild list */}
      <List>
        <ListItem disablePadding>
          <ListItemButton component={Link} href="/dashboard" onClick={onClose}>
            <ListItemText
              primary="Change Server"
              primaryTypographyProps={{
                variant: 'body2',
                color: 'text.secondary',
              }}
            />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          borderRight: '1px solid rgba(255, 255, 255, 0.12)',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
}
