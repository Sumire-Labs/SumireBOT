/**
 * SumireBOT - Entry Point
 * A modern Discord bot with Material 3 Expressive design
 */

import { SumireClient, type BotConfig } from './lib/SumireClient.js';
import yaml from 'js-yaml';
import { readFileSync } from 'fs';

// Load configuration
console.log('📝 Loading configuration...');
const configFile = readFileSync('./config.yaml', 'utf8');
const config = yaml.load(configFile) as BotConfig;

// Validate configuration
if (!config.token || config.token === 'YOUR_BOT_TOKEN_HERE') {
  console.error('❌ Please set your Discord bot token in config.yaml');
  process.exit(1);
}

// Create and start the bot
const client = new SumireClient(config);

// Handle process termination
process.on('SIGINT', async () => {
  await client.destroy();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await client.destroy();
  process.exit(0);
});

// Start the bot
await client.start();
