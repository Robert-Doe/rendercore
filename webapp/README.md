# Rendercore Webapp — Rendering Pipeline Visualizer

An interactive, in-browser demo of the actual rendering pipeline built across
this course's modules. It is a faithful TypeScript port of the real
algorithms in:

- `05_html_tokenizer/html_tokenizer.py` → `src/lib/tokenizer.ts`
- `06_dom_tree_builder/dom_tree_builder.py` → `src/lib/domBuilder.ts`
- `07_css_parser/css_parser.py` → `src/lib/cssParser.ts`
- `08_selector_matching/selector_matching.py` → `src/lib/selectorMatching.ts`
- `09_cascade/cascade.py` → `src/lib/cascade.ts`
- `10_box_model/box_model.py` → `src/lib/boxModel.ts`
- `11_block_inline_layout/block_layout.py` → `src/lib/blockLayout.ts`

Type in HTML + CSS and watch it flow through tokenizing, tree building,
parsing, selector matching, cascade resolution, and block layout — with a
to-scale box diagram at the end, positioned by the real ported layout
algorithm.

## Local development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output goes to `dist/`.

## Static hosting

This is a static site — deploy `dist/` to any static host:

- **Vercel / Netlify / Cloudflare Pages**: set the project root to `webapp`,
  build command to `npm run build`, and output directory to `dist`.
