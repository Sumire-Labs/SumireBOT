# SumireBot v2

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Runtime | Python 3.14.3 |
| Framework | discord.py 2.6.4 |
| Database | aiosqlite |
| Music | Wavelink 3.4.0 + Lavalink 4.x |
| Translation | googletrans-py |

## アーキテクチャ

```
sumire-bot-v2/
├── bot.py                 # エントリーポイント / Botクラス定義
├── config.yaml            # 設定ファイル (gitignore)
├── config.yaml.example    # 設定テンプレート
├── requirements.txt
│
├── cogs/                  # 機能モジュール (discord.py Cog)
│   ├── general.py         # /ping, /avatar
│   ├── logger.py          # サーバーログシステム
│   ├── ticket.py          # チケットシステム
│   ├── translate.py       # 翻訳機能
│   └── music.py           # 音楽プレイヤー
│
├── utils/                 # ユーティリティ
│   ├── config.py          # Config singleton (YAML読み込み)
│   ├── database.py        # Database singleton (aiosqlite)
│   ├── embeds.py          # Embed生成ヘルパー
│   ├── checks.py          # パーミッションデコレータ
│   └── logging.py         # ロギング設定
│
├── views/                 # discord.ui.View コンポーネント
│   ├── ticket_views.py    # チケットUI (Components V2)
│   └── persistent.py      # 永続的View管理
│
└── database/              # SQLiteファイル (自動生成)
```

## 設計方針

### Singleton パターン
`Config` と `Database` はシングルトンとして実装。どの Cog からも同一インスタンスにアクセス可能。

```python
# どこからでも同じインスタンスを取得
config = Config()
db = Database()
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
```
