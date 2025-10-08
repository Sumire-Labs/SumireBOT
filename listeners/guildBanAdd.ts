/**
 * Guild Ban Add Event Listener
 * Logs when members are banned
 */

import { Listener } from '@sapphire/framework';
import type { GuildBan } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

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

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '🔨 メンバーがBANされました',
      color: this.container.colors.error,
      fields: [
        createField(
          'メンバー',
          `<@${ban.user.id}> (${ban.user.tag})`,
          false
        ),
        createField(
          '理由',
          ban.reason || '理由なし',
          false
        ),
      ],
      thumbnail: ban.user.displayAvatarURL(),
      footer: 'BAN時刻',
      timestamp: true,
    });

    await logChannel.send({ embeds: [embed] });
  }
}
