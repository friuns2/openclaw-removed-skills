import { ConversationExtractor } from './_conversation';
import { ConversationMessage, ConversationMetadata, Footnote } from '../types/extractors';
export declare class ChatGPTExtractor extends ConversationExtractor {
    private articles;
    private footnotes;
    private footnoteCounter;
    private cachedMessages;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    protected extractMessages(): ConversationMessage[];
    protected getFootnotes(): Footnote[];
    protected getMetadata(): ConversationMetadata;
    private getTitle;
}
