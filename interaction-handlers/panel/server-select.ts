/**
 * Panel Server Select Handler
 * Handles server selection from select menu
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { StringSelectMenuInteraction } from 'discord.js';
import { ButtonBuilder, ButtonStyle, ActionRowBuilder } from 'discord.js';
import { PterodactylClient } from '../../common/pterodactyl/client.js';

export class ServerSelectHandler extends InteractionHandler {
  public constructor(ctx: InteractionHandler.LoaderContext, options: InteractionHandler.Options) {
    super(ctx, {
      ...options,
      interactionHandlerType: InteractionHandlerTypes.SelectMenu,
    });
  }

  public override parse(interaction: StringSelectMenuInteraction) {
    if (interaction.customId !== 'panel_server_select') return this.none();
    return this.some();
  }

  public override async run(interaction: StringSelectMenuInteraction) {
    if (!this.container.config.pterodactyl) return;

    await interaction.deferUpdate();

    const serverId = interaction.values[0];

    try {
      const client = new PterodactylClient(this.container.config.pterodactyl);
      const server = await client.getServer(serverId);
      const resources = await client.getServerResources(serverId);

      // Create power control buttons
      const startButton = new ButtonBuilder()
        .setCustomId(`panel_power_${serverId}_start`)
        .setLabel('起動')
        .setEmoji('▶️')
        .setStyle(ButtonStyle.Success);

      const stopButton = new ButtonBuilder()
        .setCustomId(`panel_power_${serverId}_stop`)
        .setLabel('停止')
        .setEmoji('⏹️')
        .setStyle(ButtonStyle.Danger);

      const restartButton = new ButtonBuilder()
        .setCustomId(`panel_power_${serverId}_restart`)
        .setLabel('再起動')
        .setEmoji('🔄')
        .setStyle(ButtonStyle.Primary);

      const killButton = new ButtonBuilder()
        .setCustomId(`panel_power_${serverId}_kill`)
        .setLabel('強制終了')
        .setEmoji('⚠️')
        .setStyle(ButtonStyle.Secondary);

      const row = new ActionRowBuilder<ButtonBuilder>().addComponents(
        startButton,
        stopButton,
        restartButton,
        killButton
      );

      // Create embed with server info
      const statusEmoji = resources.current_state === 'running' ? '🟢' : '🔴';
      const embed = this.container.embedBuilder.create({
        title: `${statusEmoji} ${server.name}`,
        description: server.description || 'No description',
        color: resources.current_state === 'running'
          ? this.container.colors.success
          : this.container.colors.error,
        fields: [
          {
            name: '状態',
            value: resources.current_state || 'unknown',
            inline: true,
          },
          {
            name: 'CPU使用率',
            value: `${resources.resources.cpu_absolute.toFixed(2)}%`,
            inline: true,
          },
          {
            name: 'メモリ使用量',
            value: `${(resources.resources.memory_bytes / 1024 / 1024).toFixed(0)} MB / ${server.limits.memory} MB`,
            inline: true,
          },
          {
            name: 'ディスク使用量',
            value: `${(resources.resources.disk_bytes / 1024 / 1024).toFixed(0)} MB / ${server.limits.disk} MB`,
            inline: true,
          },
          {
            name: 'ネットワーク',
            value: `↑ ${(resources.resources.network_tx_bytes / 1024 / 1024).toFixed(2)} MB\n↓ ${(resources.resources.network_rx_bytes / 1024 / 1024).toFixed(2)} MB`,
            inline: true,
          },
        ],
        footer: `Server ID: ${server.identifier}`,
        timestamp: true,
      });

      await interaction.editReply({
        embeds: [embed],
        components: [row],
      });
    } catch (error) {
      console.error('Server select error:', error);
      const embed = this.container.embedBuilder.error(
        'エラー',
        'サーバー情報の取得に失敗しました。'
      );
      await interaction.editReply({
        embeds: [embed],
        components: [],
      });
    }
  }
}
