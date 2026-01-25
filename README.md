# SumireBot v2

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Runtime | Python  |
| Framework | discord.py |
| Database | aiosqlite |
| Music | Wavelink |
| Translation | googletrans-py |

## アーキテクチャ

```
sumirebot/
├── bot.py                     # エントリーポイント / Botクラス定義
├── config.yaml                # 設定ファイル (gitignore)
├── config.yaml.example        # 設定テンプレート
├── requirements.txt
├── start.ps1                  # 起動スクリプト (自動再起動対応)
│
├── cogs/                      # 機能モジュール (Mixin パターン)
│   ├── general/               # 一般コマンド (/ping, /avatar, /profile)
│   ├── utility/               # ユーティリティ (/translate, /confess, ログシステム)
│   ├── moderation/            # モデレーション (/ban, /kick, /timeout)
│   ├── music/                 # 音楽プレイヤー (/play, /skip, /leave, /loop)
│   ├── leveling/              # レベルシステム (/rank, /leaderboard)
│   ├── ticket/                # チケットシステム
│   ├── admin/                 # 管理者機能 (自動ロール, オーナーコマンド)
│   ├── giveaway/              # 抽選システム (/giveaway)
│   ├── poll/                  # 投票システム (/poll)
│   ├── star/                  # スター評価システム (/star, /starboard)
│   ├── embedfix/              # SNS埋め込み修正 (Instagram, Twitter/X, Medal.tv)
│   ├── teamshuffle/           # チーム分けくじ (/teamshuffle)
│   ├── warthunder/            # War Thunder BRルーレット (/wt-roulette)
│   └── wordcounter/           # 単語カウンター (/counter, /counterboard, /mycount)
│
├── utils/                     # ユーティリティ
│   ├── config.py              # Config singleton (YAML読み込み)
│   ├── database/              # Database モジュール (Mixin パターン)
│   │   ├── core.py            # 接続・トランザクション・テーブル初期化
│   │   ├── guild.py           # サーバー設定
│   │   ├── leveling.py        # レベルシステム
│   │   ├── star.py            # スター評価
│   │   ├── wordcounter.py     # 単語カウンター
│   │   └── ...                # 各機能のMixin
│   ├── embeds.py              # Embed生成ヘルパー
│   ├── checks.py              # パーミッションデコレータ
│   ├── logging.py             # ロギング設定
│   ├── status.py              # Botステータス管理
│   ├── time_parser.py         # 時間パース (1d12h30m → 秒)
│   └── cog_loader.py          # Cog動的ロード
│
├── views/                     # discord.ui.View コンポーネント
│   ├── common_views.py        # 共通View (Success/Error/Warning/Info)
│   ├── ticket_views.py        # チケットUI
│   ├── music_views.py         # 音楽プレイヤーUI
│   ├── star_views.py          # スター評価UI
│   ├── wordcounter_views.py   # 単語カウンターUI
│   ├── teamshuffle_views.py   # チーム分けくじUI
│   ├── giveaway_views.py      # 抽選UI
│   ├── poll_views.py          # 投票UI
│   └── persistent.py          # 永続的View管理
│
└── database/                  # SQLiteファイル (自動生成)
```

## 設計方針

### Singleton パターン
`Config` と `Database` はシングルトンとして実装。どの Cog からも同一インスタンスにアクセス可能。

```python
# どこからでも同じインスタンスを取得
config = Config()
db = Database()
```

### Mixin パターン
各 Cog は複数の Mixin から構成され、機能ごとにファイルを分離。

```python
class General(PingMixin, AvatarMixin, ProfileMixin, commands.Cog):
    pass
```

### マルチサーバー対応
全てのデータは `guild_id` をキーとして管理。サーバー間でデータが混在しない設計。

### UI
- **Components V2 (LayoutView)**: チケットパネル等のインタラクティブUI
- **従来の Embed + View**: ログ出力、情報表示 (Components V2 では Embed 使用不可のため)

## データベーススキーマ

```sql
-- サーバー設定
guild_settings (guild_id PK, language, created_at)

-- ログ設定
logger_settings (guild_id PK, channel_id, enabled, log_messages, log_channels, log_roles, log_members)

-- チケット設定
ticket_settings (guild_id PK, category_id, panel_channel_id, panel_message_id, ticket_counter)

-- チケット
tickets (id PK, guild_id, channel_id UNIQUE, user_id, ticket_number, category, status, created_at, closed_at)

-- 永続的View
persistent_views (id PK, guild_id, channel_id, message_id UNIQUE, view_type, data JSON, created_at)

-- 音楽設定
music_settings (guild_id PK, default_volume, dj_role_id, music_channel_id)

-- 自動ロール設定
autorole_settings (guild_id PK, human_role_id, bot_role_id, enabled)

-- レベルシステム設定
leveling_settings (guild_id PK, enabled, ignored_channels)

-- ユーザーレベルデータ
user_levels (id PK, guild_id, user_id UNIQUE, xp, level, last_xp_time, vc_time, vc_level, vc_join_time, reactions_given, reactions_received)

-- 抽選
giveaways (id PK, guild_id, channel_id, message_id UNIQUE, host_id, prize, winner_count, end_time, participants, winners, ended, created_at)

-- 投票
polls (id PK, guild_id, channel_id, message_id UNIQUE, author_id, question, options, votes, end_time, ended, created_at)

-- スター評価設定
star_settings (guild_id PK, enabled, target_channels JSON, weekly_report_channel_id, weekly_report_last_sent)

-- スターメッセージ
star_messages (id PK, guild_id, channel_id, message_id UNIQUE, author_id, star_count, starred_users JSON, created_at)

-- チーム分けくじ
team_shuffle_panels (id PK, guild_id, channel_id, message_id UNIQUE, creator_id, title, team_count, participants JSON, created_at)

-- 単語カウンター設定
wordcounter_settings (guild_id PK, enabled, words JSON, milestones JSON)

-- 単語カウント
wordcounter_counts (id PK, guild_id, user_id, word, count, last_milestone, updated_at, UNIQUE(guild_id, user_id, word))
```
