import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class TwitterExtractor extends BaseExtractor {
    private mainTweet;
    private threadTweets;
    constructor(document: Document, url: string);
    canExtract(): boolean;
    extract(): ExtractorResult;
    private formatTweetText;
    private extractTweet;
    private extractUserInfo;
    private extractImages;
    private getTweetId;
    private getTweetAuthor;
    private createDescription;
}
