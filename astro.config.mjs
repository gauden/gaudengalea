import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://gaudengalea.com",
  output: "static",
  trailingSlash: "always",
  markdown: {
    drafts: true,
  },
});
