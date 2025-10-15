/**
 * Guild Ban Remove Event Listener
 * Logs when bans are removed
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

export class GuildBanRemoveListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'guildBanRemove',
    });
  }

  public async run(ban: GuildBan) {
    const guildId = ban.guild.id;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('guildBanRemove')) return;

    // Get log channel
    const logChannel = ban.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🔓 BANが解除されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **メンバー:** <@${ban.user.id}>\n` +
        `🏷️ **ユーザー名:** ${ban.user.tag}\n` +
        `🆔 **ユーザーID:** \`${ban.user.id}\`\n` +
        `🕒 **BAN解除時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
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
      console.error('Failed to send guild ban remove log:', error);
    }
  }
}
