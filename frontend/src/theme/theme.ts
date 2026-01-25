'use client';

import { createTheme, ThemeOptions } from '@mui/material/styles';

// SumireBot のカラースキーム
const colors = {
  primary: '#9B59B6',      // メインカラー（紫）
  secondary: '#3498DB',    // セカンダリ（青）
  success: '#2ECC71',      // 成功
  error: '#E74C3C',        // エラー
  warning: '#F39C12',      // 警告
  info: '#3498DB',         // 情報
  discord: '#5865F2',      // Discord ブランドカラー
};

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary,
      light: '#B980D1',
      dark: '#7D3C98',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: colors.secondary,
      light: '#5DADE2',
      dark: '#2471A3',
      contrastText: '#FFFFFF',
    },
    success: {
      main: colors.success,
      light: '#58D68D',
      dark: '#239B56',
      contrastText: '#FFFFFF',
    },
    error: {
      main: colors.error,
      light: '#EC7063',
      dark: '#B03A2E',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: colors.warning,
      light: '#F5B041',
      dark: '#B9770E',
      contrastText: '#000000',
    },
    info: {
      main: colors.info,
      light: '#5DADE2',
      dark: '#2471A3',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#1a1a2e',
      paper: '#16213e',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#B0B0B0',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Noto Sans JP"',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '4px 8px',
          '&.Mui-selected': {
            backgroundColor: 'rgba(155, 89, 182, 0.2)',
            '&:hover': {
              backgroundColor: 'rgba(155, 89, 182, 0.3)',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          width: 42,
          height: 26,
          padding: 0,
        },
        switchBase: {
          padding: 0,
          margin: 2,
          transitionDuration: '300ms',
          '&.Mui-checked': {
            transform: 'translateX(16px)',
            '& + .MuiSwitch-track': {
              backgroundColor: colors.primary,
              opacity: 1,
            },
          },
        },
        thumb: {
          boxSizing: 'border-box',
          width: 22,
          height: 22,
        },
        track: {
          borderRadius: 13,
          backgroundColor: '#39393D',
          opacity: 1,
        },
      },
    },
  },
};

const theme = createTheme(themeOptions);

export default theme;
export { colors };
