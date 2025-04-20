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
            serif: ['Latin Modern Roman']
        },
        colors: {
          transparent: 'transparent',
          current: 'currentColor',
            gray: {
              shade_f: '#ffffff',
              shade_e: '#eeeeee',
              shade_d: '#dddddd',
              shade_c: '#cccccc',
              shade_b: '#bbbbbb',
              shade_a: '#aaaaaa',
              shade_9: '#999999',
              shade_8: '#888888',
              shade_7: '#777777',
              shade_6: '#666666',
              shade_5: '#555555',
              shade_4: '#444444',
              shade_3: '#333333',
              shade_2: '#222222',
              DEFAULT: '#111111'
            },
            accent: {
              light: '#A5CCF3',
              DEFAULT: '#1C79D8',
              dark: '#1B4979'
            },
            secondary_accent: {
              light: '#F49071',
              DEFAULT: '#F16C43',
              dark: '#BE380E'
            },
            red: {
              DEFAULT: '#EC3D3D',
              dark: '#8C0D0D'
            },
            green: {
              DEFAULT: '#69E665',
              dark: '#198316'
            },
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
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

