/**
 * Guild Member Add Event Listener
 * Logs when members join
 */

import { Listener } from '@sapphire/framework';
import type { GuildMember } from 'discord.js';
import { loggerSettingsService, autoroleSettingsService } from '../common/database/client.js';
import { createField, formatTimestamp } from '../common/design/components.js';

export class GuildMemberAddListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      event: 'guildMemberAdd',
    });
  }

  public async run(member: GuildMember) {
    const guildId = member.guild.id;

    // Auto-assign role if configured
    const autoroleSettings = await autoroleSettingsService.get(guildId);
    if (autoroleSettings) {
      const roleId = member.user.bot ? autoroleSettings.botRoleId : autoroleSettings.humanRoleId;

      if (roleId) {
        try {
          const role = member.guild.roles.cache.get(roleId);
          if (role && member.guild.members.me?.permissions.has('ManageRoles')) {
            await member.roles.add(role);
          }
        } catch (error) {
          console.error(`Failed to assign autorole to ${member.user.tag}:`, error);
        }
      }
    }

    // Check if logger is enabled
    const settings = await loggerSettingsService.get(guildId);
    if (!settings) return;

    const enabledEvents = await loggerSettingsService.getEnabledEvents(guildId);
    if (!enabledEvents.includes('guildMemberAdd')) return;

    // Get log channel
    const logChannel = member.guild.channels.cache.get(settings.logChannelId);
    if (!logChannel?.isTextBased()) return;

    // Create log embed
    const embed = this.container.embedBuilder.create({
      title: '👋 メンバーが参加しました',
      color: this.container.colors.success,
      fields: [
        createField(
          'メンバー',
          `<@${member.id}> (${member.user.tag})`,
          false
        ),
        createField(
          'アカウント作成日',
          formatTimestamp(member.user.createdAt, 'F'),
          true
        ),
      ],
      thumbnail: member.user.displayAvatarURL(),
      footer: '参加時刻',
      timestamp: true,
    });

    await logChannel.send({ embeds: [embed] });
  }
}
