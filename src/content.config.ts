import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blog = defineCollection({
	// Load Markdown and MDX files in the `src/content/blog/` directory.
	// Note: keeping this Markdown-only for now avoids occasional duplicate-id warnings on Windows.
	loader: glob({ base: './src/content/blog', pattern: '**/*.md' }),
	// Type-check frontmatter using a schema
	schema: z.object({
		title: z.string(),
		description: z.string(),
		// Transform string to Date object
		pubDate: z.coerce.date(),
		updatedDate: z.coerce.date().optional(),
		heroImage: z.string().optional(),
		hidden: z.boolean().optional(),
	}),
});

const pages = defineCollection({
	// Static pages content (services, patents, work, tools, about, contact, testimonials)
	loader: glob({ base: './src/content/pages', pattern: '**/*.md' }),
	schema: z.object({
		title: z.string(),
		description: z.string().optional(),
	}),
});

const home = defineCollection({
	// Homepage content
	loader: glob({ base: './src/content/home', pattern: '**/*.md' }),
	schema: z.object({
		title: z.string(),
		tagline: z.string(),
		intro: z.string(),
	}),
});

const blogPage = defineCollection({
	// Blog listing page settings
	loader: glob({ base: './src/content/blog-page', pattern: '**/*.md' }),
	schema: z.object({
		title: z.string(),
		intro: z.string().optional(),
	}),
});

export const collections = { blog, pages, home, 'blog-page': blogPage };
