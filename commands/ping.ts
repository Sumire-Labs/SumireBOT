/**
 * Ping Command
 * Measures bot latency (WebSocket, REST API, SQL) with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';
import { createProgressTracker } from '../common/design/progress.js';
import { measureDatabaseLatency } from '../common/database/client.js';

export class PingCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'ping',
      description: 'レイテンシを計測します。',
    });
  }

  public override async registerApplicationCommands(registry: Command.Registry) {
    registry.registerChatInputCommand((builder) =>
      builder
        .setName('ping')
        .setDescription('BOTのレイテンシを測定します')
    );
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    // Create progress tracker with steps
    const progress = createProgressTracker(
      interaction,
      [
        {
          title: 'WebSocketレイテンシを測定中...',
        },
        {
          title: 'REST APIレイテンシを測定中...',
        },
        {
          title: 'SQLレイテンシを測定中...',
        },
      ],
      this.container.embedBuilder
    );

    // Start progress
    await progress.start();

    // Measure WebSocket latency
    const wsLatency = this.container.client.ws.ping;
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Move to next step
    await progress.next();

    // Measure REST API latency
    const restStart = Date.now();
    await this.container.client.rest.get('/gateway');
    const restLatency = Date.now() - restStart;
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Move to next step
    await progress.next();

    // Measure SQL latency
    const sqlLatency = await measureDatabaseLatency();
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Get color based on average latency
    const avgLatency = (wsLatency + restLatency + sqlLatency) / 3;
    let color = this.container.colors.success;
    let statusEmoji = '🟢';
    let statusText = '良好';

    if (avgLatency > 200) {
      color = this.container.colors.warning;
      statusEmoji = '🟡';
      statusText = '普通';
    }
    if (avgLatency > 500) {
      color = this.container.colors.error;
      statusEmoji = '🔴';
      statusText = '遅延';
    }

    // Complete with results using Components v2
    const headerSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `# 🏓 Pong!\n${statusEmoji} **ステータス:** ${statusText}`
      )
    );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const latencySection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `📊 **レイテンシ測定結果**\n\n` +
        `🌐 **WebSocket:** \`${wsLatency}ms\`\n` +
        `🔗 **REST API:** \`${restLatency}ms\`\n` +
        `💾 **データベース:** \`${sqlLatency}ms\`\n\n` +
        `📈 **平均レイテンシ:** \`${Math.round(avgLatency)}ms\``
      )
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const infoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `💡 **レイテンシについて**\n` +
        `• 🟢 \`0-200ms\`: 良好\n` +
        `• 🟡 \`200-500ms\`: 普通\n` +
        `• 🔴 \`500ms+\`: 遅延`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(color)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(latencySection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(infoSection);

    await interaction.editReply({
      content: '',
      embeds: [],
      components: [container],
      flags: MessageFlags.IsComponentsV2,
    });
  }
}
