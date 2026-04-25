export interface MathData {
    mathml: string;
    latex: string | null;
    isBlock: boolean;
}
export declare const getMathMLFromElement: (el: Element) => MathData | null;
export declare const getBasicLatexFromElement: (el: Element) => string | null;
export declare const isBlockDisplay: (el: Element) => boolean;
export declare const mathSelectors: string;
