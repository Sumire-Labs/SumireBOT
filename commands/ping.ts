/**
 * Ping Command
 * Measures bot latency (WebSocket, REST API, SQL)
 */

import { Command } from '@sapphire/framework';
import { createProgressTracker } from '../common/design/progress.js';
import { measureDatabaseLatency } from '../common/database/client.js';
import { createField } from '../common/design/components.js';

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
    if (avgLatency > 200) color = this.container.colors.warning;
    if (avgLatency > 500) color = this.container.colors.error;

    // Complete with results
    const resultEmbed = this.container.embedBuilder.create({
      title: '🏓 Pong!',
      color,
      fields: [
        createField(
          'WebSocket',
          `\`${wsLatency}ms\``,
          true
        ),
        createField(
          'REST API',
          `\`${restLatency}ms\``,
          true
        ),
        createField(
          'データベース',
          `\`${sqlLatency}ms\``,
          true
        ),
      ],
      footer: 'レイテンシ測定完了',
      timestamp: true,
    });

    await progress.update(resultEmbed);
  }
}
