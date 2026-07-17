import { getCollection } from 'astro:content';
import { SITE_DESCRIPTION, SITE_TITLE } from '../consts';

/**
 * llms.txt — a machine-readable index of this site for AI agents
 * (https://llmstxt.org/). Mirrors the rss.xml.js pattern: generated at
 * build time from the same content collections the pages use.
 * A full-content companion lives at /llms-full.txt.
 */
export async function GET(context) {
	const site = (context.site?.href ?? 'https://beijer.uk/').replace(/\/$/, '');
	const posts = (await getCollection('blog'))
		.filter((p) => !p.data.hidden)
		.sort((a, b) => b.data.pubDate - a.data.pubDate);

	const staticPages = [
		['About', '/about', 'Who Michael Beijer is: Dutch–English patent and technical translator and translation-tech developer'],
		['Services', '/services', 'Translation, MT post-editing, terminology and consultancy services'],
		['Patents', '/patents', 'Patent translation specialisation and experience'],
		['Tools', '/tools', 'Software and tools built by Michael (Supervertaler, Beijerterm, and more)'],
		['Testimonials', '/testimonials', 'Client testimonials'],
		['Links', '/links', 'Curated links'],
		['Contact', '/contact', 'How to get in touch'],
	];

	const lines = [
		`# ${SITE_TITLE}`,
		'',
		`> ${SITE_DESCRIPTION}`,
		'',
		'Personal site of Michael Beijer: Dutch–English patent/technical translator,',
		'terminologist, and developer of translation tools (Supervertaler, Beijerterm).',
		'',
		'## Pages',
		'',
		...staticPages.map(([t, path, d]) => `- [${t}](${site}${path}): ${d}`),
		'',
		'## Blog',
		'',
		...posts.map(
			(p) => `- [${p.data.title}](${site}/blog/${p.id}/): ${p.data.description}`
		),
		'',
		'## Optional',
		'',
		`- [Full content dump](${site}/llms-full.txt): all blog posts in one Markdown file`,
		'- [Supervertaler docs](https://docs.supervertaler.com/llms.txt): AI-readable docs for the Supervertaler translation tools',
		'- [Beijerterm](https://beijerterm.com/llms.txt): Michael\'s Dutch–English terminology site',
		'',
	];

	return new Response(lines.join('\n'), {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
}
