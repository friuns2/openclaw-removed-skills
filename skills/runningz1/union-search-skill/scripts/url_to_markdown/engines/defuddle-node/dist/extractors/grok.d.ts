import { ConversationExtractor } from './_conversation';
import { ConversationMessage, ConversationMetadata, Footnote } from '../types/extractors';
export declare class GrokExtractor extends ConversationExtractor {
    private messageContainerSelector;
    private messageBubbles;
    private footnotes;
    private footnoteCounter;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    protected extractMessages(): ConversationMessage[];
    protected getFootnotes(): Footnote[];
    protected getMetadata(): ConversationMetadata;
    private getTitle;
    private processFootnotes;
}
