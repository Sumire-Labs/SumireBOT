/**
 * Material 3 Expressive Color System
 * Dynamic and vibrant color palette for Discord embeds
 */

export interface ColorPalette {
  primary: number;
  secondary: number;
  tertiary: number;
  success: number;
  warning: number;
  error: number;
  info: number;
  surface: number;
  surfaceVariant: number;
  onSurface: number;
}

/**
 * Convert hex color to Discord color integer
 */
export function hexToInt(hex: string): number {
  return parseInt(hex.replace('#', ''), 16);
}

/**
 * Default Material 3 Color Palette
 */
export const M3Colors: ColorPalette = {
  primary: hexToInt('#6750A4'),
  secondary: hexToInt('#625B71'),
  tertiary: hexToInt('#7D5260'),
  success: hexToInt('#4CAF50'),
  warning: hexToInt('#FF9800'),
  error: hexToInt('#F44336'),
  info: hexToInt('#2196F3'),
  surface: hexToInt('#1E1E1E'),
  surfaceVariant: hexToInt('#2C2C2C'),
  onSurface: hexToInt('#E6E1E5'),
};

/**
 * Load colors from config
 */
export function loadColorsFromConfig(config: any): ColorPalette {
  if (!config) return M3Colors;

  const designColors = config.design?.colors;
  if (!designColors) return M3Colors;

  return {
    primary: hexToInt(designColors.primary || '#6750A4'),
    secondary: hexToInt(designColors.secondary || '#625B71'),
    tertiary: hexToInt(designColors.tertiary || '#7D5260'),
    success: hexToInt(designColors.success || '#4CAF50'),
    warning: hexToInt(designColors.warning || '#FF9800'),
    error: hexToInt(designColors.error || '#F44336'),
    info: hexToInt(designColors.info || '#2196F3'),
    surface: hexToInt(designColors.surface || '#1E1E1E'),
    surfaceVariant: hexToInt(designColors.surfaceVariant || '#2C2C2C'),
    onSurface: hexToInt(designColors.onSurface || '#E6E1E5'),
  };
}
