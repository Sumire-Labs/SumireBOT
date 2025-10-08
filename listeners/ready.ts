/**
 * Ready Event Listener
 * Fires when the bot is ready
 */

import { Listener } from '@sapphire/framework';
import { ActivityType, type Client } from 'discord.js';

export class ReadyListener extends Listener {
  public constructor(context: Listener.LoaderContext, options: Listener.Options) {
    super(context, {
      ...options,
      once: true,
      event: 'clientReady',
    });
  }

  public run(client: Client<true>): void {
    const { config } = this.container;

    // Set presence
    const activityTypeMap: Record<string, ActivityType> = {
      playing: ActivityType.Playing,
      streaming: ActivityType.Streaming,
      listening: ActivityType.Listening,
      watching: ActivityType.Watching,
      competing: ActivityType.Competing,
    };

    const activityType = activityTypeMap[config.activity.type] || ActivityType.Watching;

    client.user.setPresence({
      status: config.status,
      activities: [
        {
          name: config.activity.name,
          type: activityType,
        },
      ],
    });

    console.log(`✅ ${client.user.tag} is ready!`);
    console.log(`📊 Serving ${client.guilds.cache.size} guilds`);
  }
}
