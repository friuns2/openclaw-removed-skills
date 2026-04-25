import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class RedditExtractor extends BaseExtractor {
    private shredditPost;
    private isOldReddit;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    canExtractAsync(): boolean;
    private isCommentsPage;
    extractAsync(): Promise<ExtractorResult>;
    extract(): ExtractorResult;
    private extractOldReddit;
    private getPostContent;
    private createContentHtml;
    private extractComments;
    private getPostId;
    private getSubreddit;
    private getPostAuthor;
    private createDescription;
    private processOldRedditComments;
    private renderOldRedditComment;
    private processComments;
}
