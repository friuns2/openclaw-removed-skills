import { ConversationExtractor } from './_conversation';
import { ConversationMessage, ConversationMetadata } from '../types/extractors';
export declare class ClaudeExtractor extends ConversationExtractor {
    private articles;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    protected extractMessages(): ConversationMessage[];
    protected getMetadata(): ConversationMetadata;
    private getTitle;
}
