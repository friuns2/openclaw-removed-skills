"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RedditExtractor = void 0;
const _base_1 = require("./_base");
const dom_1 = require("../utils/dom");
class RedditExtractor extends _base_1.BaseExtractor {
    constructor(document, url) {
        super(document, url);
        this.shredditPost = document.querySelector('shreddit-post');
        this.isOldReddit = !!document.querySelector('.thing.link');
    }
    canExtract() {
        return !!this.shredditPost || this.isOldReddit;
    }
    canExtractAsync() {
        // For new reddit comment pages, extract() returns empty content
        // when shreddit-comment elements are missing (server-side fetch),
        // causing parseAsync() to fall through to this async path.
        return this.isCommentsPage() && !this.isOldReddit;
    }
    isCommentsPage() {
        return /\/r\/.+\/comments\//.test(this.url);
    }
    async extractAsync() {
        // Convert URL to old.reddit.com
        const oldUrl = new URL(this.url);
        oldUrl.hostname = 'old.reddit.com';
        const response = await fetch(oldUrl.toString(), {
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; Defuddle/1.0)',
            },
        });
        if (!response.ok) {
            throw new Error(`Failed to fetch old.reddit.com: ${response.status}`);
        }
        const html = await response.text();
        const Parser = this.document.defaultView?.DOMParser ?? (typeof DOMParser !== 'undefined' ? DOMParser : null);
        if (!Parser) {
            throw new Error('DOMParser is not available in this environment');
        }
        const doc = new Parser().parseFromString(html, 'text/html');
        return this.extractOldReddit(doc);
    }
    extract() {
        if (this.isOldReddit) {
            return this.extractOldReddit(this.document);
        }
        // New reddit server-side HTML includes shreddit-post but not
        // shreddit-comment elements (those require JS). Return empty
        // so parseAsync() falls through to extractAsync() which fetches
        // old.reddit.com with full content.
        const hasComments = this.document.querySelectorAll('shreddit-comment').length > 0;
        if (this.isCommentsPage() && !hasComments) {
            return { content: '', contentHtml: '' };
        }
        const postContent = this.getPostContent();
        const comments = this.extractComments();
        const contentHtml = this.createContentHtml(postContent, comments);
        const postTitle = this.document.querySelector('h1')?.textContent?.trim() || '';
        const subreddit = this.getSubreddit();
        const postAuthor = this.getPostAuthor();
        const description = this.createDescription(postContent);
        return {
            content: contentHtml,
            contentHtml: contentHtml,
            extractedContent: {
                postId: this.getPostId(),
                subreddit,
                postAuthor,
            },
            variables: {
                title: postTitle,
                author: postAuthor,
                site: `r/${subreddit}`,
                description,
            }
        };
    }
    extractOldReddit(root) {
        const thingLink = root.querySelector('.thing.link');
        const postTitle = thingLink?.querySelector('a.title')?.textContent?.trim() || '';
        const postAuthor = thingLink?.getAttribute('data-author') || '';
        const subreddit = thingLink?.getAttribute('data-subreddit') || '';
        const postBodyEl = thingLink?.querySelector('.usertext-body .md');
        const postBody = postBodyEl ? (0, dom_1.serializeHTML)(postBodyEl) : '';
        const commentArea = root.querySelector('.commentarea .sitetable');
        const comments = commentArea ? this.processOldRedditComments(commentArea) : '';
        const contentHtml = this.createContentHtml(postBody, comments);
        const description = this.createDescription(postBody);
        return {
            content: contentHtml,
            contentHtml: contentHtml,
            extractedContent: {
                postId: this.getPostId(),
                subreddit,
                postAuthor,
            },
            variables: {
                title: postTitle,
                author: postAuthor,
                site: `r/${subreddit}`,
                description,
            }
        };
    }
    getPostContent() {
        const textBodyEl = this.shredditPost?.querySelector('[slot="text-body"]');
        const textBody = textBodyEl ? (0, dom_1.serializeHTML)(textBodyEl) : '';
        const mediaBody = this.shredditPost?.querySelector('#post-image')?.outerHTML || '';
        return textBody + mediaBody;
    }
    createContentHtml(postContent, comments) {
        return `
			<div class="reddit-post">
				<div class="post-content">
					${postContent}
				</div>
			</div>
			${comments ? `
				<hr>
				<h2>Comments</h2>
				<div class="reddit-comments">
					${comments}
				</div>
			` : ''}
		`.trim();
    }
    extractComments() {
        const comments = Array.from(this.document.querySelectorAll('shreddit-comment'));
        return this.processComments(comments);
    }
    getPostId() {
        const match = this.url.match(/comments\/([a-zA-Z0-9]+)/);
        return match?.[1] || '';
    }
    getSubreddit() {
        const match = this.url.match(/\/r\/([^/]+)/);
        return match?.[1] || '';
    }
    getPostAuthor() {
        return this.shredditPost?.getAttribute('author') || '';
    }
    createDescription(postContent) {
        if (!postContent)
            return '';
        const tempDiv = this.document.createElement('div');
        tempDiv.appendChild((0, dom_1.parseHTML)(this.document, postContent));
        return tempDiv.textContent?.trim()
            .slice(0, 140)
            .replace(/\s+/g, ' ') || '';
    }
    processOldRedditComments(container) {
        const topLevelComments = Array.from(container.querySelectorAll(':scope > .thing.comment'));
        return topLevelComments.map(comment => this.renderOldRedditComment(comment)).join('');
    }
    renderOldRedditComment(comment) {
        const author = comment.getAttribute('data-author') || '';
        const permalink = comment.getAttribute('data-permalink') || '';
        const score = comment.querySelector('.entry .tagline .score.unvoted')?.textContent?.trim() || '';
        const timeEl = comment.querySelector('.entry .tagline time[datetime]');
        const datetime = timeEl?.getAttribute('datetime') || '';
        const date = datetime ? new Date(datetime).toISOString().split('T')[0] : '';
        const bodyEl = comment.querySelector('.entry .usertext-body .md');
        const body = bodyEl ? (0, dom_1.serializeHTML)(bodyEl) : '';
        let html = '<blockquote>';
        html += `<div class="comment">
	<div class="comment-metadata">
		<span class="comment-author"><strong>${author}</strong></span> •
		<a href="https://reddit.com${permalink}" class="comment-link">${score}</a> •
		<span class="comment-date">${date}</span>
	</div>
	<div class="comment-content">${body}</div>
</div>`;
        // Recurse into child comments
        const childContainer = comment.querySelector('.child > .sitetable');
        if (childContainer) {
            const children = Array.from(childContainer.querySelectorAll(':scope > .thing.comment'));
            for (const child of children) {
                html += this.renderOldRedditComment(child);
            }
        }
        html += '</blockquote>';
        return html;
    }
    processComments(comments) {
        let html = '';
        let currentDepth = -1;
        let blockquoteStack = []; // Keep track of open blockquotes at each depth
        for (const comment of comments) {
            const depth = parseInt(comment.getAttribute('depth') || '0');
            const author = comment.getAttribute('author') || '';
            const score = comment.getAttribute('score') || '0';
            const permalink = comment.getAttribute('permalink') || '';
            const commentEl = comment.querySelector('[slot="comment"]');
            const content = commentEl ? (0, dom_1.serializeHTML)(commentEl) : '';
            // Get timestamp from faceplate-timeago element
            const timeElement = comment.querySelector('faceplate-timeago');
            const timestamp = timeElement?.getAttribute('ts') || '';
            const date = timestamp ? new Date(timestamp).toISOString().split('T')[0] : '';
            // For top-level comments, close all previous blockquotes and start fresh
            if (depth === 0) {
                // Close all open blockquotes
                while (blockquoteStack.length > 0) {
                    html += '</blockquote>';
                    blockquoteStack.pop();
                }
                html += '<blockquote>';
                blockquoteStack = [0];
                currentDepth = 0;
            }
            // For nested comments
            else {
                // If we're moving back up the tree
                if (depth < currentDepth) {
                    // Close blockquotes until we reach the current depth
                    while (blockquoteStack.length > 0 && blockquoteStack[blockquoteStack.length - 1] >= depth) {
                        html += '</blockquote>';
                        blockquoteStack.pop();
                    }
                }
                // If we're going deeper
                else if (depth > currentDepth) {
                    html += '<blockquote>';
                    blockquoteStack.push(depth);
                }
                // If we're at the same depth, no need to close or open blockquotes
            }
            html += `<div class="comment">
	<div class="comment-metadata">
		<span class="comment-author"><strong>${author}</strong></span> •
		<a href="https://reddit.com${permalink}" class="comment-link">${score} points</a> •
		<span class="comment-date">${date}</span>
	</div>
	<div class="comment-content">${content}</div>
</div>`;
            currentDepth = depth;
        }
        // Close any remaining blockquotes
        while (blockquoteStack.length > 0) {
            html += '</blockquote>';
            blockquoteStack.pop();
        }
        return html;
    }
}
exports.RedditExtractor = RedditExtractor;
//# sourceMappingURL=reddit.js.map