import {
  ContainerBuilder,
  SectionBuilder,
  TextDisplayBuilder,
  SeparatorBuilder,
  MessageFlags,
} from 'discord.js';

console.log('ContainerBuilder:', typeof ContainerBuilder);
console.log('SectionBuilder:', typeof SectionBuilder);
console.log('TextDisplayBuilder:', typeof TextDisplayBuilder);
console.log('SeparatorBuilder:', typeof SeparatorBuilder);
console.log('MessageFlags.IsComponentsV2:', MessageFlags.IsComponentsV2);

try {
  const headerSection = new SectionBuilder().addTextDisplayComponents(
    new TextDisplayBuilder().setContent('# Test Header')
  );

  const separator = new SeparatorBuilder()
    .setDivider(true)
    .setSpacing(1);

  const infoSection = new SectionBuilder().addTextDisplayComponents(
    new TextDisplayBuilder().setContent('Test content')
  );

  const container = new ContainerBuilder()
    .setAccentColor(0x5865F2)
    .addSectionComponents(headerSection)
    .addSeparatorComponents(separator)
    .addSectionComponents(infoSection);

  console.log('\nContainer created successfully!');
  console.log('Container data:', JSON.stringify(container.toJSON(), null, 2));
} catch (error) {
  console.error('\nError creating container:', error);
}
