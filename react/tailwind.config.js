/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "../aquillm/templates/**/*.html",
  ],
  theme: {
    extend: {
        fontFamily: {
            serif: ['Latin Modern Roman']
        },
        colors: {
            'deep-primary': '#2f6e55',
            'lighter-primary': '#acc5bb',
            'lightest-primary': '#d5e2dd',
            'deep-secondary': '#533a44',
            'lighter-secondary': '#644e57'
        },
    },
},
  plugins: [],
}

