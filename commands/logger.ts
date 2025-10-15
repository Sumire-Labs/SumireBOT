/**
 * Logger Command
 * Logger system management with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  PermissionFlagsBits,
  ChannelType,
  MessageFlags,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

export class LoggerCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'logger',
      description: 'ロガーを設定します。',
    });
  }

  public override async registerApplicationCommands(registry: Command.Registry) {
    registry.registerChatInputCommand((builder) =>
      builder
        .setName('logger')
        .setDescription('ログシステムの管理')
        .addSubcommand((subcommand) =>
          subcommand
            .setName('setup')
            .setDescription('ログ出力先チャンネルを設定します')
            .addChannelOption((option) =>
              option
                .setName('channel')
                .setDescription('ログを出力するチャンネル')
                .setRequired(true)
                .addChannelTypes(ChannelType.GuildText)
            )
        )
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    );
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    const subcommand = interaction.options.getSubcommand();

    if (subcommand === 'setup') {
      await this.handleSetup(interaction);
    }
  }

  private async handleSetup(interaction: Command.ChatInputCommandInteraction) {
    const guildId = interaction.guildId;
    if (!guildId) return;

    const channel = interaction.options.getChannel('channel', true);

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    // Default enabled events
    const enabledEvents = [
      'messageDelete',
      'messageUpdate',
      'guildMemberAdd',
      'guildMemberRemove',
      'guildBanAdd',
      'guildBanRemove',
      'guildMemberUpdate',
      'roleCreate',
      'roleUpdate',
      'roleDelete',
      'channelCreate',
      'channelDelete',
    ];

    // Save settings
    await loggerSettingsService.set(guildId, channel.id, enabledEvents);

    // Success message with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# ✅ ログチャンネルを設定しました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const channelInfoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `ログ出力先チャンネルを設定しました。\n\n` +
        `📍 **ログチャンネル:** <#${channel.id}>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const eventsText = enabledEvents
      .map(event => {
        const eventNames: Record<string, string> = {
          'messageDelete': '📝 メッセージ削除',
          'messageUpdate': '✏️ メッセージ編集',
          'guildMemberAdd': '➕ メンバー参加',
          'guildMemberRemove': '➖ メンバー退出',
          'guildBanAdd': '🔨 Ban追加',
          'guildBanRemove': '🔓 Ban解除',
          'guildMemberUpdate': '👤 メンバー更新',
          'roleCreate': '🎭 ロール作成',
          'roleUpdate': '🎨 ロール更新',
          'roleDelete': '🗑️ ロール削除',
          'channelCreate': '📢 チャンネル作成',
          'channelDelete': '🚫 チャンネル削除',
        };
        return eventNames[event] || event;
      })
      .join('\n');

    const eventsSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📋 **記録するイベント:**\n${eventsText}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(channelInfoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(eventsSection);

    await interaction.editReply({
      components: [container],
      flags: MessageFlags.IsComponentsV2,
    });
  }
}
