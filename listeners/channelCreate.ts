/**
 * Channel Create Event Listener
 * Logs when channels are created
 */

import { Listener } from '@sapphire/framework';
import type { GuildChannel } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

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
      0: 'テキストチャンネル',
      2: 'ボイスチャンネル',
      4: 'カテゴリー',
      5: 'アナウンスチャンネル',
      13: 'ステージチャンネル',
      15: 'フォーラムチャンネル',
    };

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 📢 チャンネルが作成されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📺 **チャンネル:** <#${channel.id}>\n` +
        `🏷️ **チャンネル名:** ${channel.name}\n` +
        `🆔 **チャンネルID:** \`${channel.id}\`\n` +
        `📁 **タイプ:** ${channelTypeMap[channel.type] || 'Unknown'}\n` +
        `🕒 **作成時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send channel create log:', error);
    }
  }
}
