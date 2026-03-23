// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';
import { visit } from 'unist-util-visit';

/** Strip <p> tags that sneak inside <pre> blocks during Markdown processing. */
function rehypeUnwrapPreParagraphs() {
  return (tree) => {
    visit(tree, 'element', (node) => {
      if (node.tagName !== 'pre') return;
      const unwrap = (children) => {
        const out = [];
        for (const child of children) {
          if (child.type === 'element' && child.tagName === 'p') {
            if (out.length > 0) out.push({ type: 'text', value: '\n\n' });
            out.push(...unwrap(child.children || []));
          } else {
            out.push(child);
          }
        }
        return out;
      };
      // Unwrap inside <pre> and inside <pre><code>
      node.children = unwrap(node.children);
      for (const child of node.children) {
        if (child.type === 'element' && child.tagName === 'code' && child.children) {
          child.children = unwrap(child.children);
        }
      }
    });
  };
}

// https://astro.build/config
export default defineConfig({
site: 'https://michaelbeijer.co.uk',
integrations: [mdx(), sitemap()],
markdown: {
  rehypePlugins: [rehypeUnwrapPreParagraphs],
},
});
