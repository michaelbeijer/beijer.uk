import { getCollection } from 'astro:content';
import { SITE_DESCRIPTION, SITE_TITLE } from '../consts';

/**
 * llms-full.txt — the blog's full content as one Markdown file, for AI
 * agents that want the substance rather than the /llms.txt index.
 * Raw Markdown bodies straight from the content collection.
 */
export async function GET(context) {
	const site = (context.site?.href ?? 'https://beijer.uk/').replace(/\/$/, '');
	const posts = (await getCollection('blog'))
		.filter((p) => !p.data.hidden)
		.sort((a, b) => b.data.pubDate - a.data.pubDate);

	const parts = [
		`# ${SITE_TITLE} — full content`,
		'',
		`> ${SITE_DESCRIPTION}`,
		'',
	];

	for (const p of posts) {
		const date = p.data.pubDate.toISOString().slice(0, 10);
		parts.push('---', '', `# ${p.data.title}`, '');
		parts.push(`Published: ${date} · ${site}/blog/${p.id}/`, '');
		if (p.data.description) parts.push(`> ${p.data.description}`, '');
		parts.push((p.body ?? '').trim(), '');
	}

	return new Response(parts.join('\n'), {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
}
