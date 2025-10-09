/**
 * Sumire Custom Client
 * Extended Sapphire client with custom features
 */

import { SapphireClient, container } from '@sapphire/framework';
import { GatewayIntentBits, Partials } from 'discord.js';
import { initDatabase } from '../common/database/client.js';
import { M3EmbedBuilder } from '../common/design/embeds.js';
import { loadColorsFromConfig, type ColorPalette } from '../common/design/colors.js';

export interface BotConfig {
  token: string;
  databasePath: string;
  status: 'online' | 'idle' | 'dnd' | 'invisible';
  activity: {
    type: string;
    name: string;
  };
  features: {
    ping: boolean;
    lang: boolean;
    ticket: boolean;
    logger: boolean;
  };
}

export class SumireClient extends SapphireClient {
  public config: BotConfig;
  public colors: ColorPalette;
  public embedBuilder: M3EmbedBuilder;

  constructor(config: BotConfig) {
    super({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMembers,
        GatewayIntentBits.GuildBans,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
      ],
      partials: [Partials.GuildMember, Partials.Message],
      loadMessageCommandListeners: true,
    });

    this.config = config;
    this.colors = loadColorsFromConfig(null); // Use default Material 3 colors
    this.embedBuilder = new M3EmbedBuilder(this.colors);

    // Initialize systems
    this.initializeSystems();
  }

  private initializeSystems(): void {
    // Initialize database
    console.log('🗄️  Initializing database...');
    initDatabase(this.config.databasePath);

    // Store in container for global access
    container.config = this.config;
    container.embedBuilder = this.embedBuilder;
    container.colors = this.colors;
  }

  public async start(): Promise<void> {
    try {
      console.log('🚀 Starting SumireBOT...');
      await this.login(this.config.token);
    } catch (error) {
      console.error('❌ Failed to start bot:', error);
      process.exit(1);
    }
  }

  public override async destroy(): Promise<void> {
    console.log('👋 Shutting down SumireBOT...');
    await super.destroy();
  }
}

// Augment container with custom properties
declare module '@sapphire/pieces' {
  interface Container {
    config: BotConfig;
    embedBuilder: M3EmbedBuilder;
    colors: ColorPalette;
  }
}
