import { MathData } from './math.base';
export declare const createCleanMathEl: (doc: Document, mathData: MathData | null, latex: string | null, isBlock: boolean) => Element;
export declare const mathRules: {
    selector: string;
    element: string;
    transform: (el: Element, doc: Document) => Element;
}[];
