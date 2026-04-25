import { ConversationExtractor } from './_conversation';
import { ConversationMessage, ConversationMetadata, Footnote } from '../types/extractors';
export declare class GeminiExtractor extends ConversationExtractor {
    private conversationContainers;
    private footnotes;
    private messageCount;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    protected extractMessages(): ConversationMessage[];
    private extractSources;
    protected getFootnotes(): Footnote[];
    protected getMetadata(): ConversationMetadata;
    private getTitle;
}
