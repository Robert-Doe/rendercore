// Ported from ../../../09_cascade/cascade.py
//
// Given several matching, conflicting rules for the same element and
// property, picks exactly one final value — deterministically — using
// specificity, source order, and !important, in the correct precedence
// order. Also implements inheritance and fallback to an initial value.

import { ElementNode } from './domBuilder';
import { Rule, Selector } from './cssParser';
import { matchesSelector } from './selectorMatching';

const INHERITED_PROPERTIES = new Set([
  'color', 'font-family', 'font-size', 'font-weight', 'line-height', 'text-align',
]);

const INITIAL_VALUES: Record<string, string> = {
  color: 'black',
  'font-weight': 'normal',
  'font-size': '16px',
  display: 'inline',
};

export type Specificity = [number, number, number];

export function specificity(selector: Selector): Specificity {
  const ids = selector.parts.filter((p) => p.id).length;
  const classes = selector.parts.reduce((sum, p) => sum + p.classes.length, 0);
  const types = selector.parts.filter((p) => p.typeName).length;
  return [ids, classes, types];
}

function cmpSpecificity(a: Specificity, b: Specificity): number {
  for (let i = 0; i < 3; i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

interface Candidate {
  spec: Specificity;
  orderIdx: number;
  important: boolean;
  value: string;
}

export type ComputedStyle = Record<string, string>;

export function computeStyle(
  node: ElementNode,
  rules: Rule[],
  parentStyle: ComputedStyle | null,
): ComputedStyle {
  const candidates = new Map<string, Candidate[]>();

  rules.forEach((rule, orderIdx) => {
    const matched = rule.selectors.filter((s) => matchesSelector(node, s));
    if (!matched.length) return;
    let best = specificity(matched[0]);
    for (const s of matched.slice(1)) {
      const spec = specificity(s);
      if (cmpSpecificity(spec, best) > 0) best = spec;
    }
    for (const decl of rule.declarations) {
      const list = candidates.get(decl.property) ?? [];
      list.push({ spec: best, orderIdx, important: decl.important, value: decl.value });
      candidates.set(decl.property, list);
    }
  });

  const computed: ComputedStyle = {};
  for (const [prop, cands] of candidates) {
    const importantCands = cands.filter((c) => c.important);
    const pool = importantCands.length ? importantCands : cands;
    let best = pool[0];
    for (const c of pool.slice(1)) {
      const specCmp = cmpSpecificity(c.spec, best.spec);
      if (specCmp > 0 || (specCmp === 0 && c.orderIdx > best.orderIdx)) {
        best = c;
      }
    }
    computed[prop] = best.value;
  }

  if (parentStyle) {
    for (const prop of INHERITED_PROPERTIES) {
      if (!(prop in computed) && prop in parentStyle) {
        computed[prop] = parentStyle[prop];
      }
    }
  }

  for (const [prop, initial] of Object.entries(INITIAL_VALUES)) {
    if (!(prop in computed)) computed[prop] = initial;
  }

  return computed;
}

export function computeAll(root: ElementNode, rules: Rule[]): Map<ElementNode, ComputedStyle> {
  const result = new Map<ElementNode, ComputedStyle>();

  function visit(node: ElementNode, parentStyle: ComputedStyle | null) {
    const style = computeStyle(node, rules, parentStyle);
    result.set(node, style);
    for (const child of node.children) {
      if (child.kind === 'Element') visit(child, style);
    }
  }

  visit(root, null);
  return result;
}
