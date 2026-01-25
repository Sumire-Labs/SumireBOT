import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pollsApi } from '@/lib/api';
import type { PollCreate } from '@/types';

export function usePolls(guildId: string) {
  return useQuery({
    queryKey: ['polls', guildId],
    queryFn: () => pollsApi.list(guildId),
    enabled: !!guildId,
  });
}

export function usePoll(guildId: string, pollId: number) {
  return useQuery({
    queryKey: ['poll', guildId, pollId],
    queryFn: () => pollsApi.get(guildId, pollId),
    enabled: !!guildId && !!pollId,
  });
}

export function usePollResults(guildId: string, pollId: number) {
  return useQuery({
    queryKey: ['poll-results', guildId, pollId],
    queryFn: () => pollsApi.results(guildId, pollId),
    enabled: !!guildId && !!pollId,
  });
}

export function useCreatePoll(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PollCreate) => pollsApi.create(guildId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['polls', guildId] });
    },
  });
}

export function useEndPoll(guildId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pollId: number) => pollsApi.end(guildId, pollId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['polls', guildId] });
    },
  });
}
