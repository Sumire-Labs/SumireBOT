/**
 * Material 3 Button System
 * Consistent button styling for interactions
 */

import {
  ButtonBuilder,
  ButtonStyle,
  ActionRowBuilder,
  type ButtonBuilder as ButtonBuilderType,
} from 'discord.js';

export type M3ButtonStyle = 'primary' | 'secondary' | 'success' | 'danger' | 'link';

/**
 * Convert M3 button style to Discord button style
 */
function getButtonStyle(style: M3ButtonStyle): ButtonStyle {
  switch (style) {
    case 'primary':
      return ButtonStyle.Primary;
    case 'secondary':
      return ButtonStyle.Secondary;
    case 'success':
      return ButtonStyle.Success;
    case 'danger':
      return ButtonStyle.Danger;
    case 'link':
      return ButtonStyle.Link;
  }
}

export interface M3ButtonOptions {
  customId?: string;
  label: string;
  style: M3ButtonStyle;
  emoji?: string;
  disabled?: boolean;
  url?: string;
}

/**
 * Create a Material 3 styled button
 */
export function createButton(options: M3ButtonOptions): ButtonBuilder {
  const button = new ButtonBuilder()
    .setLabel(options.label)
    .setStyle(getButtonStyle(options.style));

  if (options.customId) {
    button.setCustomId(options.customId);
  }

  if (options.emoji) {
    button.setEmoji(options.emoji);
  }

  if (options.disabled) {
    button.setDisabled(options.disabled);
  }

  if (options.url) {
    button.setURL(options.url);
  }

  return button;
}

/**
 * Create an action row with buttons
 */
export function createButtonRow(
  ...buttons: ButtonBuilder[]
): ActionRowBuilder<ButtonBuilder> {
  return new ActionRowBuilder<ButtonBuilder>().addComponents(...buttons);
}

/**
 * Common button presets
 */
export const ButtonPresets = {
  /**
   * Create a "Create Ticket" button
   */
  createTicket: () =>
    createButton({
      customId: 'ticket_create',
      label: 'チケットを作成',
      style: 'primary',
      emoji: '🎫',
    }),

  /**
   * Create a "Close Ticket" button
   */
  closeTicket: () =>
    createButton({
      customId: 'ticket_close',
      label: 'チケットをクローズ',
      style: 'danger',
      emoji: '🔒',
    }),

  /**
   * Create a "Confirm" button
   */
  confirm: (customId: string = 'confirm') =>
    createButton({
      customId,
      label: '確認',
      style: 'success',
      emoji: '✅',
    }),

  /**
   * Create a "Cancel" button
   */
  cancel: (customId: string = 'cancel') =>
    createButton({
      customId,
      label: 'キャンセル',
      style: 'secondary',
      emoji: '❌',
    }),
};
