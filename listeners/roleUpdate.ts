/**
 * Role Update Event Listener
 * Logs when roles are updated
 */

import { Listener } from '@sapphire/framework';
import type { Role } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class RoleUpdateListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'roleUpdate',
    });
  }

  public async run(oldRole: Role, newRole: Role) {
    const guildId = newRole.guild.id;

    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('roleUpdate')) return;

    const logChannel = newRole.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Detect changes
    const changes: string[] = [];

    if (oldRole.name !== newRole.name) {
      changes.push(`**Name:** ${oldRole.name} → ${newRole.name}`);
    }

    if (oldRole.hexColor !== newRole.hexColor) {
      changes.push(`**Color:** ${oldRole.hexColor} → ${newRole.hexColor}`);
    }

    if (oldRole.permissions.bitfield !== newRole.permissions.bitfield) {
      changes.push(`**Permissions:** Updated`);
    }

    if (oldRole.hoist !== newRole.hoist) {
      changes.push(`**Display separately:** ${oldRole.hoist ? 'Yes' : 'No'} → ${newRole.hoist ? 'Yes' : 'No'}`);
    }

    if (oldRole.mentionable !== newRole.mentionable) {
      changes.push(`**Mentionable:** ${oldRole.mentionable ? 'Yes' : 'No'} → ${newRole.mentionable ? 'Yes' : 'No'}`);
    }

    // If no significant changes, don't log
    if (changes.length === 0) return;

    const embed = this.container.embedBuilder.create({
      title: '🎨 ロールが更新されました',
      color: this.container.colors.info,
      fields: [
        createField(
          'ロール',
          `<@&${newRole.id}> (${newRole.name})`,
          false
        ),
        createField(
          '変更内容',
          changes.join('\n'),
          false
        ),
      ],
      footer: '更新時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send role update log:', error);
    }
  }
}
