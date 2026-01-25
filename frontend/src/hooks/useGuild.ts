import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guildsApi } from '@/lib/api';
import type {
  GuildDetailResponse,
  GuildListItem,
  LevelingSettings,
  StarSettings,
  WordCounterSettings,
  LoggerSettings,
  AutoroleSettings,
  MusicSettings,
} from '@/types';

// ギルド一覧を取得
export function useGuilds() {
  return useQuery({
    queryKey: ['guilds'],
    queryFn: guildsApi.list,
  });
}

// ギルド詳細を取得
export function useGuild(guildId: string) {
  return useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId),
    enabled: !!guildId,
  });
}

// 設定更新用のMutation hooks
export function useLevelingSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<LevelingSettings>) => guildsApi.updateLeveling(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}

export function useStarSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<StarSettings>) => guildsApi.updateStar(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}

export function useWordCounterSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<WordCounterSettings>) => guildsApi.updateWordCounter(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}

export function useLoggerSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<LoggerSettings>) => guildsApi.updateLogger(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}

export function useAutoroleSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<AutoroleSettings>) => guildsApi.updateAutorole(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}

export function useMusicSettings(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<MusicSettings>) => guildsApi.updateMusic(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guild', guildId] });
    },
  });
}
