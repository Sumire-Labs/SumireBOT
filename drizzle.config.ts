import type { Config } from 'drizzle-kit';
import yaml from 'js-yaml';
import { readFileSync } from 'fs';

// Load config.yaml to get database path
const configFile = readFileSync('./config.yaml', 'utf8');
const config = yaml.load(configFile) as any;

export default {
  schema: './common/database/schema.ts',
  out: './database/migrations',
  dialect: 'sqlite',
  dbCredentials: {
    url: config.databasePath || './sumireBOT.db'
  }
} satisfies Config;
