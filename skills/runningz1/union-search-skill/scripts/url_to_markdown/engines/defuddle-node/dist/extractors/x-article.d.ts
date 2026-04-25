import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class XArticleExtractor extends BaseExtractor {
    private articleContainer;
    constructor(document: Document, url: string, schemaOrgData?: any);
    canExtract(): boolean;
    extract(): ExtractorResult;
    private extractTitle;
    private extractAuthor;
    private getAuthorFromUrl;
    private getAuthorFromOgTitle;
    private getArticleId;
    private extractContent;
    private cleanContent;
    private convertEmbeddedTweets;
    private convertCodeBlocks;
    private convertHeaders;
    private unwrapLinkedImages;
    private upgradeImageQuality;
    private convertDraftParagraphs;
    private convertBoldSpans;
    private removeDraftAttributes;
    private createDescription;
}
