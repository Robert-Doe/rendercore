// Ported from ../../../11_block_inline_layout/block_layout.py
//
// Assigns real x/y/width/height coordinates to a tree of boxes —
// recursively, parent before child for POSITION, children before parent
// for an auto-height parent's SIZE, both in the same recursive call.
//
// Scope: block-level boxes only (display: block, stacked vertically).
// Inline layout and text wrapping are out of scope, matching the Python
// original (Module 12's job).

import { ElementNode } from './domBuilder';
import { ComputedStyle } from './cascade';
import { parseLength, edges, Box } from './boxModel';

export interface ContainingBlock {
  x: number;
  y: number;
  width: number;
}

export interface LayoutBox {
  node: ElementNode;
  x: number; // content box origin
  y: number;
  box: Box;
  children: LayoutBox[];
}

export function marginBoxHeight(lb: LayoutBox): number {
  return lb.box.marginBoxHeight;
}

export function borderBox(lb: LayoutBox): [number, number, number, number] {
  const bx = lb.x - lb.box.padding.left - lb.box.border.left;
  const by = lb.y - lb.box.padding.top - lb.box.border.top;
  return [bx, by, lb.box.borderBoxWidth, lb.box.borderBoxHeight];
}

function resolveSize(
  spec: number | 'auto',
  available: number | null,
  pad: number,
  bor: number,
  boxSizing: string,
): number | null {
  if (spec === 'auto') {
    if (available === null) return null; // "compute from children" — height only
    return Math.max(0.0, available - pad - bor);
  }
  if (boxSizing === 'border-box') return Math.max(0.0, spec - pad - bor);
  return spec;
}

function isBlockChild(node: unknown): node is ElementNode {
  return (node as ElementNode).kind === 'Element';
}

export function layoutBlock(
  node: ElementNode,
  containingBlock: ContainingBlock,
  styles: Map<ElementNode, ComputedStyle>,
): LayoutBox {
  const style = styles.get(node)!;
  const boxSizing = style['box-sizing'] ?? 'content-box';

  const padding = edges(style, 'padding');
  const border = edges(style, 'border', 'border-width');
  const margin = edges(style, 'margin');

  const widthSpec = parseLength(style.width ?? 'auto', true);
  const heightSpec = parseLength(style.height ?? 'auto', true);

  const contentWidth = resolveSize(
    widthSpec,
    containingBlock.width - margin.horizontal,
    padding.horizontal,
    border.horizontal,
    boxSizing,
  ) as number;

  const contentX = containingBlock.x + margin.left + border.left + padding.left;
  const contentY = containingBlock.y + margin.top + border.top + padding.top;

  const children: LayoutBox[] = [];
  let cursorY = contentY;
  for (const child of node.children) {
    if (!isBlockChild(child)) continue;
    const childStyle = styles.get(child);
    if (!childStyle || childStyle.display !== 'block') continue;
    const childCb: ContainingBlock = { x: contentX, y: cursorY, width: contentWidth };
    const childBox = layoutBlock(child, childCb, styles);
    children.push(childBox);
    cursorY += marginBoxHeight(childBox);
  }

  let contentHeight: number;
  if (heightSpec === 'auto') {
    contentHeight = cursorY - contentY;
  } else {
    if (boxSizing === 'border-box') {
      contentHeight = Math.max(0.0, heightSpec - padding.vertical - border.vertical);
    } else {
      contentHeight = heightSpec;
    }
  }

  const box = new Box(contentWidth, contentHeight, padding, border, margin);
  return { node, x: contentX, y: contentY, box, children };
}
