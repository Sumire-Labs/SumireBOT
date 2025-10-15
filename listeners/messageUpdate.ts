/**
 * Message Update Event Listener
 * Logs edited messages with Components v2
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
import { truncate } from '../common/design/components.js';

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

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# ✏️ メッセージが編集されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **送信者:** <@${newMessage.author.id}>\n` +
        `📍 **チャンネル:** <#${newMessage.channelId}>\n` +
        `🔗 **[メッセージへ移動](${newMessage.url})**\n` +
        `🕒 **編集時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const beforeSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📝 **編集前:**\n${truncate(oldMessage.content || '*内容なし*', 1000)}`
      )
    );

    const separator3 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const afterSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `✅ **編集後:**\n${truncate(newMessage.content || '*内容なし*', 1000)}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.warning)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(beforeSection)
      .addSeparatorComponents(separator3)
      .addSectionComponents(afterSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send message update log:', error);
    }
  }
}
