/**
 * Channel Delete Event Listener
 * Logs when channels are deleted
 */

import { Listener } from '@sapphire/framework';
import type { DMChannel, GuildChannel } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class ChannelDeleteListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'channelDelete',
    });
  }

  public async run(channel: DMChannel | GuildChannel) {
    if (channel.isDMBased()) return;

    const guildId = channel.guild.id;

    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('channelDelete')) return;

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
      title: '📢 チャンネルが削除されました',
      color: this.container.colors.error,
      fields: [
        createField(
          'チャンネル',
          channel.name,
          true
        ),
        createField(
          'タイプ',
          channelTypeMap[channel.type] || 'Unknown',
          true
        ),
      ],
      footer: '削除時刻',
      timestamp: true,
    });

    await logChannel.send({ embeds: [embed] });
  }
}
