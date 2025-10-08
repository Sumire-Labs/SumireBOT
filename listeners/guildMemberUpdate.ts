/**
 * Guild Member Update Event Listener
 * Logs member updates (including timeouts)
 */

import { Listener } from '@sapphire/framework';
import type { GuildMember } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField, formatTimestamp } from '../common/design/components.js';

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

      // Create timeout log embed
      const embed = this.container.embedBuilder.create({
        title: '⏱️ タイムアウトが設定されました',
        color: this.container.colors.warning,
        fields: [
          createField(
            'メンバー',
            `<@${newMember.id}> (${newMember.user.tag})`,
            false
          ),
          createField(
            '解除時刻',
            formatTimestamp(newTimeout, 'F'),
            true
          ),
        ],
        thumbnail: newMember.user.displayAvatarURL(),
        timestamp: true,
      });

      await logChannel.send({ embeds: [embed] });
    }
  }
}
