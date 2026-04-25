"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isElement = isElement;
exports.isTextNode = isTextNode;
exports.isCommentNode = isCommentNode;
exports.getComputedStyle = getComputedStyle;
exports.getWindow = getWindow;
exports.textPreview = textPreview;
exports.logDebug = logDebug;
const NODE_TYPE = {
    ELEMENT_NODE: 1,
    ATTRIBUTE_NODE: 2,
    TEXT_NODE: 3,
    CDATA_SECTION_NODE: 4,
    ENTITY_REFERENCE_NODE: 5,
    ENTITY_NODE: 6,
    PROCESSING_INSTRUCTION_NODE: 7,
    COMMENT_NODE: 8,
    DOCUMENT_NODE: 9,
    DOCUMENT_TYPE_NODE: 10,
    DOCUMENT_FRAGMENT_NODE: 11,
    NOTATION_NODE: 12
};
function isElement(node) {
    return node.nodeType === NODE_TYPE.ELEMENT_NODE;
}
function isTextNode(node) {
    return node.nodeType === NODE_TYPE.TEXT_NODE;
}
function isCommentNode(node) {
    return node.nodeType === NODE_TYPE.COMMENT_NODE;
}
function getComputedStyle(element) {
    const win = getWindow(element.ownerDocument);
    if (!win)
        return null;
    return win.getComputedStyle(element);
}
function getWindow(doc) {
    // First try defaultView
    if (doc.defaultView) {
        return doc.defaultView;
    }
    // Then try ownerWindow
    if (doc.ownerWindow) {
        return doc.ownerWindow;
    }
    // Finally try to get window from document
    if (doc.window) {
        return doc.window;
    }
    return null;
}
function textPreview(el) {
    return (el.textContent || '').trim().substring(0, 200);
}
function logDebug(debug, message, ...args) {
    if (debug) {
        console.log('Defuddle:', message, ...args);
    }
}
//# sourceMappingURL=utils.js.map