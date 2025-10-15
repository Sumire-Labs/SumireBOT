/**
 * AutoRole Command
 * Automatic role assignment management with Components v2
 */

import { Command } from '@sapphire/framework';
import {
  PermissionFlagsBits,
  MessageFlags,
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
} from 'discord.js';
import { autoroleSettingsService } from '../common/database/client.js';

export class AutoRoleCommand extends Command {
  public constructor(context: Command.LoaderContext, options: Command.Options) {
    super(context, {
      ...options,
      name: 'autorole',
      description: '自動ロール付与を設定します。',
    });
  }

  public override async registerApplicationCommands(registry: Command.Registry) {
    registry.registerChatInputCommand((builder) =>
      builder
        .setName('autorole')
        .setDescription('自動ロール付与の管理')
        .addSubcommand((subcommand) =>
          subcommand
            .setName('setup')
            .setDescription('自動ロール付与を設定します')
            .addRoleOption((option) =>
              option
                .setName('role')
                .setDescription('自動で付与するロール')
                .setRequired(true)
            )
            .addStringOption((option) =>
              option
                .setName('target')
                .setDescription('対象のタイプ（人間 or Bot）')
                .setRequired(true)
                .addChoices(
                  { name: 'Human 👤', value: 'human' },
                  { name: 'Bot 🤖', value: 'bot' }
                )
            )
        )
        .addSubcommand((subcommand) =>
          subcommand
            .setName('remove')
            .setDescription('自動ロール付与を削除します')
            .addStringOption((option) =>
              option
                .setName('target')
                .setDescription('削除する対象のタイプ（人間 or Bot）')
                .setRequired(true)
                .addChoices(
                  { name: 'Human 👤', value: 'human' },
                  { name: 'Bot 🤖', value: 'bot' }
                )
            )
        )
        .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    );
  }

  public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
    const subcommand = interaction.options.getSubcommand();

    if (subcommand === 'setup') {
      await this.handleSetup(interaction);
    } else if (subcommand === 'remove') {
      await this.handleRemove(interaction);
    }
  }

  private async handleSetup(interaction: Command.ChatInputCommandInteraction) {
    const guildId = interaction.guildId;
    if (!guildId) return;

    const role = interaction.options.getRole('role', true);
    const target = interaction.options.getString('target', true);

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const guild = interaction.guild;
    if (!guild) return;

    const me = guild.members.me;
    if (!me) return;

    // Check if bot can manage this role
    if (role.position >= me.roles.highest.position) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'このロールはBotの最高ロール以上のため、付与できません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Check if role is manageable
    if (role.managed) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'このロールは統合によって管理されているため、付与できません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Check bot permissions
    if (!me.permissions.has(PermissionFlagsBits.ManageRoles)) {
      const embed = this.container.embedBuilder.error(
        'エラーが発生しました',
        'ロールを管理する権限がありません。'
      );
      await interaction.editReply({ embeds: [embed] });
      return;
    }

    // Save settings
    if (target === 'human') {
      await autoroleSettingsService.setHumanRole(guildId, role.id);
    } else {
      await autoroleSettingsService.setBotRole(guildId, role.id);
    }

    // Success message with Components v2
    const targetName = target === 'human' ? '👤 Human' : '🤖 Bot';
    const successHeader = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# ✅ 自動ロール付与を設定しました')
    );

    const separator = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const successInfo = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `自動ロール付与の設定が完了しました。\n\n` +
        `📋 **対象:** ${targetName}\n` +
        `🎭 **付与するロール:** <@&${role.id}>\n\n` +
        `**動作:**\n` +
        `${targetName}メンバーがサーバーに参加すると、自動的にこのロールが付与されます。`
      )
    );

    const successContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(successHeader)
      .addSeparatorComponents(separator)
      .addSectionComponents(successInfo);

    await interaction.editReply({
      components: [successContainer],
      flags: MessageFlags.IsComponentsV2,
    });
  }

  private async handleRemove(interaction: Command.ChatInputCommandInteraction) {
    const guildId = interaction.guildId;
    if (!guildId) return;

    const target = interaction.options.getString('target', true);

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    // Remove settings
    if (target === 'human') {
      await autoroleSettingsService.setHumanRole(guildId, null);
    } else {
      await autoroleSettingsService.setBotRole(guildId, null);
    }

    // Success message with Components v2
    const targetName = target === 'human' ? '👤 Human' : '🤖 Bot';
    const successHeader = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent('# ✅ 自動ロール付与を削除しました')
    );

    const separator = new SeparatorBuilder()
      .setDivider(true)
      .setSpacing(1);

    const successInfo = new SectionBuilder().addTextDisplayComponents(
      new TextDisplayBuilder().setContent(
        `自動ロール付与の設定が削除されました。\n\n` +
        `📋 **対象:** ${targetName}\n\n` +
        `**状態:**\n` +
        `${targetName}メンバーへの自動ロール付与が無効になりました。`
      )
    );

    const successContainer = new ContainerBuilder()
      .setAccentColor(this.container.colors.success)
      .addSectionComponents(successHeader)
      .addSeparatorComponents(separator)
      .addSectionComponents(successInfo);

    await interaction.editReply({
      components: [successContainer],
      flags: MessageFlags.IsComponentsV2,
    });
  }
}
