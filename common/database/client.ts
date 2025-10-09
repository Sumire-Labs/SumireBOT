/**
 * Database Client
 * Drizzle ORM with Bun SQLite
 */

import { Database } from 'bun:sqlite';
import { drizzle, type BunSQLiteDatabase } from 'drizzle-orm/bun-sqlite';
import { migrate } from 'drizzle-orm/bun-sqlite/migrator';
import * as schema from './schema.js';
import { eq } from 'drizzle-orm';
import { existsSync } from 'fs';

let db: BunSQLiteDatabase<typeof schema> | null = null;

/**
 * Initialize the database connection
 */
export function initDatabase(path: string = './database/sumire.db'): BunSQLiteDatabase<typeof schema> {
  if (db) return db;

  const sqlite = new Database(path, { create: true });
  sqlite.exec('PRAGMA journal_mode = WAL;');

  db = drizzle(sqlite, { schema });

  // Run migrations automatically
  runMigrations(db);

  return db;
}

/**
 * Run database migrations
 */
function runMigrations(database: BunSQLiteDatabase<typeof schema>): void {
  try {
    // Check if migrations directory exists with valid journal
    const migrationsPath = './database/migrations';
    const journalPath = `${migrationsPath}/meta/_journal.json`;

    if (existsSync(journalPath)) {
      migrate(database, { migrationsFolder: migrationsPath });
      console.log('✅ Database migrations applied');
    } else {
      // Create tables directly if no migrations exist
      console.log('ℹ️  No migrations found, creating tables directly...');
      createTablesDirectly(database);
    }
  } catch (_error) {
    console.log('ℹ️  Falling back to direct table creation...');
    // Try to create tables directly as fallback
    createTablesDirectly(database);
  }
}

/**
 * Create tables directly (fallback method)
 */
function createTablesDirectly(database: BunSQLiteDatabase<typeof schema>): void {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sqlite = (database as any).$client;

  // Create ticket_settings table
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS ticket_settings (
      guild_id TEXT PRIMARY KEY,
      category_id TEXT NOT NULL,
      notify_role_id TEXT,
      panel_channel_id TEXT,
      panel_message_id TEXT,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )
  `);

  // Create tickets table
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS tickets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guild_id TEXT NOT NULL,
      channel_id TEXT NOT NULL UNIQUE,
      user_id TEXT NOT NULL,
      reason TEXT,
      status TEXT NOT NULL DEFAULT 'open',
      created_at INTEGER NOT NULL,
      closed_at INTEGER
    )
  `);

  // Create logger_settings table
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS logger_settings (
      guild_id TEXT PRIMARY KEY,
      log_channel_id TEXT NOT NULL,
      enabled_events TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )
  `);

  // Create autorole_settings table
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS autorole_settings (
      guild_id TEXT PRIMARY KEY,
      human_role_id TEXT,
      bot_role_id TEXT,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )
  `);

  console.log('✅ Database tables created');
}

/**
 * Get the database instance
 */
export function getDatabase(): BunSQLiteDatabase<typeof schema> {
  if (!db) {
    throw new Error('Database not initialized. Call initDatabase() first.');
  }
  return db;
}

/**
 * Measure database latency
 */
export async function measureDatabaseLatency(): Promise<number> {
  const start = Date.now();
  const db = getDatabase();

  // Simple SELECT 1 query to measure latency
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sqlite = (db as any).$client;
  sqlite.prepare('SELECT 1').run();

  return Date.now() - start;
}

/**
 * Ticket Settings helpers
 */
export const ticketSettingsService = {
  async get(guildId: string) {
    const db = getDatabase();
    const result = await db.query.ticketSettings.findFirst({
      where: eq(schema.ticketSettings.guildId, guildId),
    });
    return result;
  },

  async set(data: schema.InsertTicketSettings) {
    const db = getDatabase();
    const existing = await this.get(data.guildId);

    if (existing) {
      await db
        .update(schema.ticketSettings)
        .set({ ...data, updatedAt: new Date() })
        .where(eq(schema.ticketSettings.guildId, data.guildId));
    } else {
      await db.insert(schema.ticketSettings).values({
        ...data,
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }
  },
};

/**
 * Ticket helpers
 */
export const ticketService = {
  async create(data: schema.InsertTicket) {
    const db = getDatabase();
    const result = await db.insert(schema.tickets).values({
      ...data,
      createdAt: new Date(),
    }).returning();
    return result[0];
  },

  async get(channelId: string) {
    const db = getDatabase();
    const result = await db.query.tickets.findFirst({
      where: eq(schema.tickets.channelId, channelId),
    });
    return result;
  },

  async getByUserId(userId: string, guildId: string) {
    const db = getDatabase();
    const result = await db.query.tickets.findFirst({
      where: (tickets, { and, eq }) =>
        and(
          eq(tickets.userId, userId),
          eq(tickets.guildId, guildId),
          eq(tickets.status, 'open')
        ),
    });
    return result;
  },

  async close(channelId: string) {
    const db = getDatabase();
    await db
      .update(schema.tickets)
      .set({ status: 'closed', closedAt: new Date() })
      .where(eq(schema.tickets.channelId, channelId));
  },
};

/**
 * Logger Settings helpers
 */
export const loggerSettingsService = {
  async get(guildId: string) {
    const db = getDatabase();
    const result = await db.query.loggerSettings.findFirst({
      where: eq(schema.loggerSettings.guildId, guildId),
    });
    return result;
  },

  async set(guildId: string, logChannelId: string, enabledEvents: string[]) {
    const db = getDatabase();
    const existing = await this.get(guildId);

    if (existing) {
      await db
        .update(schema.loggerSettings)
        .set({
          logChannelId,
          enabledEvents: JSON.stringify(enabledEvents),
          updatedAt: new Date(),
        })
        .where(eq(schema.loggerSettings.guildId, guildId));
    } else {
      await db.insert(schema.loggerSettings).values({
        guildId,
        logChannelId,
        enabledEvents: JSON.stringify(enabledEvents),
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }
  },

  async getEnabledEvents(guildId: string): Promise<string[]> {
    const settings = await this.get(guildId);
    if (!settings) return [];

    try {
      return JSON.parse(settings.enabledEvents);
    } catch {
      return [];
    }
  },
};

/**
 * AutoRole Settings helpers
 */
export const autoroleSettingsService = {
  async get(guildId: string) {
    const db = getDatabase();
    const result = await db.query.autoroleSettings.findFirst({
      where: eq(schema.autoroleSettings.guildId, guildId),
    });
    return result;
  },

  async setHumanRole(guildId: string, roleId: string | null) {
    const db = getDatabase();
    const existing = await this.get(guildId);

    if (existing) {
      await db
        .update(schema.autoroleSettings)
        .set({ humanRoleId: roleId, updatedAt: new Date() })
        .where(eq(schema.autoroleSettings.guildId, guildId));
    } else {
      await db.insert(schema.autoroleSettings).values({
        guildId,
        humanRoleId: roleId,
        botRoleId: null,
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }
  },

  async setBotRole(guildId: string, roleId: string | null) {
    const db = getDatabase();
    const existing = await this.get(guildId);

    if (existing) {
      await db
        .update(schema.autoroleSettings)
        .set({ botRoleId: roleId, updatedAt: new Date() })
        .where(eq(schema.autoroleSettings.guildId, guildId));
    } else {
      await db.insert(schema.autoroleSettings).values({
        guildId,
        humanRoleId: null,
        botRoleId: roleId,
        createdAt: new Date(),
        updatedAt: new Date(),
      });
    }
  },
};
