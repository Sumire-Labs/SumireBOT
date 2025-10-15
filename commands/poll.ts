/**
 * Poll Command
 * Create polls with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  SlashCommandBuilder,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
  MessageFlags,
} from 'discord.js';
import { pollService } from '../common/database/client.js';

const EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'];

export class PollCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'poll',
      description: '投票を作成',
    });
  }

  public override registerApplicationCommands(registry: Command.Registry) {
    const command = new SlashCommandBuilder()
      .setName(this.name)
      .setDescription(this.description)
      .addStringOption((option) =>
        option
          .setName('question')
          .setDescription('投票の質問')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('option1')
          .setDescription('選択肢1')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('option2')
          .setDescription('選択肢2')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('option3')
          .setDescription('選択肢3')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option4')
          .setDescription('選択肢4')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option5')
          .setDescription('選択肢5')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option6')
          .setDescription('選択肢6')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option7')
          .setDescription('選択肢7')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option8')
          .setDescription('選択肢8')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option9')
          .setDescription('選択肢9')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('option10')
          .setDescription('選択肢10')
          .setRequired(false)
      )
      .addIntegerOption((option) =>
        option
          .setName('duration')
          .setDescription('投票期間（分）省略で無期限')
          .setRequired(false)
          .setMinValue(1)
      );

    registry.registerChatInputCommand(command);
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    const guildId = interaction.guildId;
    const channelId = interaction.channelId;
    if (!guildId || !channelId) return;

    const question = interaction.options.getString('question', true);
    const duration = interaction.options.getInteger('duration');

    // Collect all options
    const options: string[] = [];
    for (let i = 1; i <= 10; i++) {
      const option = interaction.options.getString(`option${i}`);
      if (option) options.push(option);
    }

    if (options.length < 2) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        '最低2つの選択肢が必要です。'
      );
      await interaction.reply({ embeds: [embed], flags: [4] }); // Ephemeral
      return;
    }

    if (options.length > 10) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        '選択肢は最大10個までです。'
      );
      await interaction.reply({ embeds: [embed], flags: [4] }); // Ephemeral
      return;
    }

    // Calculate end time if duration is specified
    const endsAt = duration ? new Date(Date.now() + duration * 60 * 1000) : null;

    // Create poll with Components v2
    await interaction.deferReply();

    // Build header section with question
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(`# 📊 ${question}`)
    );

    // Build separators
    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    // Build info section
    const infoText = endsAt
      ? `⏰ **投票期限:** <t:${Math.floor(endsAt.getTime() / 1000)}:R>\n👤 **作成者:** ${interaction.user.tag}`
      : `👤 **作成者:** ${interaction.user.tag}`;

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(infoText)
    );

    // Build options section
    const optionsText = options
      .map((option, index) => `${EMOJI_NUMBERS[index]} **${option}**: 0票`)
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

    // Create buttons for voting
    const buttonRows: ActionRowBuilder<ButtonBuilder>[] = [];
    for (let i = 0; i < options.length; i += 5) {
      const row = new ActionRowBuilder<ButtonBuilder>();
      for (let j = i; j < Math.min(i + 5, options.length); j++) {
        const button = new ButtonBuilder()
          .setCustomId(`poll_vote_${j}`)
          .setLabel(EMOJI_NUMBERS[j])
          .setStyle(ButtonStyle.Primary);
        row.addComponents(button);
      }
      buttonRows.push(row);
    }

    // Send poll message
    const message = await interaction.editReply({
      components: [container, ...buttonRows],
      flags: MessageFlags.IsComponentsV2,
    });

    // Save poll to database
    await pollService.create({
      guildId,
      channelId,
      messageId: message.id,
      creatorId: interaction.user.id,
      question,
      options: JSON.stringify(options),
      endsAt,
      status: 'active',
    });

    // Schedule poll closing if duration is specified
    if (endsAt) {
      const timeUntilEnd = endsAt.getTime() - Date.now();
      setTimeout(async () => {
        await this.closePoll(message.id);
      }, timeUntilEnd);
    }
  }

  private async closePoll(messageId: string) {
    try {
      const poll = await pollService.get(messageId);
      if (!poll || poll.status === 'closed') return;

      // Get the message
      const channel = await this.container.client.channels.fetch(poll.channelId);
      if (!channel?.isTextBased()) return;

      const message = await channel.messages.fetch(messageId);
      if (!message) return;

      // Get vote counts from database (assuming we store them)
      const options = JSON.parse(poll.options) as string[];
      const votes = JSON.parse(poll.votes || '{}') as Record<string, number>;

      const results = options.map((option, index) => ({
        option,
        count: votes[index.toString()] || 0,
        emoji: EMOJI_NUMBERS[index],
      }));

      // Sort by count
      results.sort((a, b) => b.count - a.count);

      // Create results with Components v2
      const headerSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(`# 📊 ${poll.question} [終了]`)
      );

      const sep1 = new SeparatorBuilder()
        .setDivider(true)
        .setSpacing(1);

      const sep2 = new SeparatorBuilder()
        .setDivider(true)
        .setSpacing(1);

      // Build results text
      const resultsText = results
        .map((r) => `${r.emoji} **${r.option}**: ${r.count}票`)
        .join('\n');

      const resultsSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(resultsText)
      );

      // Winner section
      const winnerSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(
          `🏆 **最多得票**\n${results[0].emoji} ${results[0].option} (${results[0].count}票)`
        )
      );

      const container = new ContainerBuilder()
        .setAccentColor(this.container.colors.success)
        .addSectionComponents(headerSection)
        .addSeparatorComponents(sep1)
        .addSectionComponents(resultsSection)
        .addSeparatorComponents(sep2)
        .addSectionComponents(winnerSection);

      await message.edit({ components: [container] });
      await pollService.close(messageId);
    } catch (error) {
      console.error('Failed to close poll:', error);
    }
  }
}
