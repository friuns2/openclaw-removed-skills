import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class XOembedExtractor extends BaseExtractor {
    canExtract(): boolean;
    extract(): ExtractorResult;
    canExtractAsync(): boolean;
    extractAsync(): Promise<ExtractorResult>;
    private extractOembed;
    private tryExtractFxTwitter;
    private fetchFxTwitter;
    private buildArticleResult;
    private buildTweetResult;
    private renderTweet;
    private applyMarkers;
    private applyFacets;
    private renderArticle;
    private renderBlock;
    private renderAtomicBlock;
    private renderInlineContent;
    private escapeHtml;
}
