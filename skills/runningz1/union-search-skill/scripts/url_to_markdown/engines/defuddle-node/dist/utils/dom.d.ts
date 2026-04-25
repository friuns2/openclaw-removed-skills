/**
 * Move all child nodes from source to target.
 * Clears target first, then moves each child node from source.
 */
export declare function transferContent(source: Node, target: Node): void;
/**
 * Read an element's inner HTML.
 */
export declare function serializeHTML(el: {
    innerHTML: string;
}): string;
/**
 * Decode HTML entities in a string (e.g. `&amp;` → `&`).
 * Uses a <textarea> element which is safe for entity decoding.
 */
export declare function decodeHTMLEntities(doc: Document, text: string): string;
/**
 * Check if an element belongs directly to an ancestor table,
 * not to an intervening nested TABLE.
 */
export declare function isDirectTableChild(el: Node, ancestor: Node): boolean;
/**
 * Parse an HTML string into a DocumentFragment.
 * Uses a <template> element when available (safer: no script execution,
 * no resource loading). Falls back to a <div> for environments that
 * don't support template.content (e.g. some server-side DOM libraries).
 */
export declare function parseHTML(doc: Document, html: string): DocumentFragment;
