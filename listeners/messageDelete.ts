/**
 * Message Delete Event Listener
 * Logs deleted messages
 */

import { Listener } from '@sapphire/framework';
import type { Message } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class MessageDeleteListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'messageDelete',
    });
  }

  public async run(message: Message) {
    if (!message.guild || message.author?.bot) return;

    const guildId = message.guild.id;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('messageDelete')) return;

    // Get log channel
    const logChannel = message.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '📝 メッセージが削除されました',
      color: this.container.colors.error,
      fields: [
        createField(
          '送信者',
          message.author ? `<@${message.author.id}>` : 'Unknown',
          true
        ),
        createField(
          'チャンネル',
          `<#${message.channelId}>`,
          true
        ),
        createField(
          '内容',
          message.content || '*内容なし*',
          false
        ),
      ],
      footer: '削除時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send message delete log:', error);
    }
  }
}
