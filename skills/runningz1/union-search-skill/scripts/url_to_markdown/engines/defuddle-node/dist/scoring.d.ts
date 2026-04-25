import { DebugRemoval } from './types';
export interface ContentScore {
    score: number;
    element: Element;
}
export declare class ContentScorer {
    private doc;
    private debug;
    constructor(doc: Document, debug?: boolean);
    static scoreElement(element: Element): number;
    static findBestElement(elements: Element[], minScore?: number): Element | null;
    /**
     * Scores blocks based on their content and structure
     * and removes those that are likely not content.
     */
    static scoreAndRemove(doc: Document, debug?: boolean, debugRemovals?: DebugRemoval[]): void;
    /**
     * Determines if an element is likely to be content based on its structure and attributes.
     */
    private static isLikelyContent;
    /**
     * Scores a block element based on various criteria to determine if it's likely not content.
     * Returns a negative score if the element is likely not content, a positive score if it is.
     */
    private static scoreNonContentBlock;
}
