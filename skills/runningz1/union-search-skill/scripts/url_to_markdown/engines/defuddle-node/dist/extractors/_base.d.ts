import { ExtractorResult } from '../types/extractors';
export declare abstract class BaseExtractor {
    protected document: Document;
    protected url: string;
    protected schemaOrgData?: any;
    constructor(document: Document, url: string, schemaOrgData?: any);
    abstract canExtract(): boolean;
    abstract extract(): ExtractorResult;
    canExtractAsync(): boolean;
    extractAsync(): Promise<ExtractorResult>;
}
