/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "../aquillm/templates/**/*.html",
    "../aquillm/aquillm/**/*.py",
  ],
  theme: {
    extend: {
        fontFamily: {
          opendyslexic: ['"OpenDyslexic"', 'sans-serif'],
          lexend: ['Lexend', 'sans-serif'],
          comicsans: ['"Comic Sans"', 'cursive'],
          verdana: ['Verdana', 'sans-serif'],
          timesnewroman: ['"Times New Roman"', 'serif'],
          latin_modern_roman: ['Latin Modern Roman', 'serif'],
          sans_serif: ['Helvetica', 'Arial', 'sans-serif']
        },
        colors: {
          // Use the custom property syntax. Tailwind will output utility classes like bg-scheme-shade_6.
          scheme: {
            shade_15: 'var(--color-scheme-shade-15)',
            shade_14: 'var(--color-scheme-shade-14)',
            shade_13: 'var(--color-scheme-shade-13)',
            shade_12: 'var(--color-scheme-shade-12)',
            shade_11: 'var(--color-scheme-shade-11)',
            shade_10: 'var(--color-scheme-shade-10)',
            shade_9: 'var(--color-scheme-shade-9)',
            shade_8: 'var(--color-scheme-shade-8)',
            shade_7: 'var(--color-scheme-shade-7)',
            shade_6: 'var(--color-scheme-shade-6)',
            shade_5: 'var(--color-scheme-shade-5)',
            shade_4: 'var(--color-scheme-shade-4)',
            shade_3: 'var(--color-scheme-shade-3)',
            shade_2: 'var(--color-scheme-shade-2)',
            shade_1: 'var(--color-scheme-shade-1)',
            DEFAULT: 'var(--color-scheme-shade-1)',
            contrast: 'var(--color-contrast)',
          },
          border:{
            higher_contrast: 'var(--color-border-higher-contrast)',
            high_contrast: 'var(--color-border-high-contrast)',
            mid_contrast: 'var(--color-border-mid-contrast)',
            low_contrast: 'var(--color-border-low-contrast)',
            lower_contrast: 'var(--color-border-lower-contrast)',
            boolean: 'var(--color-border-boolean)',
          },
          text: {
            normal: 'var(--color-text-normal)',
            very_slightly_less_contrast: 'var(--color-text-very-slightly-less-contrast)',
            slightly_less_contrast: 'var(--color-text-slightly-less-contrast)',
            less_contrast: 'var(--color-text-less-contrast)',
            low_contrast: 'var(--color-text-low-contrast)',
            lower_contrast: 'var(--color-text-lower-contrast)',
          },
          accent: {
            light: 'var(--color-accent-light)',
            DEFAULT: 'var(--color-accent-DEFAULT)',
            dark: 'var(--color-accent-dark)',
          },
          secondary_accent: {
            light: 'var(--color-secondary_accent-light)',
            DEFAULT: 'var(--color-secondary_accent-DEFAULT)',
            dark: 'var(--color-secondary_accent-dark)',
          },
          red: {
            DEFAULT: 'var(--color-red-DEFAULT)',
            dark: 'var(--color-red-dark)',
          },
          green: {
            DEFAULT: 'var(--color-green-DEFAULT)',
            dark: 'var(--color-green-dark)',
          },
          slight_muted_white: {
            DEFAULT: 'var(--color-slightly-muted-white)',
          },
          tool_details:{
            assistant: 'var(--color-tool-details-section-assistant)',
            tool: 'var(--color-tool-details-section-tool)',
          }
        },

        keyframes: {
          slideOut: {
            '0%': { transform: 'translateX(0)' },
            '100%': { transform: 'translateX(-200px)' },
          },
          animation: {
            'slide-out': 'slideOut 0.25s ease-in-out forwards',
          },
          transitionDelay: {
            '150': '150ms',
          },
        },
    },
},
  plugins: [],
}

