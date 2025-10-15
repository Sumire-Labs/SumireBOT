/**
 * Avatar Command
 * Display user's avatar and banner
 */

import { Command } from '@sapphire/framework';
import { SlashCommandBuilder } from 'discord.js';
import { createField } from '../common/design/components.js';

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

    const fields = [
      createField(
        'ユーザー',
        `<@${user.id}> (${user.tag})`,
        false
      ),
      createField(
        'アバターリンク',
        avatarFormats,
        false
      ),
    ];

    // Add banner if exists
    if (user.banner) {
      const bannerFormats = [
        `[512px](${user.bannerURL({ size: 512 })})`,
        `[1024px](${user.bannerURL({ size: 1024 })})`,
        `[2048px](${user.bannerURL({ size: 2048 })})`,
        `[4096px](${user.bannerURL({ size: 4096 })})`,
      ].join(' | ');

      fields.push(
        createField(
          'バナーリンク',
          bannerFormats,
          false
        )
      );
    }

    // Add accent color if exists
    if (user.hexAccentColor) {
      fields.push(
        createField(
          'アクセントカラー',
          user.hexAccentColor,
          true
        )
      );
    }

    const embed = this.container.embedBuilder.create({
      title: `${user.username}のプロフィール画像`,
      color: user.accentColor || this.container.colors.primary,
      fields: fields,
      thumbnail: avatarURL,
      image: user.banner ? user.bannerURL({ size: 2048 }) || undefined : undefined,
      footer: `User ID: ${user.id}`,
      timestamp: true,
    });

    await interaction.reply({ embeds: [embed] });
  }
}
