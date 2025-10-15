/**
 * Guild Member Remove Event Listener
 * Logs when members leave
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
import { loggerSettingsService } from '../common/database/client.js';

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
      .join(', ') || '*ロールなし*';

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 👋 メンバーが退出しました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `👤 **メンバー:** <@${member.id}>\n` +
        `🏷️ **ユーザー名:** ${member.user.tag}\n` +
        `🆔 **ユーザーID:** \`${member.id}\`\n` +
        `🕒 **退出時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const rolesSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `🎭 **所持ロール:**\n${roles}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.error)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(rolesSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send guild member remove log:', error);
    }
  }
}
