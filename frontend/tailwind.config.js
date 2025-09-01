/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // make sure Tailwind scans all your files
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",   // 👈 this fixes border-border
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
    },
  },
  plugins: [],
}
