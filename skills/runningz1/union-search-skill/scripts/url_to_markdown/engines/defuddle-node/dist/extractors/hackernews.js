"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HackerNewsExtractor = void 0;
const _base_1 = require("./_base");
const dom_1 = require("../utils/dom");
class HackerNewsExtractor extends _base_1.BaseExtractor {
    constructor(document, url) {
        super(document, url);
        this.mainPost = document.querySelector('.fatitem');
        this.isCommentPage = this.detectCommentPage();
        this.mainComment = this.isCommentPage ? this.findMainComment() : null;
    }
    detectCommentPage() {
        // Comment pages have an "on: <story title>" link but no story title row
        return !!this.mainPost?.querySelector('.onstory') && !this.mainPost?.querySelector('.titleline');
    }
    findMainComment() {
        // Use the tr.athing row which contains both the comment metadata (.comhead)
        // and the comment text (.commtext). The .comment div alone doesn't include
        // the author (.hnuser) or timestamp (.age) which are in the sibling .comhead.
        return this.mainPost?.querySelector('tr.athing') || null;
    }
    canExtract() {
        return !!this.mainPost;
    }
    extract() {
        const postContent = this.getPostContent();
        const comments = this.extractComments();
        const contentHtml = this.createContentHtml(postContent, comments);
        const postTitle = this.getPostTitle();
        const postAuthor = this.getPostAuthor();
        const description = this.createDescription();
        const published = this.getPostDate();
        return {
            content: contentHtml,
            contentHtml: contentHtml,
            extractedContent: {
                postId: this.getPostId(),
                postAuthor,
            },
            variables: {
                title: postTitle,
                author: postAuthor,
                site: 'Hacker News',
                description,
                published,
            }
        };
    }
    createContentHtml(postContent, comments) {
        return `
			<div class="hackernews-post">
				<div class="post-content">
					${postContent}
				</div>
				${comments ? `
					<hr>
					<h2>Comments</h2>
					<div class="hackernews-comments">
						${comments}
					</div>
				` : ''}
			</div>
		`.trim();
    }
    getPostContent() {
        if (!this.mainPost)
            return '';
        // If this is a comment page, use the comment as the main content
        if (this.isCommentPage && this.mainComment) {
            const author = this.mainComment.querySelector('.hnuser')?.textContent || '[deleted]';
            const commtext = this.mainComment.querySelector('.commtext');
            const commentText = commtext ? (0, dom_1.serializeHTML)(commtext) : '';
            const timeElement = this.mainComment.querySelector('.age');
            const timestamp = timeElement?.getAttribute('title') || '';
            const date = timestamp.split('T')[0] || '';
            const points = this.mainComment.querySelector('.score')?.textContent?.trim() || '';
            const parentUrl = this.mainPost.querySelector('.navs a[href*="parent"]')?.getAttribute('href') || '';
            return `
				<div class="comment main-comment">
					<div class="comment-metadata">
						<span class="comment-author"><strong>${author}</strong></span> •
						<span class="comment-date">${date}</span>
						${points ? ` • <span class="comment-points">${points}</span>` : ''}
						${parentUrl ? ` • <a href="https://news.ycombinator.com/${parentUrl}" class="parent-link">parent</a>` : ''}
					</div>
					<div class="comment-content">${commentText}</div>
				</div>
			`.trim();
        }
        // Otherwise handle regular post content
        const titleRow = this.mainPost.querySelector('tr.athing');
        const subRow = titleRow?.nextElementSibling;
        const url = titleRow?.querySelector('.titleline a')?.getAttribute('href') || '';
        let content = '';
        if (url) {
            content += `<p><a href="${url}" target="_blank">${url}</a></p>`;
        }
        const text = this.mainPost.querySelector('.toptext');
        if (text) {
            content += `<div class="post-text">${(0, dom_1.serializeHTML)(text)}</div>`;
        }
        return content;
    }
    extractComments() {
        const comments = Array.from(this.document.querySelectorAll('tr.comtr'));
        return this.processComments(comments);
    }
    processComments(comments) {
        let html = '';
        const processedIds = new Set();
        let currentDepth = -1;
        let blockquoteStack = [];
        for (const comment of comments) {
            const id = comment.getAttribute('id');
            if (!id || processedIds.has(id))
                continue;
            processedIds.add(id);
            const indent = comment.querySelector('.ind img')?.getAttribute('width') || '0';
            const depth = parseInt(indent) / 40;
            const commentText = comment.querySelector('.commtext');
            const author = comment.querySelector('.hnuser')?.textContent || '[deleted]';
            const timeElement = comment.querySelector('.age');
            const points = comment.querySelector('.score')?.textContent?.trim() || '';
            if (!commentText)
                continue;
            // Get the comment URL
            const commentUrl = `https://news.ycombinator.com/item?id=${id}`;
            // Get the timestamp from the title attribute and extract the date portion
            const timestamp = timeElement?.getAttribute('title') || '';
            const date = timestamp.split('T')[0] || '';
            // For top-level comments, close all previous blockquotes and start fresh
            if (depth === 0) {
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
		<a href="${commentUrl}" class="comment-link">${date}</a>
		${points ? ` • <span class="comment-points">${points}</span>` : ''}
	</div>
	<div class="comment-content">${(0, dom_1.serializeHTML)(commentText)}</div>
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
    getPostId() {
        const match = this.url.match(/id=(\d+)/);
        return match?.[1] || '';
    }
    getPostTitle() {
        if (this.isCommentPage && this.mainComment) {
            const author = this.mainComment.querySelector('.hnuser')?.textContent || '[deleted]';
            const commentText = this.mainComment.querySelector('.commtext')?.textContent || '';
            // Use first 50 characters of comment as title
            const preview = commentText.trim().slice(0, 50) + (commentText.length > 50 ? '...' : '');
            return `Comment by ${author}: ${preview}`;
        }
        return this.mainPost?.querySelector('.titleline')?.textContent?.trim() || '';
    }
    getPostAuthor() {
        return this.mainPost?.querySelector('.hnuser')?.textContent?.trim() || '';
    }
    createDescription() {
        const title = this.getPostTitle();
        const author = this.getPostAuthor();
        if (this.isCommentPage) {
            return `Comment by ${author} on Hacker News`;
        }
        return `${title} - by ${author} on Hacker News`;
    }
    getPostDate() {
        if (!this.mainPost)
            return '';
        const timeElement = this.mainPost.querySelector('.age');
        const timestamp = timeElement?.getAttribute('title') || '';
        return timestamp.split('T')[0] || '';
    }
}
exports.HackerNewsExtractor = HackerNewsExtractor;
//# sourceMappingURL=hackernews.js.map