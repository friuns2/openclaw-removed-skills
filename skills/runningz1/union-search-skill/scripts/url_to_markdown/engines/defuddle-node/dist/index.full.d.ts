import { DefuddleOptions, DefuddleResponse } from './types';
import { createMarkdownContent } from './markdown';
export type { DefuddleOptions, DefuddleResponse };
export { createMarkdownContent };
declare class Defuddle {
    private defuddle;
    private options;
    constructor(doc: Document, options?: DefuddleOptions);
    parse(): DefuddleResponse;
    parseAsync(): Promise<DefuddleResponse>;
}
export default Defuddle;
