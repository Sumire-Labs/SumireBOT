/**
 * Role Delete Event Listener
 * Logs when roles are deleted
 */

import { Listener } from '@sapphire/framework';
import type { Role } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

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

    const embed = this.container.embedBuilder.create({
      title: '🎨 ロールが削除されました',
      color: this.container.colors.error,
      fields: [
        createField(
          'ロール',
          role.name,
          false
        ),
      ],
      footer: '削除時刻',
      timestamp: true,
    });

    await logChannel.send({ embeds: [embed] });
  }
}
