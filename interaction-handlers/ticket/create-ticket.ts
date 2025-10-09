/**
 * Create Ticket Interaction Handler
 * Handles ticket creation button clicks
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import { ChannelType, PermissionFlagsBits, MessageFlags } from 'discord.js';
import { ticketSettingsService, ticketService } from '../../common/database/client.js';
import { ButtonPresets, createButtonRow } from '../../common/design/buttons.js';

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

    // Send welcome message in ticket channel
    const welcomeEmbed = this.container.embedBuilder.create({
      title: 'チケット作成',
      description: 'チケットが作成されました。\n\nスタッフが対応するまでお待ちください。',
      color: this.container.colors.primary,
      footer: `チケットID #${ticket.id}`,
      timestamp: true,
    });

    await ticketChannel.send({
      content: settings.notifyRoleId ? `<@${userId}> <@&${settings.notifyRoleId}>` : `<@${userId}>`,
      embeds: [welcomeEmbed],
      components: [createButtonRow(ButtonPresets.closeTicket())],
    });

    // Send success message
    const successEmbed = this.container.embedBuilder.success(
      '完了',
      `チケットを作成しました: <#${ticketChannel.id}>`
    );

    await interaction.editReply({ embeds: [successEmbed] });
  }
}
