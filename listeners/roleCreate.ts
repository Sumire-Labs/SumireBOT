/**
 * Role Create Event Listener
 * Logs when roles are created
 */

import { Listener } from '@sapphire/framework';
import type { Role } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class RoleCreateListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'roleCreate',
    });
  }

  public async run(role: Role) {
    const guildId = role.guild.id;

    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('roleCreate')) return;

    const logChannel = role.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    const embed = this.container.embedBuilder.create({
      title: '🎨 ロールが作成されました',
      color: this.container.colors.success,
      fields: [
        createField(
          'ロール',
          `<@&${role.id}> (${role.name})`,
          true
        ),
        createField(
          'カラー',
          role.hexColor,
          true
        ),
      ],
      footer: '作成時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send role create log:', error);
    }
  }
}
