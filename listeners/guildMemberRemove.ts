/**
 * Guild Member Remove Event Listener
 * Logs when members leave
 */

import { Listener } from '@sapphire/framework';
import type { GuildMember } from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

export class GuildMemberRemoveListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'guildMemberRemove',
    });
  }

  public async run(member: GuildMember) {
    const guildId = member.guild.id;

    // BOT自身の退出はログしない（サーバーにアクセスできないため）
    if (member.id === this.container.client.user?.id) return;

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('guildMemberRemove')) return;

    // Get log channel
    const logChannel = member.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Get member roles
    const roles = member.roles.cache
      .filter((r) => r.id !== member.guild.id)
      .map((r) => `<@&${r.id}>`)
      .join(', ') || 'None';

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '👋 メンバーが退出しました',
      color: this.container.colors.error,
      fields: [
        createField(
          'メンバー',
          `<@${member.id}> (${member.user.tag})`,
          false
        ),
        createField(
          '所持ロール',
          roles,
          false
        ),
      ],
      thumbnail: member.user.displayAvatarURL(),
      footer: '退出時刻',
      timestamp: true,
    });

    await logChannel.send({ embeds: [embed] });
  }
}
