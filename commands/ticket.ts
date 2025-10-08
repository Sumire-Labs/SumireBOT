/**
 * Ticket Command
 * Ticket system management
 */

import { Command } from '@sapphire/framework';
import { PermissionFlagsBits, ChannelType } from 'discord.js';
import { ticketSettingsService } from '../common/database/client.js';
import { createProgressTracker } from '../common/design/progress.js';
import { createField } from '../common/design/components.js';
import { ButtonPresets, createButtonRow } from '../common/design/buttons.js';

export class TicketCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'ticket',
      description: 'Ticketツールのパネルを設置します。',
    });
  }

  public override async registerApplicationCommands(registry: Command.Registry) {
    registry.registerChatInputCommand((builder) =>
      builder
        .setName('ticket')
        .setDescription('チケットシステムの管理')
        .addSubcommand((subcommand) =>
          subcommand
            .setName('setup')
            .setDescription('チケットパネルを設置します')
            .addChannelOption((option) =>
              option
                .setName('channel')
                .setDescription('パネルを設置するチャンネル')
                .setRequired(true)
                .addChannelTypes(ChannelType.GuildText)
            )
            .addRoleOption((option) =>
              option
                .setName('role')
                .setDescription('通知先のロール')
                .setRequired(true)
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
    const role = interaction.options.getRole('role', true);

    // Create progress tracker
    const progress = createProgressTracker(
      interaction,
      [
        {
          title: '設定を確認中...',
        },
        {
          title: 'チケットカテゴリを作成中...',
        },
        {
          title: 'パネルを設置中...',
        },
      ],
      this.container.embedBuilder
    );

    await progress.start();

    // Check permissions
    const guild = interaction.guild;
    if (!guild) return;

    const me = guild.members.me;
    if (!me?.permissions.has([PermissionFlagsBits.ManageChannels, PermissionFlagsBits.ManageRoles])) {
      await progress.fail('権限が不足しています');
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
    await progress.next();

    // Create or get ticket category
    let category = guild.channels.cache.find(
      (c) => c.type === ChannelType.GuildCategory && c.name === '🎫 Tickets'
    );

    if (!category) {
      category = await guild.channels.create({
        name: '🎫 Tickets',
        type: ChannelType.GuildCategory,
        permissionOverwrites: [
          {
            id: guild.id,
            deny: [PermissionFlagsBits.ViewChannel],
          },
          {
            id: me.id,
            allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.ManageChannels],
          },
        ],
      });
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
    await progress.next();

    // Create ticket panel embed
    const panelEmbed = this.container.embedBuilder.create({
      title: '🎫 サポートチケット',
      description: 'サポートが必要な場合は、下のボタンをクリックしてチケットを作成してください。\n\nスタッフが対応いたします。',
      color: this.container.colors.primary,
    });

    // Send panel with button
    const panelChannel = guild.channels.cache.get(channel.id);
    if (!panelChannel?.isTextBased()) return;

    const panelMessage = await panelChannel.send({
      embeds: [panelEmbed],
      components: [createButtonRow(ButtonPresets.createTicket())],
    });

    // Save settings to database
    await ticketSettingsService.set({
      guildId,
      categoryId: category.id,
      notifyRoleId: role.id,
      panelChannelId: channel.id,
      panelMessageId: panelMessage.id,
    });

    await new Promise((resolve) => setTimeout(resolve, 500));

    // Complete
    const successEmbed = this.container.embedBuilder.success(
      'チケットパネルを設置しました',
      '指定されたチャンネルにチケットパネルを設置しました。'
    );

    successEmbed.addFields([
      createField(
        'カテゴリ',
        `<#${category.id}>`,
        true
      ),
      createField(
        '通知先ロール',
        `<@&${role.id}>`,
        true
      ),
    ]);

    await progress.update(successEmbed);
  }
}
