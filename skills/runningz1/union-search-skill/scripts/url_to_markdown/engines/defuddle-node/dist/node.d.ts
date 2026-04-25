import { JSDOM } from 'jsdom';
import DefuddleClass from './index';
import type { DefuddleOptions, DefuddleResponse } from './types';
/**
 * Parse HTML content using JSDOM
 * @param htmlOrDom HTML string or JSDOM instance to parse
 * @param url Optional URL of the page being parsed
 * @param options Optional parsing options
 * @returns Promise with parsed content and metadata
 */
export declare function Defuddle(htmlOrDom: string | JSDOM, url?: string, options?: DefuddleOptions): Promise<DefuddleResponse>;
export { DefuddleClass, DefuddleOptions, DefuddleResponse };
