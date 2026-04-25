"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.transferContent = transferContent;
exports.serializeHTML = serializeHTML;
exports.decodeHTMLEntities = decodeHTMLEntities;
exports.isDirectTableChild = isDirectTableChild;
exports.parseHTML = parseHTML;
/**
 * Move all child nodes from source to target.
 * Clears target first, then moves each child node from source.
 */
function transferContent(source, target) {
    if ('replaceChildren' in target) {
        target.replaceChildren();
    }
    else {
        while (target.firstChild) {
            target.removeChild(target.firstChild);
        }
    }
    while (source.firstChild) {
        target.appendChild(source.firstChild);
    }
}
/**
 * Read an element's inner HTML.
 */
function serializeHTML(el) {
    return el.innerHTML;
}
/**
 * Decode HTML entities in a string (e.g. `&amp;` → `&`).
 * Uses a <textarea> element which is safe for entity decoding.
 */
function decodeHTMLEntities(doc, text) {
    const textarea = doc.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}
/**
 * Check if an element belongs directly to an ancestor table,
 * not to an intervening nested TABLE.
 */
function isDirectTableChild(el, ancestor) {
    let parent = el.parentNode;
    while (parent && parent !== ancestor) {
        if (parent.nodeName === 'TABLE')
            return false;
        parent = parent.parentNode;
    }
    return parent === ancestor;
}
/**
 * Parse an HTML string into a DocumentFragment.
 * Uses a <template> element when available (safer: no script execution,
 * no resource loading). Falls back to a <div> for environments that
 * don't support template.content (e.g. some server-side DOM libraries).
 */
function parseHTML(doc, html) {
    if (!html)
        return doc.createDocumentFragment();
    const template = doc.createElement('template');
    template.innerHTML = html;
    if (template.content) {
        return template.content;
    }
    // Fallback for environments without template.content support
    const div = doc.createElement('div');
    div.innerHTML = html;
    const fragment = doc.createDocumentFragment();
    while (div.firstChild) {
        fragment.appendChild(div.firstChild);
    }
    return fragment;
}
//# sourceMappingURL=dom.js.map