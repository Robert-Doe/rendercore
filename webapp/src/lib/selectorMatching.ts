// Ported from ../../../08_selector_matching/selector_matching.py
//
// Given a DOM node and a parsed rule list, determines exactly which
// rules' selectors match that node, walking ancestors for descendant
// combinators, and correctly not matching descendants of an element
// against a selector that targets the element itself.

import { ElementNode } from './domBuilder';
import { Rule, Selector, SimpleSelector } from './cssParser';

export function nodeClasses(node: ElementNode): Set<string> {
  return new Set((node.attrs.class ?? '').split(/\s+/).filter(Boolean));
}

export function nodeId(node: ElementNode): string | undefined {
  return node.attrs.id;
}

export function matchesSimple(node: ElementNode, simple: SimpleSelector): boolean {
  if (simple.typeName !== null && node.tag !== simple.typeName) return false;
  if (simple.id !== null && nodeId(node) !== simple.id) return false;
  if (simple.classes.length > 0) {
    const classes = nodeClasses(node);
    if (!simple.classes.every((c) => classes.has(c))) return false;
  }
  return true;
}

function findMatchingAncestor(node: ElementNode, simple: SimpleSelector): ElementNode | null {
  let ancestor = node.parent;
  while (ancestor !== null) {
    if (matchesSimple(ancestor, simple)) return ancestor;
    ancestor = ancestor.parent;
  }
  return null;
}

export function matchesSelector(node: ElementNode, selector: Selector): boolean {
  const parts = selector.parts;
  if (!parts.length) return false;
  if (!matchesSimple(node, parts[parts.length - 1])) return false;

  let current: ElementNode | null = node;
  for (let i = parts.length - 2; i >= 0; i -= 1) {
    current = findMatchingAncestor(current!, parts[i]);
    if (current === null) return false;
  }
  return true;
}

export function matchesRule(node: ElementNode, rule: Rule): boolean {
  return rule.selectors.some((sel) => matchesSelector(node, sel));
}

export function matchingRules(node: ElementNode, rules: Rule[]): Rule[] {
  return rules.filter((r) => matchesRule(node, r));
}
