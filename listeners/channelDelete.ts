/**
 * Channel Delete Event Listener
 * Logs when channels are deleted
 */

import { Listener } from '@sapphire/framework';
import type { DMChannel, GuildChannel } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

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
      0: 'テキストチャンネル',
      2: 'ボイスチャンネル',
      4: 'カテゴリー',
      5: 'アナウンスチャンネル',
      13: 'ステージチャンネル',
      15: 'フォーラムチャンネル',
    };

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 📢 チャンネルが削除されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `🏷️ **チャンネル名:** ${channel.name}\n` +
        `🆔 **チャンネルID:** \`${channel.id}\`\n` +
        `📁 **タイプ:** ${channelTypeMap[channel.type] || 'Unknown'}\n` +
        `🕒 **削除時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.error)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send channel delete log:', error);
    }
  }
}
