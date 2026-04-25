export declare function isElement(node: Node): node is Element;
export declare function isTextNode(node: Node): node is Text;
export declare function isCommentNode(node: Node): node is Comment;
export declare function getComputedStyle(element: Element): CSSStyleDeclaration | null;
export declare function getWindow(doc: Document): Window | null;
export declare function textPreview(el: Element): string;
export declare function logDebug(debug: boolean, message: string, ...args: any[]): void;
