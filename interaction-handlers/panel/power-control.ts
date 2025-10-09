/**
 * Panel Power Control Handler
 * Handles server power operations (start/stop/restart/kill)
 */

import { InteractionHandler, InteractionHandlerTypes } from '@sapphire/framework';
import type { ButtonInteraction } from 'discord.js';
import { MessageFlags } from 'discord.js';
import { PterodactylClient, type PowerSignal } from '../../common/pterodactyl/client.js';

export class PowerControlHandler extends InteractionHandler {
  public constructor(ctx: InteractionHandler.LoaderContext, options: InteractionHandler.Options) {
    super(ctx, {
      ...options,
      interactionHandlerType: InteractionHandlerTypes.Button,
    });
  }

  public override parse(interaction: ButtonInteraction) {
    if (!interaction.customId.startsWith('panel_power_')) return this.none();
    return this.some();
  }

  public override async run(interaction: ButtonInteraction) {
    if (!this.container.config.pterodactyl) return;

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    // Parse custom ID: panel_power_{serverId}_{signal}
    const parts = interaction.customId.split('_');
    const serverId = parts[2];
    const signal = parts[3] as PowerSignal['signal'];

    const signalText: Record<PowerSignal['signal'], string> = {
      start: '起動',
      stop: '停止',
      restart: '再起動',
      kill: '強制終了',
    };

    try {
      const client = new PterodactylClient(this.container.config.pterodactyl);
      await client.sendPowerSignal(serverId, signal);

      const embed = this.container.embedBuilder.success(
        '完了',
        `サーバーに${signalText[signal]}コマンドを送信しました。`
      );

      await interaction.editReply({ embeds: [embed] });

      // Update the original message with new server status after a delay
      setTimeout(async () => {
        try {
          const server = await client.getServer(serverId);
          const resources = await client.getServerResources(serverId);

          const statusEmoji = resources.current_state === 'running' ? '🟢' : '🔴';
          const updatedEmbed = this.container.embedBuilder.create({
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
            ],
            footer: `Server ID: ${server.identifier} | 最終更新`,
            timestamp: true,
          });

          await interaction.message.edit({ embeds: [updatedEmbed] });
        } catch (error) {
          console.error('Failed to update server status:', error);
        }
      }, 3000);
    } catch (error) {
      console.error('Power control error:', error);
      const embed = this.container.embedBuilder.error(
        'エラー',
        `${signalText[signal]}コマンドの送信に失敗しました。`
      );
      await interaction.editReply({ embeds: [embed] });
    }
  }
}
