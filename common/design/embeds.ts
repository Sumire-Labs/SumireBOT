/**
 * Material 3 Expressive Embed System
 * Beautiful and consistent embed generation
 */

import { EmbedBuilder, type APIEmbedField } from 'discord.js';
import { M3Colors, type ColorPalette } from './colors.js';

export interface EmbedOptions {
  title?: string;
  description?: string;
  color?: number | keyof ColorPalette;
  fields?: APIEmbedField[];
  footer?: string;
  timestamp?: boolean;
  thumbnail?: string;
  image?: string;
  author?: {
    name: string;
    iconURL?: string;
  };
}

export class M3EmbedBuilder {
  private colors: ColorPalette;

  constructor(colors: ColorPalette = M3Colors) {
    this.colors = colors;
  }

  /**
   * Create a basic embed with Material 3 styling
   */
  create(options: EmbedOptions): EmbedBuilder {
    const embed = new EmbedBuilder();

    if (options.title) {
      embed.setTitle(options.title);
    }

    if (options.description) {
      embed.setDescription(options.description);
    }

    // Set color
    if (options.color) {
      const color = typeof options.color === 'string'
        ? this.colors[options.color]
        : options.color;
      embed.setColor(color);
    } else {
      embed.setColor(this.colors.primary);
    }

    if (options.fields && options.fields.length > 0) {
      embed.addFields(options.fields);
    }

    if (options.footer) {
      embed.setFooter({ text: options.footer });
    }

    if (options.timestamp) {
      embed.setTimestamp();
    }

    if (options.thumbnail) {
      embed.setThumbnail(options.thumbnail);
    }

    if (options.image) {
      embed.setImage(options.image);
    }

    if (options.author) {
      embed.setAuthor({
        name: options.author.name,
        iconURL: options.author.iconURL,
      });
    }

    return embed;
  }

  /**
   * Create a success embed
   */
  success(title: string, description?: string, footer?: string): EmbedBuilder {
    return this.create({
      title: `✅ ${title}`,
      description,
      color: this.colors.success,
      footer,
      timestamp: true,
    });
  }

  /**
   * Create an error embed
   */
  error(title: string, description?: string, footer?: string): EmbedBuilder {
    return this.create({
      title: `❌ ${title}`,
      description,
      color: this.colors.error,
      footer,
      timestamp: true,
    });
  }

  /**
   * Create a warning embed
   */
  warning(title: string, description?: string, footer?: string): EmbedBuilder {
    return this.create({
      title: `⚠️ ${title}`,
      description,
      color: this.colors.warning,
      footer,
      timestamp: true,
    });
  }

  /**
   * Create an info embed
   */
  info(title: string, description?: string, footer?: string): EmbedBuilder {
    return this.create({
      title: `ℹ️ ${title}`,
      description,
      color: this.colors.info,
      footer,
      timestamp: true,
    });
  }

  /**
   * Create a loading/progress embed
   */
  loading(title: string, description?: string): EmbedBuilder {
    return this.create({
      title: `🔄 ${title}`,
      description,
      color: this.colors.primary,
      timestamp: true,
    });
  }
}

// Export a default instance
export const embedBuilder = new M3EmbedBuilder();
