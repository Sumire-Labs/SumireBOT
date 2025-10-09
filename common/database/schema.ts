/**
 * Database Schema for SumireBOT
 * Drizzle ORM with SQLite
 */

import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

/**
 * Ticket Settings Table
 * Stores ticket system configuration per guild
 */
export const ticketSettings = sqliteTable('ticket_settings', {
  guildId: text('guild_id').primaryKey(),
  categoryId: text('category_id').notNull(),
  notifyRoleId: text('notify_role_id'),
  panelChannelId: text('panel_channel_id'),
  panelMessageId: text('panel_message_id'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

/**
 * Tickets Table
 * Stores individual ticket information
 */
export const tickets = sqliteTable('tickets', {
  id: integer('id', { mode: 'number' }).primaryKey({ autoIncrement: true }),
  guildId: text('guild_id').notNull(),
  channelId: text('channel_id').notNull().unique(),
  userId: text('user_id').notNull(),
  reason: text('reason'),
  status: text('status').notNull().default('open'), // open, closed
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  closedAt: integer('closed_at', { mode: 'timestamp' }),
});

/**
 * Logger Settings Table
 * Stores logger configuration per guild
 */
export const loggerSettings = sqliteTable('logger_settings', {
  guildId: text('guild_id').primaryKey(),
  logChannelId: text('log_channel_id').notNull(),
  enabledEvents: text('enabled_events').notNull(), // JSON array of event names
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

/**
 * AutoRole Settings Table
 * Stores automatic role assignment configuration per guild
 */
export const autoroleSettings = sqliteTable('autorole_settings', {
  guildId: text('guild_id').primaryKey(),
  humanRoleId: text('human_role_id'),
  botRoleId: text('bot_role_id'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

// Export types
export type TicketSettings = typeof ticketSettings.$inferSelect;
export type InsertTicketSettings = typeof ticketSettings.$inferInsert;

export type Ticket = typeof tickets.$inferSelect;
export type InsertTicket = typeof tickets.$inferInsert;

export type LoggerSettings = typeof loggerSettings.$inferSelect;
export type InsertLoggerSettings = typeof loggerSettings.$inferInsert;

export type AutoroleSettings = typeof autoroleSettings.$inferSelect;
export type InsertAutoroleSettings = typeof autoroleSettings.$inferInsert;
