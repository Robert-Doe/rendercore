import './style.css';
import { tokenize, Token } from './lib/tokenizer';
import { buildTree, DomNode, ElementNode } from './lib/domBuilder';
import { parseStylesheet, Rule, selectorToString } from './lib/cssParser';
import { computeAll, ComputedStyle } from './lib/cascade';
import { layoutBlock, LayoutBox, borderBox } from './lib/blockLayout';

const HTML_PRESET = `<body>
  <div id="outer">
    <div id="a" class="box">A</div>
    <div id="b" class="box">
      <div id="b1">B1</div>
      <div id="b2">B2</div>
    </div>
  </div>
</body>`;

const CSS_PRESET = `body, div { display: block; }

#outer {
  width: 420px;
  padding-top: 12px; padding-right: 12px;
  padding-bottom: 12px; padding-left: 12px;
  border-width: 2px;
}

.box {
  border-width: 1px;
  padding-top: 8px; padding-right: 8px;
  padding-bottom: 8px; padding-left: 8px;
  margin-bottom: 14px;
}

#a { height: 46px; }
#a.box { color: red; }

#b { border-width: 2px; }
#b1 { height: 30px; }
#b2 { height: 40px; margin-top: 10px; }

nav a.active { color: red; }
nav a { color: blue; }`;

type TabId = 'tokens' | 'dom' | 'css' | 'styles' | 'layout';

const TAB_LABELS: Record<TabId, string> = {
  tokens: 'HTML Tokens',
  dom: 'DOM Tree',
  css: 'CSS Rules',
  styles: 'Computed Styles',
  layout: 'Box Layout',
};

interface PipelineResult {
  tokens: Token[];
  dom: ElementNode;
  rules: Rule[];
  styles: Map<ElementNode, ComputedStyle>;
  layout: LayoutBox | null;
  error: string | null;
}

let activeTab: TabId = 'tokens';
let lastResult: PipelineResult | null = null;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderApp() {
  const app = document.getElementById('app')!;
  app.innerHTML = `
    <div class="topbar">
      <div class="brand">rendercore</div>
      <div class="links">
        <a href="https://github.com/Robert-Doe/rendercore" target="_blank" rel="noopener">GitHub</a>
        <a href="https://robertdoe.com" target="_blank" rel="noopener">&larr; robertdoe.com</a>
      </div>
    </div>

    <div class="hero">
      <h1>Rendering Pipeline Visualizer</h1>
      <p>A browser engine, one module at a time. This page runs a faithful
      TypeScript port of the course's HTML tokenizer, DOM tree builder, CSS parser,
      selector matcher, cascade, and block layout algorithms on whatever HTML and
      CSS you type below.</p>
      <div class="modules">
        <span class="pill">05_html_tokenizer</span>
        <span class="pill">06_dom_tree_builder</span>
        <span class="pill">07_css_parser</span>
        <span class="pill">08_selector_matching</span>
        <span class="pill">09_cascade</span>
        <span class="pill">10_box_model</span>
        <span class="pill">11_block_inline_layout</span>
      </div>
    </div>

    <div class="demo-grid">
      <div class="card">
        <h2>Input</h2>
        <div class="field-label">HTML</div>
        <textarea id="html-input" spellcheck="false">${escapeHtml(HTML_PRESET)}</textarea>
        <div class="field-label">CSS</div>
        <textarea id="css-input" spellcheck="false" style="min-height:160px">${escapeHtml(CSS_PRESET)}</textarea>
        <button class="run-btn" id="run-btn">Run pipeline &rarr;</button>
        <div class="presets">
          <button class="preset-btn" id="preset-default">Default example</button>
          <button class="preset-btn" id="preset-broken">Broken HTML recovery</button>
          <button class="preset-btn" id="preset-cascade">Cascade &amp; specificity</button>
        </div>
      </div>

      <div class="card">
        <h2>Pipeline output</h2>
        <div class="tabs" id="tabs"></div>
        <div id="tab-content"></div>
      </div>
    </div>

    <footer>
      Built as a real port of the rendercore course modules &middot;
      <a href="https://github.com/Robert-Doe/rendercore" target="_blank" rel="noopener">source on GitHub</a>
    </footer>
  `;

  const htmlInput = document.getElementById('html-input') as HTMLTextAreaElement;
  const cssInput = document.getElementById('css-input') as HTMLTextAreaElement;

  document.getElementById('run-btn')!.addEventListener('click', () => {
    runPipeline(htmlInput.value, cssInput.value);
  });

  document.getElementById('preset-default')!.addEventListener('click', () => {
    htmlInput.value = HTML_PRESET;
    cssInput.value = CSS_PRESET;
    runPipeline(htmlInput.value, cssInput.value);
  });

  document.getElementById('preset-broken')!.addEventListener('click', () => {
    htmlInput.value = `<ul>\n  <li>One\n  <li>Two\n  <li>Three\n</ul>\n<p>Unclosed paragraph\n<p>Second paragraph auto-closes the first`;
    cssInput.value = `ul, li, p { display: block; }\nli { padding-top: 4px; padding-bottom: 4px; }`;
    runPipeline(htmlInput.value, cssInput.value);
  });

  document.getElementById('preset-cascade')!.addEventListener('click', () => {
    htmlInput.value = `<body>\n  <p class="highlight">Text <span>inner</span></p>\n  <div id="special" class="override">Important test</div>\n</body>`;
    cssInput.value = `body, p, div, span { display: block; }\n.highlight { color: red; }\np { color: black; }\n#special { color: navy; }\n.override { color: orange !important; }`;
    runPipeline(htmlInput.value, cssInput.value);
  });

  renderTabs();
  runPipeline(htmlInput.value, cssInput.value);
}

