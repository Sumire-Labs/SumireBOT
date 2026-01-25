import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { giveawaysApi } from '@/lib/api';
import type { GiveawayCreate } from '@/types';

export function useGiveaways(guildId: string) {
  return useQuery({
    queryKey: ['giveaways', guildId],
    queryFn: () => giveawaysApi.list(guildId),
    enabled: !!guildId,
  });
}

export function useGiveaway(guildId: string, giveawayId: number) {
  return useQuery({
    queryKey: ['giveaway', guildId, giveawayId],
    queryFn: () => giveawaysApi.get(guildId, giveawayId),
    enabled: !!guildId && !!giveawayId,
  });
}

export function useCreateGiveaway(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GiveawayCreate) => giveawaysApi.create(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
    },
  });
}

export function useEndGiveaway(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (giveawayId: number) => giveawaysApi.end(guildId, giveawayId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
    },
  });
}

export function useRerollGiveaway(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ giveawayId, count = 1 }: { giveawayId: number; count?: number }) =>
      giveawaysApi.reroll(guildId, giveawayId, count),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['giveaways', guildId] });
    },
  });
}
