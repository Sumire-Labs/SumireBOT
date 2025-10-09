/**
 * Channel Create Event Listener
 * Logs when channels are created
 */

import { Listener } from '@sapphire/framework';
import type { GuildChannel } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class ChannelCreateListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'channelCreate',
    });
  }

  public async run(channel: GuildChannel) {
    const guildId = channel.guild.id;

    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('channelCreate')) return;

    const logChannel = channel.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    const channelTypeMap: Record<number, string> = {
      0: 'Text',
      2: 'Voice',
      4: 'Category',
      5: 'Announcement',
      13: 'Stage',
      15: 'Forum',
    };

    const embed = this.container.embedBuilder.create({
      title: '📢 チャンネルが作成されました',
      color: this.container.colors.success,
      fields: [
        createField(
          'チャンネル',
          `<#${channel.id}> (${channel.name})`,
          true
        ),
        createField(
          'タイプ',
          channelTypeMap[channel.type] || 'Unknown',
          true
        ),
      ],
      footer: '作成時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send channel create log:', error);
    }
  }
}