function runPipeline(html: string, css: string) {
  try {
    const tokens = tokenize(html);
    const dom = buildTree(tokens);
    const rules = parseStylesheet(css);
    const styles = computeAll(dom, rules);

    let layout: LayoutBox | null = null;
    const bodyEl = [...dom.children].find(
      (c): c is ElementNode => c.kind === 'Element' && c.tag === 'body',
    );
    const rootForLayout = bodyEl ?? dom.children.find((c): c is ElementNode => c.kind === 'Element');
    if (rootForLayout && styles.get(rootForLayout)?.display === 'block') {
      layout = layoutBlock(rootForLayout, { x: 0, y: 0, width: 640 }, styles);
    }

    lastResult = { tokens, dom, rules, styles, layout, error: null };
  } catch (e) {
    lastResult = {
      tokens: [],
      dom: buildTree([]),
      rules: [],
      styles: new Map(),
      layout: null,
      error: e instanceof Error ? e.message : String(e),
    };
  }
  renderTabContent();
}

function renderTabs() {
  const tabsEl = document.getElementById('tabs')!;
  tabsEl.innerHTML = (Object.keys(TAB_LABELS) as TabId[])
    .map((id) => `<button class="tab-btn${id === activeTab ? ' active' : ''}" data-tab="${id}">${TAB_LABELS[id]}</button>`)
    .join('');
  tabsEl.querySelectorAll<HTMLButtonElement>('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab as TabId;
      renderTabs();
      renderTabContent();
    });
  });
}

function renderTabContent() {
  const el = document.getElementById('tab-content')!;
  if (!lastResult) {
    el.innerHTML = '<div class="empty-state">Run the pipeline to see output.</div>';
    return;
  }

  if (lastResult.error) {
    el.innerHTML = `<div class="error-box">Pipeline error: ${escapeHtml(lastResult.error)}</div>`;
    return;
  }

  switch (activeTab) {
    case 'tokens':
      el.innerHTML = renderTokens(lastResult.tokens);
      break;
    case 'dom':
      el.innerHTML = renderDom(lastResult.dom);
      break;
    case 'css':
      el.innerHTML = renderRules(lastResult.rules);
      break;
    case 'styles':
      el.innerHTML = renderStyles(lastResult.dom, lastResult.styles);
      break;
    case 'layout':
      el.innerHTML = renderLayout(lastResult.layout);
      break;
  }
}

function renderTokens(tokens: Token[]): string {
  if (!tokens.length) return '<div class="empty-state">No tokens.</div>';
  const lines = tokens.map((t, i) => {
    const idx = `<span class="tok-punc">[${String(i).padStart(2, '0')}]</span>`;
    if (t.kind === 'StartTag') {
      const attrs = Object.entries(t.attrs)
        .map(([k, v]) => ` <span class="tok-attr">${escapeHtml(k)}</span>=<span class="tok-str">"${escapeHtml(v)}"</span>`)
        .join('');
      return `${idx} <span class="tok-punc">&lt;</span><span class="tok-tag">${escapeHtml(t.name)}</span>${attrs}${t.selfClosing ? ' <span class="tok-punc">/</span>' : ''}<span class="tok-punc">&gt;</span>`;
    }
    if (t.kind === 'EndTag') {
      return `${idx} <span class="tok-punc">&lt;/</span><span class="tok-tag">${escapeHtml(t.name)}</span><span class="tok-punc">&gt;</span>`;
    }
    if (t.kind === 'Text') {
      const trimmed = t.data.replace(/\n/g, '\\n');
      return `${idx} <span class="tok-text">Text(${escapeHtml(JSON.stringify(trimmed))})</span>`;
    }
    return `${idx} <span class="tok-comment">Comment(${escapeHtml(JSON.stringify(t.data))})</span>`;
  });
  return `<div class="output-panel">${lines.join('\n')}</div>`;
}

