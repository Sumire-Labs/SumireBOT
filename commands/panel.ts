/**
 * Panel Command
 * Pterodactyl Panel server management with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  SlashCommandBuilder,
  StringSelectMenuBuilder,
  ActionRowBuilder,
  MessageFlags,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
} from 'discord.js';
import { PterodactylClient } from '../common/pterodactyl/client.js';

export class PanelCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'panel',
      description: 'Pterodactylパネルのサーバー管理',
    });
  }

  public override registerApplicationCommands(registry: Command.Registry) {
    const command = new SlashCommandBuilder()
      .setName(this.name)
      .setDescription(this.description)
      .setDMPermission(false)
      .setDefaultMemberPermissions('0'); // Administrator only

    registry.registerChatInputCommand(command);
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    const guildId = interaction.guildId;
    if (!guildId) return;

    // Check if panel feature is enabled
    if (!this.container.config.features.panel) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        'Panel機能が無効になっています。'
      );
      await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
      return;
    }

    // Check if pterodactyl config exists
    if (!this.container.config.pterodactyl) {
      const embed = this.container.embedBuilder.error(
        'エラー',
        'Pterodactylの設定がされていません。'
      );
      await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
      return;
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    try {
      const client = new PterodactylClient(this.container.config.pterodactyl);
      const servers = await client.getServers();

      if (servers.length === 0) {
        const embed = this.container.embedBuilder.warning(
          '警告',
          'サーバーが見つかりませんでした。'
        );
        await interaction.editReply({ embeds: [embed] });
        return;
      }

      // Create select menu for server selection
      const selectMenu = new StringSelectMenuBuilder()
        .setCustomId('panel_server_select')
        .setPlaceholder('サーバーを選択してください')
        .addOptions(
          servers.map((server) => ({
            label: server.name,
            description: server.description.slice(0, 100) || 'No description',
            value: server.identifier,
          }))
        );

      const row = new ActionRowBuilder<StringSelectMenuBuilder>().addComponents(selectMenu);

      // Build server list with Components v2
      const headerSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent('# 🖥️ サーバー管理パネル')
      );

      const separator = new SeparatorBuilder()
        .setDivider(true)
        .setSpacing(1);

      const infoSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(
          `${servers.length}個のサーバーが見つかりました。\n\n` +
          `📋 **利用可能なサーバー**\n` +
          servers.map(s => `• ${s.name}`).slice(0, 5).join('\n') +
          (servers.length > 5 ? `\n*... 他${servers.length - 5}件*` : '') +
          `\n\n下のメニューから管理するサーバーを選択してください。`
        )
      );

      const container = new ContainerBuilder()
        .setAccentColor(this.container.colors.primary)
        .addSectionComponents(headerSection)
        .addSeparatorComponents(separator)
        .addSectionComponents(infoSection);

      await interaction.editReply({
        components: [container, row],
        flags: MessageFlags.IsComponentsV2,
      });
    } catch (error) {
      console.error('Panel command error:', error);
      const embed = this.container.embedBuilder.error(
        'エラー',
        'サーバー一覧の取得に失敗しました。\nAPI設定を確認してください。'
      );
      await interaction.editReply({ embeds: [embed] });
    }
  }
}
