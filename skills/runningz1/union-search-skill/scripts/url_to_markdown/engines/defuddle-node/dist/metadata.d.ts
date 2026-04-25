import { DefuddleMetadata, MetaTagItem } from './types';
export declare class MetadataExtractor {
    static extract(doc: Document, schemaOrgData: any, metaTags: MetaTagItem[]): DefuddleMetadata;
    private static getAuthor;
    private static extractByline;
    private static getSiteName;
    private static getSite;
    private static getTitle;
    private static cleanTitle;
    private static getDescription;
    private static getImage;
    private static getFavicon;
    private static getPublished;
    private static getMetaContent;
    private static getMetaContents;
    private static getTimeElement;
    private static readonly MONTH_MAP;
    private static parseDateText;
    private static getSchemaProperty;
}
