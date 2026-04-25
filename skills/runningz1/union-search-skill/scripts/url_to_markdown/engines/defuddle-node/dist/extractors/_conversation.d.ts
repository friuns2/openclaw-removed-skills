import { BaseExtractor } from './_base';
import { ConversationMessage, ConversationMetadata, Footnote, ExtractorResult } from '../types/extractors';
export declare abstract class ConversationExtractor extends BaseExtractor {
    protected abstract extractMessages(): ConversationMessage[];
    protected abstract getMetadata(): ConversationMetadata;
    protected getFootnotes(): Footnote[];
    extract(): ExtractorResult;
    protected createContentHtml(messages: ConversationMessage[], footnotes: Footnote[]): string;
}
