/**
 * Ticket Command
 * Ticket system management with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  PermissionFlagsBits,
  ChannelType,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
  MessageFlags,
} from 'discord.js';
import { ticketSettingsService } from '../common/database/client.js';

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

    // Defer reply
    await interaction.deferReply();

    // Check permissions
    const guild = interaction.guild;
    if (!guild) return;

    const me = guild.members.me;
    if (!me?.permissions.has([PermissionFlagsBits.ManageChannels, PermissionFlagsBits.ManageRoles])) {
      await interaction.editReply({
        content: '❌ 権限が不足しています。BOTにチャンネル管理とロール管理の権限を付与してください。',
      });
      return;
    }

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

    // Create ticket panel with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🎫 サポートチケット')
    );

    const separator = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const descSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        'サポートが必要な場合は、下のボタンをクリックしてチケットを作成してください。\n\n' +
        '📝 **対応内容**\n' +
        '• 技術サポート\n' +
        '• 質問・問い合わせ\n' +
        '• 不具合報告\n' +
        '• その他のご相談\n\n' +
        'スタッフが迅速に対応いたします。'
      )
    );

    const panelContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.primary)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator)
      .addSectionComponents(descSection);

    // Create ticket button
    const createButton = new ButtonBuilder()
      .setCustomId('ticket_create')
      .setLabel('チケットを作成')
      .setStyle(ButtonStyle.Primary)
      .setEmoji('🎫');

    const buttonRow = new ActionRowBuilder<ButtonBuilder>().addComponents(createButton);

    // Send panel with button
    const panelChannel = guild.channels.cache.get(channel.id);
    if (!panelChannel?.isTextBased()) return;

    const panelMessage = await panelChannel.send({
      components: [panelContainer, buttonRow],
      flags: MessageFlags.IsComponentsV2,
    });

    // Save settings to database
    await ticketSettingsService.set({
      guildId,
      categoryId: category.id,
      notifyRoleId: role.id,
      panelChannelId: channel.id,
      panelMessageId: panelMessage.id,
    });

    // Complete - Build success message with Components v2
    const successHeader = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# ✅ チケットパネルを設置しました')
    );

    const successSep = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const successInfo = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `指定されたチャンネルにチケットパネルを設置しました。\n\n` +
        `📂 **カテゴリ:** <#${category.id}>\n` +
        `🔔 **通知先ロール:** <@&${role.id}>\n` +
        `📍 **パネルチャンネル:** <#${channel.id}>`
      )
    );

    const successContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(successHeader)
      .addSeparatorComponents(successSep)
      .addSectionComponents(successInfo);

    await interaction.editReply({
      content: '',
      embeds: [],
      components: [successContainer],
      flags: MessageFlags.IsComponentsV2,
    });
  }
}
