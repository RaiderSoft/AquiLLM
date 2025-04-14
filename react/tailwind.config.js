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
          // You can continue using system fonts for Verdana and Times New Roman:
          verdana: ['Verdana', 'sans-serif'],
          timesnewroman: ['"Times New Roman"', 'serif'],
          // Keep your existing defaults too:
          latin_modern_roman: ['Latin Modern Roman', 'serif'],
          sans_serif: ['Helvetica', 'Arial', 'sans-serif']
        },
        colors: {
          // Use the custom property syntax. Tailwind will output utility classes like bg-gray-shade_6.
          gray: {
            shade_f: 'var(--color-gray-shade_f)',
            shade_e: 'var(--color-gray-shade_e)',
            shade_e_i: 'var(--color-gray-shade_e_i)',
            shade_d: 'var(--color-gray-shade_d)',
            shade_c: 'var(--color-gray-shade_c)',
            shade_b: 'var(--color-gray-shade_b)',
            shade_a: 'var(--color-gray-shade_a)',
            shade_9: 'var(--color-gray-shade_9)',
            shade_8: 'var(--color-gray-shade_8)',
            shade_7: 'var(--color-gray-shade_7)',
            shade_6: 'var(--color-gray-shade_6)',
            shade_5: 'var(--color-gray-shade_5)',
            shade_4: 'var(--color-gray-shade_4)',
            shade_3: 'var(--color-gray-shade_3)',
            shade_2: 'var(--color-gray-shade_2)',
            DEFAULT: 'var(--color-gray-DEFAULT)',
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

