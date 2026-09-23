// Ported from ../../../05_html_tokenizer/html_tokenizer.py
//
// A hand-rolled state machine that turns raw HTML into a stream of typed
// tokens (start tag, end tag, text, comment), including the two cases a
// naive "split on < and >" approach breaks on: comments containing fake
// tags, and <script>/<style> content that must not be tokenized as markup
// even though it's full of < and > characters.
//
// Out of scope, matching the Python original: entity decoding, full
// DOCTYPE parsing, CDATA sections.

export interface StartTagToken {
  kind: 'StartTag';
  name: string;
  attrs: Record<string, string>;
  selfClosing: boolean;
}

export interface EndTagToken {
  kind: 'EndTag';
  name: string;
}

export interface TextToken {
  kind: 'Text';
  data: string;
}

export interface CommentToken {
  kind: 'Comment';
  data: string;
}

export type Token = StartTagToken | EndTagToken | TextToken | CommentToken;

const RAWTEXT_ELEMENTS = new Set(['script', 'style']);
const WHITESPACE = ' \t\n\r\f';

function isAlpha(ch: string | null): boolean {
  return ch !== null && /[a-zA-Z]/.test(ch);
}

function isAlnum(ch: string | null): boolean {
  return ch !== null && /[a-zA-Z0-9]/.test(ch);
}

class HTMLTokenizer {
  private html: string;
  private pos = 0;
  private length: number;
  private tokens: Token[] = [];
  private state: 'DATA' | 'RAWTEXT' = 'DATA';
  private textBuffer: string[] = [];
  private rawtextTagName: string | null = null;

  constructor(html: string) {
    this.html = html;
    this.length = html.length;
  }

  private peek(): string | null {
    return this.pos < this.length ? this.html[this.pos] : null;
  }

  private advance(): string {
    const ch = this.html[this.pos];
    this.pos += 1;
    return ch;
  }

  private emitTextIfAny() {
    if (this.textBuffer.length) {
      this.tokens.push({ kind: 'Text', data: this.textBuffer.join('') });
      this.textBuffer = [];
    }
  }

  run(): Token[] {
    while (this.pos < this.length) {
      if (this.state === 'DATA') this.stepData();
      else this.stepRawtext();
    }
    this.emitTextIfAny();
    return this.tokens;
  }

  private stepData() {
    const ch = this.advance();
    if (ch === '<') this.consumeMarkup();
    else this.textBuffer.push(ch);
  }

  private consumeMarkup() {
    const nxt = this.peek();
    if (nxt === '!') {
      this.advance();
      this.emitTextIfAny();
      if (this.html.slice(this.pos, this.pos + 2) === '--') {
        this.pos += 2;
        this.consumeComment();
      } else {
        this.consumeBogusDeclaration();
      }
      return;
    }
    if (nxt === '/') {
      this.advance();
      this.emitTextIfAny();
      this.consumeEndTag();
      return;
    }
    if (nxt !== null && isAlpha(nxt)) {
      this.emitTextIfAny();
      this.consumeStartTag();
      return;
    }
    this.textBuffer.push('<');
  }

  private consumeName(): string {
    const start = this.pos;
    while (this.peek() !== null && (isAlnum(this.peek()) || '-_:'.includes(this.peek()!))) {
      this.advance();
    }
    return this.html.slice(start, this.pos);
  }

  private skipWhitespace() {
    while (this.peek() !== null && WHITESPACE.includes(this.peek()!)) this.advance();
  }

  private consumeStartTag() {
    const name = this.consumeName().toLowerCase();
    const attrs: Record<string, string> = {};
    let selfClosing = false;
    while (true) {
      this.skipWhitespace();
      const ch = this.peek();
      if (ch === null) break;
      if (ch === '/') {
        this.advance();
        this.skipWhitespace();
        if (this.peek() === '>') {
          this.advance();
          selfClosing = true;
        }
        break;
      }
      if (ch === '>') {
        this.advance();
        break;
      }
      const attrName = this.consumeAttrName();
      if (!attrName) {
        this.advance();
        continue;
      }
      this.skipWhitespace();
      let value = '';
      if (this.peek() === '=') {
        this.advance();
        this.skipWhitespace();
        value = this.consumeAttrValue();
      }
      attrs[attrName.toLowerCase()] = value;
    }

    this.tokens.push({ kind: 'StartTag', name, attrs, selfClosing });
    if (RAWTEXT_ELEMENTS.has(name) && !selfClosing) {
      this.rawtextTagName = name;
      this.state = 'RAWTEXT';
    }
  }

  private consumeAttrName(): string {
    const start = this.pos;
    while (this.peek() !== null && !(WHITESPACE + '=/>').includes(this.peek()!)) this.advance();
    return this.html.slice(start, this.pos);
  }

  private consumeAttrValue(): string {
    const ch = this.peek();
    if (ch === '"' || ch === "'") {
      const quote = this.advance();
      const start = this.pos;
      while (this.peek() !== null && this.peek() !== quote) this.advance();
      const value = this.html.slice(start, this.pos);
      if (this.peek() === quote) this.advance();
      return value;
    }
    const start = this.pos;
    while (this.peek() !== null && !(WHITESPACE + '>').includes(this.peek()!)) this.advance();
    return this.html.slice(start, this.pos);
  }

  private consumeEndTag() {
    const name = this.consumeName().toLowerCase();
    this.skipWhitespace();
    if (this.peek() === '>') this.advance();
    this.tokens.push({ kind: 'EndTag', name });
  }

  private consumeComment() {
    const start = this.pos;
    const end = this.html.indexOf('-->', this.pos);
    if (end === -1) {
      this.tokens.push({ kind: 'Comment', data: this.html.slice(start) });
      this.pos = this.length;
    } else {
      this.tokens.push({ kind: 'Comment', data: this.html.slice(start, end) });
      this.pos = end + 3;
    }
  }

  private consumeBogusDeclaration() {
    const end = this.html.indexOf('>', this.pos);
    this.pos = end === -1 ? this.length : end + 1;
  }

  private stepRawtext() {
    const endMarker = `</${this.rawtextTagName}`;
    const idx = this.html.toLowerCase().indexOf(endMarker, this.pos);
    let data: string;
    if (idx === -1) {
      data = this.html.slice(this.pos);
      this.pos = this.length;
    } else {
      data = this.html.slice(this.pos, idx);
      this.pos = idx;
    }
    if (data) this.tokens.push({ kind: 'Text', data });
    this.state = 'DATA';
  }
}

export function tokenize(html: string): Token[] {
  return new HTMLTokenizer(html).run();
}
