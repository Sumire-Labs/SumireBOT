/**
 * Material 3 Common Components
 * Reusable UI components
 */

import {
  StringSelectMenuBuilder,
  StringSelectMenuOptionBuilder,
  ActionRowBuilder,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle,
} from 'discord.js';

/**
 * Create a language selector
 */
export function createLanguageSelector(currentLang: string): ActionRowBuilder<StringSelectMenuBuilder> {
  const options = [
    new StringSelectMenuOptionBuilder()
      .setLabel('English')
      .setValue('en')
      .setEmoji('🇺🇸')
      .setDescription('Change language to English')
      .setDefault(currentLang === 'en'),
    new StringSelectMenuOptionBuilder()
      .setLabel('日本語')
      .setValue('ja')
      .setEmoji('🇯🇵')
      .setDescription('言語を日本語に変更')
      .setDefault(currentLang === 'ja'),
  ];

  const select = new StringSelectMenuBuilder()
    .setCustomId('language_select')
    .setPlaceholder('言語を選択 / Select Language')
    .addOptions(options);

  return new ActionRowBuilder<StringSelectMenuBuilder>().addComponents(select);
}

/**
 * Create a ticket reason modal
 */
export function createTicketReasonModal(): ModalBuilder {
  const modal = new ModalBuilder()
    .setCustomId('ticket_reason_modal')
    .setTitle('チケットを作成');

  const reasonInput = new TextInputBuilder()
    .setCustomId('ticket_reason')
    .setLabel('お問い合わせ内容')
    .setPlaceholder('詳細をご記入ください...')
    .setStyle(TextInputStyle.Paragraph)
    .setRequired(true)
    .setMinLength(10)
    .setMaxLength(1000);

  const firstRow = new ActionRowBuilder<TextInputBuilder>().addComponents(reasonInput);

  modal.addComponents(firstRow);

  return modal;
}

/**
 * Format a timestamp for display
 */
export function formatTimestamp(date: Date, style: 'f' | 'F' | 'd' | 'D' | 't' | 'T' | 'R' = 'F'): string {
  const timestamp = Math.floor(date.getTime() / 1000);
  return `<t:${timestamp}:${style}>`;
}

/**
 * Create a field for embeds with inline support
 */
export function createField(name: string, value: string, inline: boolean = false) {
  return { name, value, inline };
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Create a progress bar
 */
export function createProgressBar(current: number, total: number, length: number = 10): string {
  const percentage = Math.min(current / total, 1);
  const filled = Math.round(percentage * length);
  const empty = length - filled;

  return '█'.repeat(filled) + '░'.repeat(empty) + ` ${Math.round(percentage * 100)}%`;
}
