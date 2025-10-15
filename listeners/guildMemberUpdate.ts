/**
 * Guild Member Update Event Listener
 * Logs member updates (including timeouts)
 */

import { Listener } from '@sapphire/framework';
import type { GuildMember } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

export class GuildMemberUpdateListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'guildMemberUpdate',
    });
  }

  public async run(oldMember: GuildMember, newMember: GuildMember) {
    const guildId = newMember.guild.id;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('guildMemberUpdate')) return;

    // Check for timeout changes
    const oldTimeout = oldMember.communicationDisabledUntil;
    const newTimeout = newMember.communicationDisabledUntil;

    if (oldTimeout?.getTime() !== newTimeout?.getTime() && newTimeout && newTimeout > new Date()) {
      // Get log channel
      const logChannel = newMember.guild.channels.cache.get(settings.logChannelId);
      if (!logChannel?.isTextBased()) return;

      // Create log with Components v2
      const headerSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent('# ⏱️ タイムアウトが設定されました')
      );

      const separator1 = new SeparatorBuilder()
        .setDivider(true)
        .setSpacing(1);

      const infoSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(
          `👤 **メンバー:** <@${newMember.id}>\n` +
          `🏷️ **ユーザー名:** ${newMember.user.tag}\n` +
          `🆔 **ユーザーID:** \`${newMember.id}\`\n` +
          `🕒 **設定時刻:** <t:${Math.floor(Date.now() / 1000)}:F>\n` +
          `⏰ **解除時刻:** <t:${Math.floor(newTimeout.getTime() / 1000)}:F>`
        )
      );

      const container = new ContainerBuilder()
        .setAccentColor(this.container.colors.warning)
        .addSectionComponents(headerSection)
        .addSeparatorComponents(separator1)
        .addSectionComponents(infoSection);

      try {
        await logChannel.send({
          components: [container],
          flags: MessageFlags.IsComponentsV2,
        });
      } catch (error) {
        console.error('Failed to send guild member update log:', error);
      }
    }
  }
}
