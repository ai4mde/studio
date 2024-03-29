import { sentryVitePlugin } from "@sentry/vite-plugin";
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

    envPrefix: ["VITE_", "AI4MDE_"],

    plugins: [tsconfigPaths(), svgr(), Pages({
        dirs: "src/routes",
    }), react(), sentryVitePlugin({
        org: "ai4mde",
        project: "studio-studio",
        url: "https://sentry.semax.nguml.com"
    })],

    build: {
        sourcemap: true
    }
});
