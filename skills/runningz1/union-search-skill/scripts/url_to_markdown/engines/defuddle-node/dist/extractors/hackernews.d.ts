import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class HackerNewsExtractor extends BaseExtractor {
    private mainPost;
    private isCommentPage;
    private mainComment;
    constructor(document: Document, url: string);
    private detectCommentPage;
    private findMainComment;
    canExtract(): boolean;
    extract(): ExtractorResult;
    private createContentHtml;
    private getPostContent;
    private extractComments;
    private processComments;
    private getPostId;
    private getPostTitle;
    private getPostAuthor;
    private createDescription;
    private getPostDate;
}
