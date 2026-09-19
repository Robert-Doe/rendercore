// Ported from ../../../10_box_model/box_model.py
//
// Every styled node gets a computed content/padding/border/margin box.
// box-sizing changes what the `width` property NUMBER MEANS, so it must
// be resolved before content width can be computed at all.

import { ComputedStyle } from './cascade';

export function parseLength(value: string | undefined, autoAllowed = false): number | 'auto' {
  const v = (value ?? '').trim();
  if (v === 'auto') return autoAllowed ? 'auto' : 0.0;
  if (!v) return 0.0;
  let numeric = v;
  if (numeric.endsWith('px')) numeric = numeric.slice(0, -2);
  const parsed = parseFloat(numeric);
  return Number.isNaN(parsed) ? 0.0 : parsed;
}

export class EdgeSizes {
  top: number;
  right: number;
  bottom: number;
  left: number;

  constructor(top = 0, right = 0, bottom = 0, left = 0) {
    this.top = top;
    this.right = right;
    this.bottom = bottom;
    this.left = left;
  }

  get horizontal(): number {
    return this.left + this.right;
  }

  get vertical(): number {
    return this.top + this.bottom;
  }
}

export class Box {
  contentWidth: number;
  contentHeight: number;
  padding: EdgeSizes;
  border: EdgeSizes;
  margin: EdgeSizes;

  constructor(contentWidth: number, contentHeight: number, padding: EdgeSizes, border: EdgeSizes, margin: EdgeSizes) {
    this.contentWidth = contentWidth;
    this.contentHeight = contentHeight;
    this.padding = padding;
    this.border = border;
    this.margin = margin;
  }

  get paddingBoxWidth(): number {
    return this.contentWidth + this.padding.horizontal;
  }

  get paddingBoxHeight(): number {
    return this.contentHeight + this.padding.vertical;
  }

  get borderBoxWidth(): number {
    return this.paddingBoxWidth + this.border.horizontal;
  }

  get borderBoxHeight(): number {
    return this.paddingBoxHeight + this.border.vertical;
  }

  get marginBoxWidth(): number {
    return this.borderBoxWidth + this.margin.horizontal;
  }

  get marginBoxHeight(): number {
    return this.borderBoxHeight + this.margin.vertical;
  }
}

export function edges(style: ComputedStyle, prefix: string, uniformKey?: string): EdgeSizes {
  if (uniformKey) {
    const w = parseLength(style[uniformKey] ?? '0') as number;
    return new EdgeSizes(w, w, w, w);
  }
  return new EdgeSizes(
    parseLength(style[`${prefix}-top`] ?? '0') as number,
    parseLength(style[`${prefix}-right`] ?? '0') as number,
    parseLength(style[`${prefix}-bottom`] ?? '0') as number,
    parseLength(style[`${prefix}-left`] ?? '0') as number,
  );
}

export function computeBox(style: ComputedStyle): Box {
  const boxSizing = style['box-sizing'] ?? 'content-box';
  const widthSpec = parseLength(style.width ?? 'auto', true);
  const heightSpec = parseLength(style.height ?? 'auto', true);

  const padding = edges(style, 'padding');
  const border = edges(style, 'border', 'border-width');
  const margin = edges(style, 'margin');

  function resolve(spec: number | 'auto', pad: number, bor: number): number {
    if (spec === 'auto') return 0.0;
    if (boxSizing === 'border-box') return Math.max(0.0, spec - pad - bor);
    return spec;
  }

  const contentWidth = resolve(widthSpec, padding.horizontal, border.horizontal);
  const contentHeight = resolve(heightSpec, padding.vertical, border.vertical);

  return new Box(contentWidth, contentHeight, padding, border, margin);
}
