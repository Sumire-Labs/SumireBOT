'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  Chip,
  Skeleton,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { leaderboardsApi } from '@/lib/api';
import { colors } from '@/theme/theme';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function LeaderboardPage() {
  const params = useParams();
  const guildId = params.guildId as string;
  const [tab, setTab] = useState(0);

  const { data: levelData, isLoading: levelLoading } = useQuery({
    queryKey: ['leaderboard', 'levels', guildId],
    queryFn: () => leaderboardsApi.levels(guildId),
  });

  const { data: vcData, isLoading: vcLoading } = useQuery({
    queryKey: ['leaderboard', 'vc', guildId],
    queryFn: () => leaderboardsApi.vc(guildId),
  });

  const { data: starData, isLoading: starLoading } = useQuery({
    queryKey: ['leaderboard', 'stars', guildId],
    queryFn: () => leaderboardsApi.starUsers(guildId),
  });

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1: return '#FFD700';
      case 2: return '#C0C0C0';
      case 3: return '#CD7F32';
      default: return 'text.secondary';
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Leaderboard
      </Typography>

      <Tabs
        value={tab}
        onChange={(_, newValue) => setTab(newValue)}
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Levels" />
        <Tab label="Voice Time" />
        <Tab label="Stars" />
      </Tabs>

      {/* Levels Tab */}
      <TabPanel value={tab} index={0}>
        <Card
          sx={{
            background: 'rgba(22, 33, 62, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell align="right">Level</TableCell>
                  <TableCell align="right">XP</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {levelLoading ? (
                  [...Array(10)].map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton width={30} /></TableCell>
                      <TableCell><Skeleton width={150} /></TableCell>
                      <TableCell><Skeleton width={50} /></TableCell>
                      <TableCell><Skeleton width={70} /></TableCell>
                    </TableRow>
                  ))
                ) : levelData?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">No data available</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  levelData?.items.map((item) => (
                    <TableRow key={item.user_id}>
                      <TableCell>
                        <Typography
                          fontWeight={item.rank <= 3 ? 700 : 400}
                          sx={{ color: getRankColor(item.rank) }}
                        >
                          #{item.rank}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32, bgcolor: colors.primary }}>
                            {item.user_id.slice(-2)}
                          </Avatar>
                          <Typography>User {item.user_id.slice(-6)}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`Lv.${item.level}`}
                          size="small"
                          sx={{ bgcolor: 'rgba(155, 89, 182, 0.2)', color: colors.primary }}
                        />
                      </TableCell>
                      <TableCell align="right">{item.xp.toLocaleString()} XP</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </TabPanel>

      {/* Voice Time Tab */}
      <TabPanel value={tab} index={1}>
        <Card
          sx={{
            background: 'rgba(22, 33, 62, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell align="right">VC Level</TableCell>
                  <TableCell align="right">Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {vcLoading ? (
                  [...Array(10)].map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton width={30} /></TableCell>
                      <TableCell><Skeleton width={150} /></TableCell>
                      <TableCell><Skeleton width={50} /></TableCell>
                      <TableCell><Skeleton width={70} /></TableCell>
                    </TableRow>
                  ))
                ) : vcData?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">No data available</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  vcData?.items.map((item) => (
                    <TableRow key={item.user_id}>
                      <TableCell>
                        <Typography
                          fontWeight={item.rank <= 3 ? 700 : 400}
                          sx={{ color: getRankColor(item.rank) }}
                        >
                          #{item.rank}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32, bgcolor: colors.secondary }}>
                            {item.user_id.slice(-2)}
                          </Avatar>
                          <Typography>User {item.user_id.slice(-6)}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`Lv.${item.vc_level}`}
                          size="small"
                          sx={{ bgcolor: 'rgba(52, 152, 219, 0.2)', color: colors.secondary }}
                        />
                      </TableCell>
                      <TableCell align="right">{formatTime(item.vc_time)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </TabPanel>

      {/* Stars Tab */}
      <TabPanel value={tab} index={2}>
        <Card
          sx={{
            background: 'rgba(22, 33, 62, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell align="right">Stars</TableCell>
                  <TableCell align="right">Messages</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {starLoading ? (
                  [...Array(10)].map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton width={30} /></TableCell>
                      <TableCell><Skeleton width={150} /></TableCell>
                      <TableCell><Skeleton width={50} /></TableCell>
                      <TableCell><Skeleton width={70} /></TableCell>
                    </TableRow>
                  ))
                ) : starData?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">No data available</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  starData?.items.map((item) => (
                    <TableRow key={item.user_id}>
                      <TableCell>
                        <Typography
                          fontWeight={item.rank <= 3 ? 700 : 400}
                          sx={{ color: getRankColor(item.rank) }}
                        >
                          #{item.rank}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32, bgcolor: colors.warning }}>
                            {item.user_id.slice(-2)}
                          </Avatar>
                          <Typography>User {item.user_id.slice(-6)}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${item.total_stars}`}
                          size="small"
                          icon={<span>⭐</span>}
                          sx={{ bgcolor: 'rgba(243, 156, 18, 0.2)', color: colors.warning }}
                        />
                      </TableCell>
                      <TableCell align="right">{item.message_count}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </TabPanel>
    </Box>
  );
}
