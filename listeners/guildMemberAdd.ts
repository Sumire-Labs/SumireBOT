/**
 * Guild Member Add Event Listener
 * Logs when members join
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
import { loggerSettingsService, autoroleSettingsService } from '../common/database/client.js';

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

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 👋 メンバーが参加しました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **メンバー:** <@${member.id}>\n` +
        `🏷️ **ユーザー名:** ${member.user.tag}\n` +
        `🆔 **ユーザーID:** \`${member.id}\`\n` +
        `📅 **アカウント作成日:** <t:${Math.floor(member.user.createdTimestamp / 1000)}:F>\n` +
        `🕒 **参加時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send guild member add log:', error);
    }
  }
}
