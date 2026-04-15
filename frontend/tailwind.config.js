/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        heading: ['Space Grotesk', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        poppins: ['Space Grotesk', 'sans-serif'],
        inter: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        'supply-blue': {
          DEFAULT: '#2563eb',
          light: '#3b82f6',
          dark: '#1d4ed8',
        },
        'council-purple': {
          DEFAULT: '#7c3aed',
          light: '#8b5cf6',
          dark: '#6d28d9',
        },
        'risk-red': {
          DEFAULT: '#dc2626',
          light: '#ef4444',
          dark: '#b91c1c',
        },
        'success-green': {
          DEFAULT: '#16a34a',
          light: '#22c55e',
          dark: '#15803d',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        council: {
          bg:         '#0a0b14',
          surface:    '#0f1120',
          card:       'rgba(255,255,255,0.04)',
          border:     'rgba(255,255,255,0.08)',
          indigo:     '#6366f1',
          purple:     '#a855f7',
          violet:     '#7c3aed',
          emerald:    '#10b981',
          amber:      '#f59e0b',
          rose:       '#f43f5e',
          cyan:       '#06b6d4',
        }
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          from: { opacity: '0', transform: 'translateX(-12px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          from: { opacity: '0', transform: 'translateY(-10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'bounce-in': {
          '0%': { opacity: '0', transform: 'scale(0.3)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'spin-slow': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        unlockPulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(99, 102, 241, 0)' },
          '50%': { boxShadow: '0 0 0 8px rgba(99, 102, 241, 0.4)' },
        }
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out',
        'slide-in': 'slide-in 0.4s ease-out',
        'slide-up': 'slide-up 0.5s ease-out',
        'slide-down': 'slide-down 0.3s ease-out',
        'scale-in': 'scale-in 0.3s ease-out',
        'bounce-in': 'bounce-in 0.6s ease-out',
        shimmer: 'shimmer 2s linear infinite',
        float: 'float 3s ease-in-out infinite',
        'spin-slow': 'spin-slow 8s linear infinite',
        'unlock-pulse': 'unlockPulse 1.5s ease-in-out',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover': '0 4px 12px -2px rgb(0 0 0 / 0.08), 0 2px 6px -2px rgb(0 0 0 / 0.04)',
        'glow-blue': '0 0 20px rgba(37, 99, 235, 0.15)',
        'glow-purple': '0 0 20px rgba(124, 58, 237, 0.15)',
      },
    },
  },
  plugins: [],
}
