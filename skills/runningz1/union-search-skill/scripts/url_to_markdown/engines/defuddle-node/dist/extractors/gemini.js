"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GeminiExtractor = void 0;
const _conversation_1 = require("./_conversation");
const dom_1 = require("../utils/dom");
class GeminiExtractor extends _conversation_1.ConversationExtractor {
    constructor(document, url) {
        super(document, url);
        this.messageCount = null;
        this.conversationContainers = document.querySelectorAll('div.conversation-container');
        this.footnotes = [];
    }
    canExtract() {
        return !!this.conversationContainers && this.conversationContainers.length > 0;
    }
    extractMessages() {
        this.messageCount = 0;
        const messages = [];
        if (!this.conversationContainers)
            return messages;
        this.extractSources();
        this.conversationContainers.forEach((container) => {
            const userQuery = container.querySelector('user-query');
            if (userQuery) {
                const queryText = userQuery.querySelector('.query-text');
                if (queryText) {
                    const content = (0, dom_1.serializeHTML)(queryText);
                    messages.push({
                        author: 'You',
                        content: content.trim(),
                        metadata: { role: 'user' }
                    });
                }
            }
            const modelResponse = container.querySelector('model-response');
            if (modelResponse) {
                const regularContent = modelResponse.querySelector('.model-response-text .markdown');
                const extendedContent = modelResponse.querySelector('#extended-response-markdown-content');
                const contentElement = extendedContent || regularContent;
                if (contentElement) {
                    let content = (0, dom_1.serializeHTML)(contentElement);
                    const tempDiv = this.document.createElement('div');
                    tempDiv.appendChild((0, dom_1.parseHTML)(this.document, content));
                    tempDiv.querySelectorAll('.table-content').forEach(el => {
                        // `table-content` is a PARTIAL selector in defuddle (table of contents, will be removed), but a real table in Gemini (should be kept).
                        el.classList.remove('table-content');
                    });
                    content = (0, dom_1.serializeHTML)(tempDiv);
                    messages.push({
                        author: 'Gemini',
                        content: content.trim(),
                        metadata: { role: 'assistant' }
                    });
                }
            }
        });
        this.messageCount = messages.length;
        return messages;
    }
    extractSources() {
        const browseItems = this.document.querySelectorAll('browse-item');
        if (browseItems && browseItems.length > 0) {
            browseItems.forEach(item => {
                const link = item.querySelector('a');
                if (link instanceof HTMLAnchorElement) {
                    const url = link.href;
                    const domain = link.querySelector('.domain')?.textContent?.trim() || '';
                    const title = link.querySelector('.title')?.textContent?.trim() || '';
                    if (url && (domain || title)) {
                        this.footnotes.push({
                            url,
                            text: title ? `${domain}: ${title}` : domain
                        });
                    }
                }
            });
        }
    }
    getFootnotes() {
        return this.footnotes;
    }
    getMetadata() {
        const title = this.getTitle();
        const messageCount = this.messageCount ?? this.extractMessages().length;
        return {
            title,
            site: 'Gemini',
            url: this.url,
            messageCount,
            description: `Gemini conversation with ${messageCount} messages`
        };
    }
    getTitle() {
        const pageTitle = this.document.title?.trim();
        if (pageTitle && pageTitle !== 'Gemini' && !pageTitle.includes('Gemini')) {
            return pageTitle;
        }
        const researchTitle = this.document.querySelector('.title-text')?.textContent?.trim();
        if (researchTitle) {
            return researchTitle;
        }
        const firstUserQuery = this.conversationContainers?.item(0)?.querySelector('.query-text');
        if (firstUserQuery) {
            const text = firstUserQuery.textContent || '';
            return text.length > 50 ? text.slice(0, 50) + '...' : text;
        }
        return 'Gemini Conversation';
    }
}
exports.GeminiExtractor = GeminiExtractor;
//# sourceMappingURL=gemini.js.map