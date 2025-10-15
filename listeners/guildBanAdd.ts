/**
 * Guild Ban Add Event Listener
 * Logs when members are banned
 */

import { Listener } from '@sapphire/framework';
import type { GuildBan } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

export class GuildBanAddListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'guildBanAdd',
    });
  }

  public async run(ban: GuildBan) {
    const guildId = ban.guild.id;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('guildBanAdd')) return;

    // Get log channel
    const logChannel = ban.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🔨 メンバーがBANされました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **メンバー:** <@${ban.user.id}>\n` +
        `🏷️ **ユーザー名:** ${ban.user.tag}\n` +
        `🆔 **ユーザーID:** \`${ban.user.id}\`\n` +
        `🕒 **BAN時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const reasonSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📝 **理由:**\n${ban.reason || '*理由なし*'}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.error)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(reasonSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send guild ban add log:', error);
    }
  }
}
