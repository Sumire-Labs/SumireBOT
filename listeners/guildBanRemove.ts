/**
 * Guild Ban Remove Event Listener
 * Logs when bans are removed
 */

import { Listener } from '@sapphire/framework';
import type { GuildBan } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

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

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '🔓 BANが解除されました',
      color: this.container.colors.success,
      fields: [
        createField(
          'メンバー',
          `<@${ban.user.id}> (${ban.user.tag})`,
          false
        ),
      ],
      thumbnail: ban.user.displayAvatarURL(),
      footer: 'BAN解除時刻',
      timestamp: true,
    });

    try {
      await logChannel.send({ embeds: [embed] });
    } catch (error) {
      console.error('Failed to send guild ban remove log:', error);
    }
  }
}
