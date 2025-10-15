/**
 * Create Ticket Interaction Handler
 * Handles ticket creation button clicks with Components v2
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import {
  ChannelType,
  PermissionFlagsBits,
  MessageFlags,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
} from 'discord.js';
import { ticketSettingsService, ticketService } from '../../common/database/client.js';

export class CreateTicketHandler extends InteractionHandler {
  public constructor(ctx: InteractionHandler.LoaderContext, options: InteractionHandler.Options) {
    super(ctx, {
      ...options,
      interactionHandlerType: InteractionHandlerTypes.Button,
    });
  }

  public override parse(interaction: ButtonInteraction) {
    if (interaction.customId !== 'ticket_create') return this.none();
    return this.some();
  }

  public override async run(interaction: ButtonInteraction) {
    const guildId = interaction.guildId;
    const userId = interaction.user.id;

    if (!guildId) return;

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const guild = interaction.guild;
    if (!guild) return;

    // Get ticket settings
    const settings = await ticketSettingsService.get(guildId);
    if (!settings) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'チケットシステムが設定されていません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Create ticket channel
    const category = guild.channels.cache.get(settings.categoryId);
    if (!category || category.type !== ChannelType.GuildCategory) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'チケットカテゴリが見つかりません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Check if user already has an open ticket
    const existingTicket = await ticketService.getByUserId(userId, guildId);
    if (existingTicket) {
      const embed = this.container.embedBuilder.warning(
        '警告',
        `既にチケットを作成済みです: <#${existingTicket.channelId}>`
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    const me = guild.members.me;
    if (!me) return;

    // Create ticket channel
    const ticketChannel = await guild.channels.create({
      name: `ticket-${interaction.user.username}`,
      type: ChannelType.GuildText,
      parent: category.id,
      permissionOverwrites: [
        {
          id: guild.id,
          deny: [PermissionFlagsBits.ViewChannel],
        },
        {
          id: userId,
          allow: [
            PermissionFlagsBits.ViewChannel,
            PermissionFlagsBits.SendMessages,
            PermissionFlagsBits.ReadMessageHistory,
          ],
        },
        {
          id: me.id,
          allow: [
            PermissionFlagsBits.ViewChannel,
            PermissionFlagsBits.SendMessages,
            PermissionFlagsBits.ManageChannels,
          ],
        },
      ],
    });

    // Add notify role permissions
    if (settings.notifyRoleId) {
      await ticketChannel.permissionOverwrites.create(settings.notifyRoleId, {
        ViewChannel: true,
        SendMessages: true,
        ReadMessageHistory: true,
      });
    }

    // Save ticket to database
    const ticket = await ticketService.create({
      guildId,
      channelId: ticketChannel.id,
      userId,
      status: 'open',
    });

    // Send welcome message in ticket channel with Components v2
    const welcomeHeader = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🎫 チケット作成')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const welcomeInfo = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `チケットが作成されました。\n\n` +
        `👤 **作成者:** <@${userId}>\n` +
        `🆔 **チケットID:** #${ticket.id}\n` +
        `📅 **作成日時:** <t:${Math.floor(Date.now() / 1000)}:F>\n\n` +
        `スタッフが対応するまでお待ちください。\n` +
        `質問や問題の詳細を記載してください。`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const instructionsSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `💡 **ヒント**\n` +
        `• できるだけ詳しく状況を説明してください\n` +
        `• スクリーンショットがあると理解しやすくなります\n` +
        `• 問題が解決したら、下のボタンでチケットをクローズできます`
      )
    );

    const welcomeContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.primary)
      .addSectionComponents(welcomeHeader)
      .addSeparatorComponents(separator1)
      .addSectionComponents(welcomeInfo)
      .addSeparatorComponents(separator2)
      .addSectionComponents(instructionsSection);

    // Create close button
    const closeButton = new ButtonBuilder()
      .setCustomId('ticket_close')
      .setLabel('チケットをクローズ')
      .setStyle(ButtonStyle.Danger)
      .setEmoji('🔒');

    const buttonRow = new ActionRowBuilder<ButtonBuilder>().addComponents(closeButton);

    await ticketChannel.send({
      content: settings.notifyRoleId ? `<@${userId}> <@&${settings.notifyRoleId}>` : `<@${userId}>`,
      components: [welcomeContainer, buttonRow],
      flags: MessageFlags.IsComponentsV2,
    });

    // Send success message
    const successEmbed = this.container.embedBuilder.success(
      '完了',
      `チケットを作成しました: <#${ticketChannel.id}>`
    );

    await interaction.editReply({ embeds: [successEmbed] });
  }
}
