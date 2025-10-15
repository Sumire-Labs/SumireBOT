/**
 * Message Delete Event Listener
 * Logs deleted messages with Components v2
 */

import { Listener } from '@sapphire/framework';
import type { Message } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

export class MessageDeleteListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'messageDelete',
    });
  }

  public async run(message: Message) {
    // Partial messages cannot be fetched after deletion, so skip if essential data is missing
    if (message.partial && !message.author) return;

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

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 📝 メッセージが削除されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **送信者:** ${message.author ? `<@${message.author.id}>` : 'Unknown'}\n` +
        `📍 **チャンネル:** <#${message.channelId}>\n` +
        `🆔 **メッセージID:** \`${message.id}\`\n` +
        `🕒 **削除時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const contentSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📄 **メッセージ内容:**\n${message.content || '*内容なし（画像/添付ファイルのみの可能性）*'}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.error)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(contentSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send message delete log:', error);
    }
  }
}