function renderDom(root: ElementNode): string {
  const lines: string[] = [];
  function walk(node: DomNode, depth: number) {
    const indent = '  '.repeat(depth);
    if (node.kind === 'Element') {
      const attrStr = Object.entries(node.attrs)
        .map(([k, v]) => ` ${k}="${escapeHtml(v)}"`)
        .join('');
      lines.push(`${indent}<span class="tree-tag">&lt;${escapeHtml(node.tag)}${attrStr}&gt;</span>`);
      for (const child of node.children) walk(child, depth + 1);
    } else if (node.kind === 'Text') {
      lines.push(`${indent}<span class="tree-text">Text(${escapeHtml(JSON.stringify(node.data))})</span>`);
    } else {
      lines.push(`${indent}<span class="tree-comment">Comment(${escapeHtml(JSON.stringify(node.data))})</span>`);
    }
  }
  walk(root, 0);
  return `<div class="output-panel"><div class="tree-line">${lines.join('\n')}</div></div>`;
}

function renderRules(rules: Rule[]): string {
  if (!rules.length) return '<div class="empty-state">No rules parsed.</div>';
  const blocks = rules.map((r) => {
    const sel = r.selectors.map(selectorToString).join(', ');
    const decls = r.declarations
      .map(
        (d) =>
          `  <span class="rule-decl-prop">${escapeHtml(d.property)}</span>: <span class="rule-decl-val">${escapeHtml(d.value)}</span>${d.important ? ' <span class="rule-important">!important</span>' : ''};`,
      )
      .join('\n');
    return `<div class="rule-block"><span class="rule-sel">${escapeHtml(sel)}</span> {\n${decls}\n}</div>`;
  });
  return `<div class="output-panel">${blocks.join('\n')}</div>`;
}

function renderStyles(root: ElementNode, styles: Map<ElementNode, ComputedStyle>): string {
  const blocks: string[] = [];
  function walk(node: DomNode) {
    if (node.kind === 'Element') {
      const style = styles.get(node);
      if (style) {
        const attrStr = Object.entries(node.attrs)
          .map(([k, v]) => ` ${k}="${escapeHtml(v)}"`)
          .join('');
        const propLines = Object.entries(style)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => `  <span class="style-prop">${escapeHtml(k)}</span>: <span class="style-val">${escapeHtml(v)}</span>;`)
          .join('\n');
        blocks.push(
          `<div class="style-node"><span class="style-node-tag">&lt;${escapeHtml(node.tag)}${attrStr}&gt;</span>\n${propLines}</div>`,
        );
      }
      for (const child of node.children) walk(child);
    }
  }
  walk(root);
  if (!blocks.length) return '<div class="empty-state">No elements to style.</div>';
  return `<div class="output-panel">${blocks.join('\n')}</div>`;
}

const DEPTH_COLORS = ['#d4a017', '#7ec3e0', '#4ade80', '#f87171', '#c084fc', '#fb923c'];

function renderLayout(layout: LayoutBox | null): string {
  if (!layout) {
    return '<div class="empty-state">No block-level layout root found. Make sure your top-level element (e.g. &lt;body&gt;) has display: block.</div>';
  }

  const boxes: string[] = [];
  function walk(lb: LayoutBox, depth: number) {
    const [bx, by, bw, bh] = borderBox(lb);
    const color = DEPTH_COLORS[depth % DEPTH_COLORS.length];
    const tag = lb.node.tag;
    const ident = lb.node.attrs.id ? `#${lb.node.attrs.id}` : '';
    boxes.push(`
      <div style="
        position:absolute;
        left:${bx}px; top:${by}px;
        width:${Math.max(bw, 2)}px; height:${Math.max(bh, 2)}px;
        border:2px solid ${color};
        background:${color}1a;
        box-sizing:border-box;
      ">
        <div style="
          position:absolute; top:2px; left:4px;
          font-family:var(--mono); font-size:10px; color:${color};
          white-space:nowrap; pointer-events:none;
        ">${escapeHtml(tag)}${escapeHtml(ident)} &middot; ${Math.round(lb.box.contentWidth)}&times;${Math.round(lb.box.contentHeight)}</div>
      </div>
    `);
    for (const child of lb.children) walk(child, depth + 1);
  }
  walk(layout, 0);

  const [, , totalW] = borderBox(layout);
  let maxBottom = 0;
  (function measure(lb: LayoutBox) {
    const [, by, , bh] = borderBox(lb);
    maxBottom = Math.max(maxBottom, by + bh);
    for (const c of lb.children) measure(c);
  })(layout);

  return `
    <div class="layout-canvas-wrap">
      <div style="position:relative; width:${Math.max(totalW, 100) + 20}px; height:${maxBottom + 20}px;">
        ${boxes.join('')}
      </div>
    </div>
  `;
}

renderApp();
