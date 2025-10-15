/**
 * Poll Command
 * Create polls with reactions
 */

import { Command } from '@sapphire/framework';
import { SlashCommandBuilder } from 'discord.js';
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

    // Create poll embed
    const optionsText = options
      .map((option, index) => `${EMOJI_NUMBERS[index]} ${option}`)
      .join('\n');

    const embed = this.container.embedBuilder.create({
      title: `📊 ${question}`,
      description: optionsText,
      color: this.container.colors.primary,
      fields: endsAt
        ? [
            {
              name: '⏰ 投票期限',
              value: `<t:${Math.floor(endsAt.getTime() / 1000)}:R>`,
              inline: false,
            },
          ]
        : [],
      footer: `作成者: ${interaction.user.tag}`,
      timestamp: true,
    });

    // Send poll message
    await interaction.deferReply();
    const message = await interaction.editReply({ embeds: [embed] });

    // Add reactions
    for (let i = 0; i < options.length; i++) {
      await message.react(EMOJI_NUMBERS[i]);
    }

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

      // Count reactions
      const options = JSON.parse(poll.options) as string[];
      const results = await Promise.all(
        options.map(async (option, index) => {
          const reaction = message.reactions.cache.get(EMOJI_NUMBERS[index]);
          const count = reaction ? reaction.count - 1 : 0; // -1 to exclude bot's reaction
          return { option, count, emoji: EMOJI_NUMBERS[index] };
        })
      );

      // Sort by count
      results.sort((a, b) => b.count - a.count);

      // Create results embed
      const resultsText = results
        .map((r) => `${r.emoji} ${r.option}: **${r.count}票**`)
        .join('\n');

      const embed = this.container.embedBuilder.create({
        title: `📊 ${poll.question} [終了]`,
        description: resultsText,
        color: this.container.colors.success,
        fields: [
          {
            name: '🏆 最多得票',
            value: `${results[0].emoji} ${results[0].option} (${results[0].count}票)`,
            inline: false,
          },
        ],
        footer: `作成者: ${message.author?.tag || 'Unknown'}`,
        timestamp: true,
      });

      await message.edit({ embeds: [embed] });
      await pollService.close(messageId);
    } catch (error) {
      console.error('Failed to close poll:', error);
    }
  }
}
