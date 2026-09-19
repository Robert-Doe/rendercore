// Ported from ../../../07_css_parser/css_parser.py
//
// Turns a stylesheet string into a structured list of Rule objects, each
// with a parsed selector list and a parsed declaration list. Deliberately
// does not compute specificity or resolve conflicts — that's the
// cascade's job (cascade.ts / Module 9).

const WHITESPACE = ' \t\n\r\f';

export interface SimpleSelector {
  typeName: string | null;
  id: string | null;
  classes: string[];
}

export interface Selector {
  parts: SimpleSelector[]; // left = ancestor ... right = the element itself
}

export interface Declaration {
  property: string;
  value: string;
  important: boolean;
}

export interface Rule {
  selectors: Selector[];
  declarations: Declaration[];
}

export function selectorToString(sel: Selector): string {
  return sel.parts.map(simpleToString).join(' ');
}

export function simpleToString(p: SimpleSelector): string {
  const t = p.typeName ?? '*';
  const i = p.id ? `#${p.id}` : '';
  const c = p.classes.map((c) => `.${c}`).join('');
  return `${t}${i}${c}`;
}

export function stripComments(css: string): string {
  const out: string[] = [];
  let i = 0;
  const n = css.length;
  while (i < n) {
    if (css.slice(i, i + 2) === '/*') {
      const end = css.indexOf('*/', i + 2);
      i = end === -1 ? n : end + 2;
    } else {
      out.push(css[i]);
      i += 1;
    }
  }
  return out.join('');
}

function skipBlock(css: string, openBraceIdx: number): number {
  let depth = 0;
  let i = openBraceIdx;
  const n = css.length;
  while (i < n) {
    if (css[i] === '{') depth += 1;
    else if (css[i] === '}') {
      depth -= 1;
      if (depth === 0) return i + 1;
    }
    i += 1;
  }
  return n;
}

export function parseStylesheet(cssInput: string): Rule[] {
  const css = stripComments(cssInput);
  const rules: Rule[] = [];
  let i = 0;
  const n = css.length;

  while (i < n) {
    while (i < n && WHITESPACE.includes(css[i])) i += 1;
    if (i >= n) break;

    const braceIdx = css.indexOf('{', i);
    if (braceIdx === -1) break;

    const header = css.slice(i, braceIdx).trim();

    if (header.startsWith('@')) {
      i = skipBlock(css, braceIdx);
      continue;
    }

    const closeIdx = css.indexOf('}', braceIdx);
    if (closeIdx === -1) break;

    const body = css.slice(braceIdx + 1, closeIdx);
    const selectors = header
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .map(parseSelector);
    const declarations = parseDeclarations(body);
    if (selectors.length) rules.push({ selectors, declarations });
    i = closeIdx + 1;
  }

  return rules;
}

export function parseSelector(text: string): Selector {
  const tokens = text.split(/\s+/).filter(Boolean);
  return { parts: tokens.map(parseCompound) };
}

function parseCompound(token: string): SimpleSelector {
  let typeName: string | null = null;
  let id: string | null = null;
  const classes: string[] = [];
  let i = 0;
  const n = token.length;

  if (i < n && token[i] !== '.' && token[i] !== '#') {
    const start = i;
    while (i < n && token[i] !== '.' && token[i] !== '#') i += 1;
    const name = token.slice(start, i);
    typeName = name === '*' ? null : name;
  }

  while (i < n) {
    const marker = token[i];
    i += 1;
    const start = i;
    while (i < n && token[i] !== '.' && token[i] !== '#') i += 1;
    const piece = token.slice(start, i);
    if (marker === '.') classes.push(piece);
    else if (marker === '#') id = piece;
  }

  return { typeName, id, classes };
}

export function parseDeclarations(text: string): Declaration[] {
  const declarations: Declaration[] = [];
  for (const rawPart of text.split(';')) {
    const part = rawPart.trim();
    if (!part || !part.includes(':')) continue;
    const idx = part.indexOf(':');
    let prop = part.slice(0, idx).trim().toLowerCase();
    let value = part.slice(idx + 1).trim();
    let important = false;
    if (value.toLowerCase().endsWith('!important')) {
      value = value.slice(0, value.length - '!important'.length).trim();
      important = true;
    }
    declarations.push({ property: prop, value, important });
  }
  return declarations;
}
