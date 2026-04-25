import type { DefuddleResponse, DefuddleOptions } from './types';
type GenericElement = {
    classList?: {
        contains: (className: string) => boolean;
    };
    getAttribute: (name: string) => string | null;
    hasAttribute: (name: string) => boolean;
    querySelector: (selector: string) => Element | null;
    querySelectorAll: (selector: string) => NodeListOf<Element>;
    rows?: ArrayLike<{
        cells?: ArrayLike<{}>;
    }>;
    parentNode?: GenericElement | null;
    nextSibling?: GenericElement | null;
    nodeName: string;
    innerHTML: string;
    children?: ArrayLike<GenericElement>;
    cloneNode: (deep?: boolean) => Node;
    textContent?: string | null;
    attributes?: NamedNodeMap;
    className?: string;
    tagName?: string;
    nodeType: number;
    closest?: (selector: string) => Element | null;
};
export declare function isGenericElement(node: unknown): node is GenericElement;
export declare function asGenericElement(node: any): GenericElement;
export declare function createMarkdownContent(content: string, url: string): string;
export declare function toMarkdown(result: DefuddleResponse, options: DefuddleOptions, url: string): void;
export {};
