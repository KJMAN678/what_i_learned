import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const weekly = defineCollection({
  loader: glob({ pattern: '*.md', base: './weekly' }),
  schema: z.object({
    tags: z.array(z.string().min(1)).min(1),
    summary: z.string().optional(),
  }),
});

export const collections = { weekly };
