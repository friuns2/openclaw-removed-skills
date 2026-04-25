import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class GitHubExtractor extends BaseExtractor {
    canExtract(): boolean;
    extract(): ExtractorResult;
    private extractIssue;
    private extractAuthor;
    private cleanBodyContent;
    private extractIssueNumber;
    private extractRepoInfo;
    private createDescription;
}
