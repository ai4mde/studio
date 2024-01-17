import { defineConfig } from "vite";
import Pages from "vite-plugin-pages";
import svgr from "vite-plugin-svgr";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// https://vitejs.dev/config/
export default defineConfig({
  optimizeDeps: {
    exclude: ["@codemirror/state"],
  },
  plugins: [
    svgr(),
    Pages({
      dirs: "src/routes",
    }),
    react(),
    tsconfigPaths(),
  ],
});
