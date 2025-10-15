/**
 * Role Delete Event Listener
 * Logs when roles are deleted
 */

import { Listener } from '@sapphire/framework';
import type { Role } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

export class RoleDeleteListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'roleDelete',
    });
  }

  public async run(role: Role) {
    const guildId = role.guild.id;

    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('roleDelete')) return;

    const logChannel = role.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🎨 ロールが削除されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `🏷️ **ロール名:** ${role.name}\n` +
        `🆔 **ロールID:** \`${role.id}\`\n` +
        `🎨 **カラー:** ${role.hexColor}\n` +
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
      console.error('Failed to send role delete log:', error);
    }
  }
}
