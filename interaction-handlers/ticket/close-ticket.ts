/**
 * Close Ticket Interaction Handler
 * Handles ticket close button clicks with Components v2
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import {
  MessageFlags,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
} from 'discord.js';
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

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

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

    // Send closing message with Components v2
    const closedHeader = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🔒 チケットがクローズされました')
    );

    const separator = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const closedInfo = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `チケットが正常にクローズされました。\n\n` +
        `👤 **クローズしたユーザー:** <@${interaction.user.id}>\n` +
        `🆔 **チケットID:** #${ticket.id}\n` +
        `📅 **クローズ日時:** <t:${Math.floor(Date.now() / 1000)}:F>\n\n` +
        `⚠️ **このチャンネルは5秒後に削除されます。**`
      )
    );

    const closedContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.error)
      .addSectionComponents(closedHeader)
      .addSeparatorComponents(separator)
      .addSectionComponents(closedInfo);

    if (interaction.channel?.isTextBased() && 'send' in interaction.channel) {
      await interaction.channel.send({
        components: [closedContainer],
        flags: MessageFlags.IsComponentsV2,
      });
    }

    await interaction.editReply({ content: '✅ チケットをクローズしました。' });

    // Delete channel after 5 seconds
    setTimeout(async () => {
      const channel = interaction.channel;
      if (channel?.isDMBased() === false) {
        await channel.delete('Ticket closed');
      }
    }, 5000);
  }
}
