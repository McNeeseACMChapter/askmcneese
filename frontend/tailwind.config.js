/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        mcneese: {
          blue: "#00549F",
          gold: "#F2A900",
          dark: "#003B6F",
        },
      },
    },
  },
  plugins: [],
};
