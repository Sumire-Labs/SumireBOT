/**
 * Role Update Event Listener
 * Logs when roles are updated
 */

import { Listener } from '@sapphire/framework';
import type { Role } from 'discord.js';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { loggerSettingsService } from '../common/database/client.js';

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
      changes.push(`**名前:** ${oldRole.name} → ${newRole.name}`);
    }

    if (oldRole.hexColor !== newRole.hexColor) {
      changes.push(`**カラー:** ${oldRole.hexColor} → ${newRole.hexColor}`);
    }

    if (oldRole.permissions.bitfield !== newRole.permissions.bitfield) {
      changes.push(`**権限:** 更新されました`);
    }

    if (oldRole.hoist !== newRole.hoist) {
      changes.push(`**別表示:** ${oldRole.hoist ? 'はい' : 'いいえ'} → ${newRole.hoist ? 'はい' : 'いいえ'}`);
    }

    if (oldRole.mentionable !== newRole.mentionable) {
      changes.push(`**メンション可能:** ${oldRole.mentionable ? 'はい' : 'いいえ'} → ${newRole.mentionable ? 'はい' : 'いいえ'}`);
    }

    // If no significant changes, don't log
    if (changes.length === 0) return;

    // Create log with Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# 🎨 ロールが更新されました')
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `🎭 **ロール:** <@&${newRole.id}>\n` +
        `🏷️ **ロール名:** ${newRole.name}\n` +
        `🆔 **ロールID:** \`${newRole.id}\`\n` +
        `🕒 **更新時刻:** <t:${Math.floor(Date.now() / 1000)}:F>`
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const changesSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📝 **変更内容:**\n${changes.join('\n')}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(this.container.colors.info)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(infoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(changesSection);

    try {
      await logChannel.send({
        components: [container],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Failed to send role update log:', error);
    }
  }
}
