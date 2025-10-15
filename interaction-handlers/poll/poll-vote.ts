/**
 * Poll Vote Interaction Handler
 * Handles poll voting button clicks
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { pollService } from '../../common/database/client.js';

const EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'];

export class PollVoteHandler extends InteractionHandler {
  public constructor(ctx: InteractionHandler.LoaderContext, options: InteractionHandler.Options) {
    super(ctx, {
      ...options,
      interactionHandlerType: InteractionHandlerTypes.Button,
    });
  }

  public override parse(interaction: ButtonInteraction) {
    if (!interaction.customId.startsWith('poll_vote_')) return this.none();
    return this.some();
  }

  public override async run(interaction: ButtonInteraction) {
    const optionIndex = parseInt(interaction.customId.replace('poll_vote_', ''));
    const messageId = interaction.message.id;
    const userId = interaction.user.id;

    // Get poll from database
    const poll = await pollService.get(messageId);
    if (!poll) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        '投票が見つかりませんでした。'
      );
      await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
      return;
    }

    if (poll.status === 'closed') {
      const embed = this.container.embedBuilder.warning(
        '警告',
        'この投票は終了しています。'
      );
      await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
      return;
    }

    // Record vote
    const result = await pollService.vote(messageId, userId, optionIndex);
    if (!result) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        '投票に失敗しました。'
      );
      await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
      return;
    }

    // Update poll message with new vote counts
    const options = JSON.parse(poll.options) as string[];
    const { votes } = result;

    // Build header section with question
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(`# 📊 ${poll.question}`)
    );

    // Build separators
    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    // Build info section
    const endsAt = poll.endsAt ? new Date(poll.endsAt) : null;
    const creator = await this.container.client.users.fetch(poll.creatorId).catch(() => null);
    const infoText = endsAt
      ? `⏰ **投票期限:** <t:${Math.floor(endsAt.getTime() / 1000)}:R>\n👤 **作成者:** ${creator?.tag || 'Unknown'}`
      : `👤 **作成者:** ${creator?.tag || 'Unknown'}`;

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(infoText)
    );

    // Build options section with updated vote counts
    const optionsText = options
      .map((option, index) => {
        const count = votes[index.toString()] || 0;
        return `${EMOJI_NUMBERS[index]} **${option}**: ${count}票`;
      })
      .join('\n');

    const optionsSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(optionsText)
    );

    // Build container
    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.primary)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(optionsSection);

    // Update the message
    await interaction.update({
      components: [container, ...interaction.message.components.slice(1)],
    });
  }
}
