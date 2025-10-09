/**
 * Panel Command
 * Pterodactyl Panel server management
 */

import { Command } from '@sapphire/framework';
import { SlashCommandBuilder, StringSelectMenuBuilder, ActionRowBuilder, MessageFlags } from 'discord.js';
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

      const embed = this.container.embedBuilder.create({
        title: '🖥️ サーバー管理パネル',
        description: `${servers.length}個のサーバーが見つかりました。\n管理するサーバーを選択してください。`,
        color: this.container.colors.primary,
        timestamp: true,
      });

      await interaction.editReply({
        embeds: [embed],
        components: [row],
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
