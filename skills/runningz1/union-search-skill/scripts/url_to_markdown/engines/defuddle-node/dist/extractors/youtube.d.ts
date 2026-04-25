import { BaseExtractor } from './_base';
import { ExtractorResult } from '../types/extractors';
export declare class YoutubeExtractor extends BaseExtractor {
    private videoElement;
    protected schemaOrgData: any;
    constructor(document: Document, url: string, schemaOrgData?: any);
    canExtract(): boolean;
    extract(): ExtractorResult;
    private formatDescription;
    private getVideoData;
    private getChannelName;
    private getChannelNameFromDom;
    private getChannelNameFromMicrodata;
    private getChannelNameFromPlayerResponse;
    private parseInlineJson;
    private getVideoId;
}
