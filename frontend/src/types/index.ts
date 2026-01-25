// ==================== 認証関連 ====================

export interface User {
  id: number;
  username: string;
  display_name: string;
  avatar_url: string;
}

export interface AuthCheckResponse {
  authenticated: boolean;
  user: User | null;
}

// ==================== ギルド関連 ====================

export interface GuildListItem {
  id: string;
  name: string;
  icon_url: string | null;
  has_manage_permission: boolean;
  bot_joined: boolean;
}

export interface GuildInfo {
  id: string;
  name: string;
  icon_url: string | null;
  member_count: number;
  bot_joined: boolean;
}

export interface ChannelInfo {
  id: string;
  name: string;
  type: 'text' | 'voice' | 'category';
}

export interface RoleInfo {
  id: string;
  name: string;
  color: number;
  position: number;
}

// ==================== 設定関連 ====================

export interface LevelingSettings {
  enabled: boolean;
  ignored_channels: string[];
}

export interface StarSettings {
  enabled: boolean;
  target_channels: string[];
  weekly_report_channel_id: string | null;
}

export interface WordCounterSettings {
  enabled: boolean;
  words: string[];
  milestones: number[];
}

export interface LoggerSettings {
  enabled: boolean;
  channel_id: string | null;
  log_messages: boolean;
  log_channels: boolean;
  log_roles: boolean;
  log_members: boolean;
}

export interface AutoroleSettings {
  enabled: boolean;
  human_role_id: string | null;
  bot_role_id: string | null;
}

export interface TicketSettings {
  category_id: string | null;
  panel_channel_id: string | null;
  panel_message_id: string | null;
  ticket_counter: number;
}

export interface MusicSettings {
  default_volume: number;
  dj_role_id: string | null;
  music_channel_id: string | null;
}

export interface GuildSettings {
  leveling: LevelingSettings;
  star: StarSettings;
  wordcounter: WordCounterSettings;
  logger: LoggerSettings;
  autorole: AutoroleSettings;
  ticket: TicketSettings;
  music: MusicSettings;
}

export interface GuildDetailResponse {
  info: GuildInfo;
  channels: ChannelInfo[];
  roles: RoleInfo[];
  settings: GuildSettings;
}

// ==================== ランキング関連 ====================

export interface LevelLeaderboardItem {
  rank: number;
  user_id: string;
  xp: number;
  level: number;
}

export interface LevelLeaderboardResponse {
  items: LevelLeaderboardItem[];
  total_users: number;
}

export interface VCLeaderboardItem {
  rank: number;
  user_id: string;
  vc_time: number;
  vc_level: number;
}

export interface VCLeaderboardResponse {
  items: VCLeaderboardItem[];
  total_users: number;
}

export interface StarUserLeaderboardItem {
  rank: number;
  user_id: string;
  total_stars: number;
  message_count: number;
}

export interface StarUserLeaderboardResponse {
  items: StarUserLeaderboardItem[];
  total_messages: number;
}

export interface StarMessageLeaderboardItem {
  rank: number;
  message_id: string;
  channel_id: string;
  author_id: string;
  star_count: number;
}

export interface StarMessageLeaderboardResponse {
  items: StarMessageLeaderboardItem[];
  total_messages: number;
}

export interface WordLeaderboardItem {
  rank: number;
  user_id: string;
  count: number;
}

export interface WordLeaderboardResponse {
  word: string;
  items: WordLeaderboardItem[];
  total_users: number;
}

export interface ReactionLeaderboardItem {
  rank: number;
  user_id: string;
  reactions_given: number;
  reactions_received: number;
}

export interface ReactionLeaderboardResponse {
  type: 'given' | 'received';
  items: ReactionLeaderboardItem[];
  total_users: number;
}

// ==================== Giveaway 関連 ====================

export interface GiveawayListItem {
  id: number;
  channel_id: string;
  message_id: string;
  prize: string;
  winner_count: number;
  participant_count: number;
  end_time: string;
  ended: boolean;
  created_at: string;
}

export interface GiveawayListResponse {
  active: GiveawayListItem[];
  ended: GiveawayListItem[];
  total_active: number;
  total_ended: number;
}

export interface GiveawayResponse {
  id: number;
  guild_id: string;
  channel_id: string;
  message_id: string;
  host_id: string;
  prize: string;
  winner_count: number;
  end_time: string;
  participants: string[];
  winners: string[];
  ended: boolean;
  created_at: string;
}

export interface GiveawayCreate {
  channel_id: string;
  prize: string;
  winner_count: number;
  duration_seconds: number;
}

export interface GiveawayEndResponse {
  id: number;
  prize: string;
  winners: string[];
  winner_names: string[];
}

export interface GiveawayRerollResponse {
  id: number;
  prize: string;
  new_winners: string[];
  new_winner_names: string[];
}

// ==================== Poll 関連 ====================

export interface PollListItem {
  id: number;
  channel_id: string;
  message_id: string;
  question: string;
  option_count: number;
  total_votes: number;
  multi_select: boolean;
  end_time: string | null;
  ended: boolean;
  created_at: string;
}

export interface PollListResponse {
  active: PollListItem[];
  ended: PollListItem[];
  total_active: number;
  total_ended: number;
}

export interface PollResponse {
  id: number;
  guild_id: string;
  channel_id: string;
  message_id: string;
  author_id: string;
  question: string;
  options: string[];
  votes: Record<string, string[]>;
  multi_select: boolean;
  end_time: string | null;
  ended: boolean;
  created_at: string;
}

export interface PollVoteResult {
  option: string;
  count: number;
  percentage: number;
  voters: string[];
}

export interface PollResultResponse {
  id: number;
  question: string;
  results: PollVoteResult[];
  total_votes: number;
  ended: boolean;
}

export interface PollCreate {
  channel_id: string;
  question: string;
  options: string[];
  multi_select: boolean;
  duration_seconds: number | null;
}
