/**
 * Material 3 Progress System
 * Ephemeral progress indicators for long-running operations
 */

import type {
  ChatInputCommandInteraction,
  Message,
  EmbedBuilder,
  APIEmbed,
} from 'discord.js';
import { MessageFlags } from 'discord.js';
import { M3EmbedBuilder } from './embeds.js';

export interface ProgressStep {
  title: string;
  description?: string;
}

export class ProgressTracker {
  private interaction: ChatInputCommandInteraction;
  private embedBuilder: M3EmbedBuilder;
  private steps: ProgressStep[];
  private currentStep: number = 0;
  private message: Message | null = null;

  constructor(
    interaction: ChatInputCommandInteraction,
    steps: ProgressStep[],
    embedBuilder: M3EmbedBuilder
  ) {
    this.interaction = interaction;
    this.steps = steps;
    this.embedBuilder = embedBuilder;
  }

  /**
   * Start the progress tracker
   */
  async start(): Promise<void> {
    const embed = this.embedBuilder.loading(
      this.steps[0].title,
      this.steps[0].description
    );

    await this.interaction.deferReply({ flags: MessageFlags.Ephemeral });
    this.message = await this.interaction.editReply({
      embeds: [embed],
    });
  }

  /**
   * Update to the next step
   */
  async next(): Promise<void> {
    this.currentStep++;

    if (this.currentStep >= this.steps.length || !this.message) {
      return;
    }

    const step = this.steps[this.currentStep];
    const embed = this.embedBuilder.loading(
      step.title,
      step.description
    );

    await this.interaction.editReply({
      embeds: [embed],
    });
  }

  /**
   * Complete the progress with a success message
   */
  async complete(title: string, description?: string, footer?: string): Promise<void> {
    const embed = this.embedBuilder.success(title, description, footer);

    await this.interaction.editReply({
      embeds: [embed],
    });
  }

  /**
   * Fail the progress with an error message
   */
  async fail(title: string, description?: string, footer?: string): Promise<void> {
    const embed = this.embedBuilder.error(title, description, footer);

    await this.interaction.editReply({
      embeds: [embed],
    });
  }

  /**
   * Update with a custom embed
   */
  async update(embed: EmbedBuilder | APIEmbed): Promise<void> {
    await this.interaction.editReply({
      embeds: [embed],
    });
  }
}

/**
 * Create a progress tracker for a command interaction
 */
export function createProgressTracker(
  interaction: ChatInputCommandInteraction,
  steps: ProgressStep[],
  embedBuilder: M3EmbedBuilder
): ProgressTracker {
  return new ProgressTracker(interaction, steps, embedBuilder);
}
