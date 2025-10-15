/**
 * Message Update Event Listener
 * Logs edited messages
 */

import { Listener } from '@sapphire/framework';
import type { Message } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField, truncate } from '../common/design/components.js';

export class MessageUpdateListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'messageUpdate',
    });
  }

  public async run(oldMessage: Message, newMessage: Message) {
    // Fetch partial messages
    if (oldMessage.partial) {
      try {
        await oldMessage.fetch();
      } catch {
        return; // Message was deleted or inaccessible
      }
    }
    if (newMessage.partial) {
      try {
        await newMessage.fetch();
      } catch {
        return; // Message was deleted or inaccessible
      }
    }

    if (!newMessage.guild || newMessage.author?.bot) return;
    if (oldMessage.content === newMessage.content) return;

    const guildId = newMessage.guild.id;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('messageUpdate')) return;

    // Get log channel
    const logChannel = newMessage.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '✏️ メッセージが編集されました',
      color: this.container.colors.warning,
      fields: [
        createField(
          '送信者',
          `<@${newMessage.author.id}>`,
          true
        ),
        createField(
          'チャンネル',
          `<#${newMessage.channelId}>`,
          true
        ),
        createField(
          '編集前',
          truncate(oldMessage.content || '*内容なし*', 1000),
          false
        ),
        createField(
          '編集後',
          truncate(newMessage.content || '*内容なし*', 1000),
          false
        ),
      ],
      footer: '編集時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send message update log:', error);
    }
  }
}
