// Theme configuration object
const theme = {
  colors: {
    bg: {
      primary: '#0a0e1a',
      secondary: '#0f1424',
      tertiary: '#141a2e',
      elevated: '#1a2138',
      surface: '#1e2642',
    },
    glass: {
      bg: 'rgba(255, 255, 255, 0.03)',
      bgHover: 'rgba(255, 255, 255, 0.06)',
      bgActive: 'rgba(255, 255, 255, 0.08)',
      border: 'rgba(255, 255, 255, 0.08)',
      borderHover: 'rgba(255, 255, 255, 0.15)',
    },
    accent: {
      cyan: '#00d4ff',
      emerald: '#00e68a',
      amber: '#ffc107',
      red: '#ff4757',
      purple: '#a855f7',
    },
    text: {
      primary: '#f0f2f5',
      secondary: '#8b95a8',
      tertiary: '#5a6478',
      muted: '#3d4556',
      inverse: '#0a0e1a',
    },
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
  },
  radii: {
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '20px',
    '2xl': '28px',
    full: '9999px',
  },
  shadows: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.3)',
    md: '0 4px 16px rgba(0, 0, 0, 0.4)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.5)',
    xl: '0 16px 48px rgba(0, 0, 0, 0.6)',
    glowCyan: '0 0 20px rgba(0, 212, 255, 0.3)',
    glowEmerald: '0 0 20px rgba(0, 230, 138, 0.3)',
    glowRed: '0 0 20px rgba(255, 71, 87, 0.3)',
    glowAmber: '0 0 20px rgba(255, 193, 7, 0.3)',
  },
  // Chart.js theme defaults
  chartDefaults: {
    backgroundColor: 'transparent',
    gridColor: 'rgba(255, 255, 255, 0.04)',
    tickColor: '#5a6478',
    fontFamily: "'Inter', sans-serif",
    fontSize: 11,
  },
};

export default theme;
