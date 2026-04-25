import { MathData } from './math.base';
export declare const getLatexFromElement: (el: Element) => string | null;
export declare const createCleanMathEl: (mathData: MathData | null, latex: string | null, isBlock: boolean, doc: Document) => Element;
export declare const mathRules: {
    selector: string;
    element: string;
    transform: (el: Element) => Element;
}[];
