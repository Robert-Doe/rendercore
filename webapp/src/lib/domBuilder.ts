// Ported from ../../../06_dom_tree_builder/dom_tree_builder.py
//
// Assembles the tokenizer's flat token stream into a real tree (the DOM),
// including recovering from "broken" HTML the way a real browser does at
// a basic level: an unclosed <p>, an <li> with no closing tag, a stray
// end tag with no matching start tag, void elements.

import { tokenize, Token } from './tokenizer';

export interface ElementNode {
  kind: 'Element';
  tag: string;
  attrs: Record<string, string>;
  children: DomNode[];
  parent: ElementNode | null;
}

export interface TextNode {
  kind: 'Text';
  data: string;
  parent: ElementNode | null;
}

export interface CommentNode {
  kind: 'Comment';
  data: string;
  parent: ElementNode | null;
}

export type DomNode = ElementNode | TextNode | CommentNode;

const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr',
]);

// Simplified "implicit close" rule: only checks the immediate top of the
// open-elements stack, matching the Python original's documented scope
// limitation (a real browser scans further up looking for a boundary
// element).
const AUTO_CLOSE_ON_TOP: Record<string, Set<string>> = {
  p: new Set(['p']),
  li: new Set(['li']),
  tr: new Set(['tr']),
  td: new Set(['td', 'th']),
  th: new Set(['td', 'th']),
};

function makeElement(tag: string, attrs: Record<string, string>, parent: ElementNode | null): ElementNode {
  return { kind: 'Element', tag, attrs, children: [], parent };
}

export function buildTree(tokens: Token[]): ElementNode {
  const root = makeElement('#document', {}, null);
  const stack: ElementNode[] = [root];

  for (const tok of tokens) {
    let top = stack[stack.length - 1];

    if (tok.kind === 'StartTag') {
      const closers = AUTO_CLOSE_ON_TOP[tok.name];
      if (closers && stack.length > 1 && closers.has(stack[stack.length - 1].tag)) {
        stack.pop();
        top = stack[stack.length - 1];
      }

      const el = makeElement(tok.name, { ...tok.attrs }, top);
      top.children.push(el);
      if (!VOID_ELEMENTS.has(tok.name) && !tok.selfClosing) {
        stack.push(el);
      }
    } else if (tok.kind === 'EndTag') {
      let matchIdx = -1;
      for (let i = stack.length - 1; i >= 1; i -= 1) {
        if (stack[i].tag === tok.name) {
          matchIdx = i;
          break;
        }
      }
      if (matchIdx !== -1) {
        stack.length = matchIdx; // closes the match AND any unclosed tags above it
      }
      // else: a stray end tag with no open match, ignored, per spec
    } else if (tok.kind === 'Text') {
      top.children.push({ kind: 'Text', data: tok.data, parent: top });
    } else if (tok.kind === 'Comment') {
      top.children.push({ kind: 'Comment', data: tok.data, parent: top });
    }
  }

  return root;
}

export function parseHtml(html: string): ElementNode {
  return buildTree(tokenize(html));
}

export function* walk(node: DomNode): Generator<ElementNode> {
  if (node.kind === 'Element') {
    yield node;
    for (const child of node.children) {
      yield* walk(child);
    }
  }
}
