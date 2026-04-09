import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const datedContent = z.object({
  title: z.string(),
  pub_date: z.coerce.date(),
  summary: z.string().optional(),
  image: z.string().optional(),
  draft: z.boolean().default(false),
});

const blog = defineCollection({
  loader: glob({ base: "./src/content/blog", pattern: "**/*.md" }),
  schema: datedContent.extend({
    series: z.string().optional(),
    order: z.number().int().optional(),
  }),
});

const lab = defineCollection({
  loader: glob({ base: "./src/content/lab", pattern: "**/*.md" }),
  schema: datedContent,
});

const pubCollection = defineCollection({
  loader: glob({ base: "./src/content/pub", pattern: "**/*.md" }),
  schema: datedContent.extend({
    url: z.string().url().optional(),
    venue: z.string().optional(),
    author: z.string().optional(),
  }),
});

const pages = defineCollection({
  loader: glob({ base: "./src/content/pages", pattern: "**/*.md" }),
  schema: z.object({
    title: z.string(),
    summary: z.string().optional(),
    subtitle: z.string().optional(),
  }),
});

export const collections = {
  blog,
  lab,
  pub: pubCollection,
  pages,
};
