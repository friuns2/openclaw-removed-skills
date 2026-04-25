"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefuddleClass = void 0;
exports.Defuddle = Defuddle;
const jsdom_1 = require("jsdom");
const index_1 = __importDefault(require("./index"));
exports.DefuddleClass = index_1.default;
const markdown_1 = require("./markdown");
/**
 * Parse HTML content using JSDOM
 * @param htmlOrDom HTML string or JSDOM instance to parse
 * @param url Optional URL of the page being parsed
 * @param options Optional parsing options
 * @returns Promise with parsed content and metadata
 */
async function Defuddle(htmlOrDom, url, options) {
    let dom;
    if (typeof htmlOrDom === 'string') {
        dom = new jsdom_1.JSDOM(htmlOrDom, {
            url,
            //			runScripts: 'outside-only',
            resources: 'usable',
            pretendToBeVisual: true,
            includeNodeLocations: true,
            storageQuota: 10000000,
            // Add virtual console to suppress warnings
            virtualConsole: new jsdom_1.VirtualConsole().sendTo(console, { omitJSDOMErrors: true })
        });
    }
    else {
        dom = htmlOrDom;
    }
    const pageUrl = url || dom.window.location.href;
    // Create Defuddle instance with URL in options
    const defuddle = new index_1.default(dom.window.document, {
        ...options,
        url: pageUrl
    });
    const result = await defuddle.parseAsync();
    // Convert to markdown if requested
    (0, markdown_1.toMarkdown)(result, options ?? {}, pageUrl);
    return result;
}
//# sourceMappingURL=node.js.map