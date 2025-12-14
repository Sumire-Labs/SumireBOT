/**
 * Logger Command
 * Logger system management
 */

import { Command } from '@sapphire/framework';
import { PermissionFlagsBits, ChannelType, MessageFlags } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class LoggerCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'logger',
      description: 'ロガーを設定します。',
      requiredUserPermissions: ['Administrator'],
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
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
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

    // Success message
    const successEmbed = this.container.embedBuilder.success(
      'ログチャンネルを設定しました',
      '以下のチャンネルにログが出力されます。'
    );

    successEmbed.addFields([
      createField(
        'ログチャンネル',
        `<#${channel.id}>`,
        false
      ),
    ]);

    await interaction.editReply({ embeds: [successEmbed] });
  }
}
