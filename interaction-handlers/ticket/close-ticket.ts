/**
 * Close Ticket Interaction Handler
 * Handles ticket close button clicks
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import { ticketService } from '../../common/database/client.js';

export class CloseTicketHandler extends InteractionHandler {
  public constructor(ctx: InteractionHandler.LoaderContext, options: InteractionHandler.Options) {
    super(ctx, {
      ...options,
      interactionHandlerType: InteractionHandlerTypes.Button,
    });
  }

  public override parse(interaction: ButtonInteraction) {
    if (interaction.customId !== 'ticket_close') return this.none();
    return this.some();
  }

  public override async run(interaction: ButtonInteraction) {
    const guildId = interaction.guildId;
    const channelId = interaction.channelId;

    if (!guildId) return;

    await interaction.deferReply({ ephemeral: true });

    // Check if this channel is a ticket
    const ticket = await ticketService.get(channelId);
    if (!ticket) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'このチャンネルはチケットではありません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Check if ticket is already closed
    if (ticket.status === 'closed') {
      const embed = this.container.embedBuilder.warning(
        '警告',
        'このチケットは既にクローズされています。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Close ticket in database
    await ticketService.close(channelId);

    // Send closing message
    const closedEmbed = this.container.embedBuilder.create({
      title: 'チケットがクローズされました',
      description: `クローズしたユーザー: <@${interaction.user.id}>\n\nこのチャンネルは5秒後に削除されます。`,
      color: this.container.colors.error,
      timestamp: true,
    });

    await interaction.editReply({ embeds: [closedEmbed] });

    // Delete channel after 5 seconds
    setTimeout(async () => {
      const channel = interaction.channel;
      if (channel?.isDMBased() === false) {
        await channel.delete('Ticket closed');
      }
    }, 5000);
  }
}
