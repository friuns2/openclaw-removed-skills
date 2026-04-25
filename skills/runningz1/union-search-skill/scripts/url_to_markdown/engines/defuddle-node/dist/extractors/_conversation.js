"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConversationExtractor = void 0;
const _base_1 = require("./_base");
const defuddle_1 = require("../defuddle");
const dom_1 = require("../utils/dom");
class ConversationExtractor extends _base_1.BaseExtractor {
    getFootnotes() {
        return [];
    }
    extract() {
        const messages = this.extractMessages();
        const metadata = this.getMetadata();
        const footnotes = this.getFootnotes();
        const rawContentHtml = this.createContentHtml(messages, footnotes);
        // Create a temporary document to run Defuddle on our content
        const tempDoc = this.document.implementation.createHTMLDocument();
        const container = tempDoc.createElement('article');
        container.appendChild((0, dom_1.parseHTML)(tempDoc, rawContentHtml));
        tempDoc.body.appendChild(container);
        // Run Defuddle on our formatted content
        const defuddled = new defuddle_1.Defuddle(tempDoc).parse();
        const contentHtml = defuddled.content;
        return {
            content: contentHtml,
            contentHtml: contentHtml,
            extractedContent: {
                messageCount: messages.length.toString(),
            },
            variables: {
                title: metadata.title || 'Conversation',
                site: metadata.site,
                description: metadata.description || `${metadata.site} conversation with ${messages.length} messages`,
                wordCount: defuddled.wordCount?.toString() || '',
            }
        };
    }
    createContentHtml(messages, footnotes) {
        const messagesHtml = messages.map((message, index) => {
            const timestampHtml = message.timestamp ?
                `<div class="message-timestamp">${message.timestamp}</div>` : '';
            // Check if content already has paragraph tags
            const hasParagraphs = /<p[^>]*>[\s\S]*?<\/p>/i.test(message.content);
            const contentHtml = hasParagraphs ? message.content : `<p>${message.content}</p>`;
            // Add metadata to data attributes
            const dataAttributes = message.metadata ?
                Object.entries(message.metadata)
                    .map(([key, value]) => `data-${key}="${value}"`)
                    .join(' ') : '';
            return `
			<div class="message message-${message.author.toLowerCase()}" ${dataAttributes}>
				<div class="message-header">
					<p class="message-author"><strong>${message.author}</strong></p>
					${timestampHtml}
				</div>
				<div class="message-content">
					${contentHtml}
				</div>
			</div>${index < messages.length - 1 ? '\n<hr>' : ''}`;
        }).join('\n').trim();
        // Add footnotes section if we have any
        const footnotesHtml = footnotes.length > 0 ? `
			<div id="footnotes">
				<ol>
					${footnotes.map((footnote, index) => `
						<li class="footnote" id="fn:${index + 1}">
							<p>
								<a href="${footnote.url}" target="_blank">${footnote.text}</a>&nbsp;<a href="#fnref:${index + 1}" class="footnote-backref">↩</a>
							</p>
						</li>
					`).join('')}
				</ol>
			</div>` : '';
        return `${messagesHtml}\n${footnotesHtml}`.trim();
    }
}
exports.ConversationExtractor = ConversationExtractor;
//# sourceMappingURL=_conversation.js.map