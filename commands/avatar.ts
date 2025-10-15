/**
 * Avatar Command
 * Display user's avatar and banner with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  SlashCommandBuilder,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  ThumbnailBuilder,
  MessageFlags,
} from 'discord.js';

export class AvatarCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'avatar',
      description: 'ユーザーのアバターとバナーを表示',
    });
  }

  public override registerApplicationCommands(registry: Command.Registry) {
    const command = new SlashCommandBuilder()
      .setName(this.name)
      .setDescription(this.description)
      .addUserOption((option) =>
        option
          .setName('user')
          .setDescription('表示するユーザー（省略で自分）')
          .setRequired(false)
      );

    registry.registerChatInputCommand(command);
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    const targetUser = interaction.options.getUser('user') || interaction.user;

    // Fetch full user to get banner
    const user = await targetUser.fetch();

    // Get avatar URLs in different sizes
    const avatarURL = user.displayAvatarURL({ size: 4096 });
    const avatarFormats = [
      `[512px](${user.displayAvatarURL({ size: 512 })})`,
      `[1024px](${user.displayAvatarURL({ size: 1024 })})`,
      `[2048px](${user.displayAvatarURL({ size: 2048 })})`,
      `[4096px](${user.displayAvatarURL({ size: 4096 })})`,
    ].join(' | ');

    // Build user profile with Components v2
    const headerSection = new SectionBuilder()
      .addTextDisplayComponents(
        new TextDisplayBuilder().setContent(`# 👤 ${user.username}のプロフィール画像`)
      )
      .setThumbnailAccessory(
        new ThumbnailBuilder().setMedia({ url: avatarURL })
      );

    const separator1 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    let userInfoText = `**ユーザー:** <@${user.id}> (${user.tag})\n**User ID:** \`${user.id}\``;
    if (user.hexAccentColor) {
      userInfoText += `\n**アクセントカラー:** ${user.hexAccentColor}`;
    }

    const userInfoSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(userInfoText)
    );

    const separator2 = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const avatarLinksSection = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `🖼️ **アバターリンク**\n${avatarFormats}`
      )
    );

    const container = new ContainerBuilder()
      .setAccentColor(user.accentColor || this.container.colors.primary)
      .addSectionComponents(headerSection)
      .addSeparatorComponents(separator1)
      .addSectionComponents(userInfoSection)
      .addSeparatorComponents(separator2)
      .addSectionComponents(avatarLinksSection);

    // Add banner if exists
    if (user.banner) {
      const bannerFormats = [
        `[512px](${user.bannerURL({ size: 512 })})`,
        `[1024px](${user.bannerURL({ size: 1024 })})`,
        `[2048px](${user.bannerURL({ size: 2048 })})`,
        `[4096px](${user.bannerURL({ size: 4096 })})`,
      ].join(' | ');

      const separator3 = new SeparatorBuilder()
        .setDivider(true)
        .setSpacing(1);

      const bannerSection = new SectionBuilder().addTextDisplayComponents(
        new TextDisplayBuilder().setContent(
          `🎨 **バナーリンク**\n${bannerFormats}`
        )
      );

      container.addSeparatorComponents(separator3).addSectionComponents(bannerSection);
    }

    await interaction.reply({
      components: [container],
      flags: MessageFlags.IsComponentsV2,
    });
  }
}
