"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExtractorRegistry = void 0;
// Extractors
const reddit_1 = require("./extractors/reddit");
const twitter_1 = require("./extractors/twitter");
const x_article_1 = require("./extractors/x-article");
const youtube_1 = require("./extractors/youtube");
const hackernews_1 = require("./extractors/hackernews");
const chatgpt_1 = require("./extractors/chatgpt");
const claude_1 = require("./extractors/claude");
const grok_1 = require("./extractors/grok");
const gemini_1 = require("./extractors/gemini");
const github_1 = require("./extractors/github");
const x_oembed_1 = require("./extractors/x-oembed");
class ExtractorRegistry {
    static initialize() {
        // Register all extractors with their URL patterns
        // X Article extractor must be registered BEFORE Twitter to take priority
        // DOM-based canExtract() determines if page has article content
        this.register({
            patterns: [
                'x.com',
                'twitter.com',
            ],
            extractor: x_article_1.XArticleExtractor
        });
        this.register({
            patterns: [
                'twitter.com',
                /\/x\.com\/.*/,
            ],
            extractor: twitter_1.TwitterExtractor
        });
        this.register({
            patterns: [
                'x.com',
                'twitter.com',
            ],
            extractor: x_oembed_1.XOembedExtractor
        });
        this.register({
            patterns: [
                'reddit.com',
                'old.reddit.com',
                'new.reddit.com',
                /^https:\/\/[^\/]+\.reddit\.com/
            ],
            extractor: reddit_1.RedditExtractor
        });
        this.register({
            patterns: [
                'youtube.com',
                'youtu.be',
                /youtube\.com\/watch\?v=.*/,
                /youtu\.be\/.*/
            ],
            extractor: youtube_1.YoutubeExtractor
        });
        this.register({
            patterns: [
                /news\.ycombinator\.com\/item\?id=.*/
            ],
            extractor: hackernews_1.HackerNewsExtractor
        });
        this.register({
            patterns: [
                /^https?:\/\/chatgpt\.com\/(c|share)\/.*/
            ],
            extractor: chatgpt_1.ChatGPTExtractor
        });
        this.register({
            patterns: [
                'claude.ai',
                /^https?:\/\/claude\.ai\/(chat|share)\/.*/
            ],
            extractor: claude_1.ClaudeExtractor
        });
        this.register({
            patterns: [
                /^https?:\/\/grok\.com\/(chat|share)(\/.*)?$/
            ],
            extractor: grok_1.GrokExtractor,
        });
        this.register({
            patterns: [
                /^https?:\/\/gemini\.google\.com\/app\/.*/
            ],
            extractor: gemini_1.GeminiExtractor
        });
        this.register({
            patterns: [
                'github.com',
                /^https?:\/\/github\.com\/.*/
            ],
            extractor: github_1.GitHubExtractor
        });
    }
    static register(mapping) {
        this.mappings.push(mapping);
    }
    static findExtractor(document, url, schemaOrgData) {
        return this.findByPredicate(document, url, schemaOrgData, e => e.canExtract());
    }
    static findAsyncExtractor(document, url, schemaOrgData) {
        return this.findByPredicate(document, url, schemaOrgData, e => e.canExtractAsync());
    }
    static findByPredicate(document, url, schemaOrgData, predicate) {
        try {
            const domain = new URL(url).hostname;
            for (const { patterns, extractor } of this.mappings) {
                const matches = patterns.some(pattern => {
                    if (pattern instanceof RegExp) {
                        return pattern.test(url);
                    }
                    return domain.includes(pattern);
                });
                if (matches) {
                    const instance = new extractor(document, url, schemaOrgData);
                    if (predicate(instance)) {
                        return instance;
                    }
                }
            }
            return null;
        }
        catch (error) {
            console.error('Error finding extractor:', error);
            return null;
        }
    }
}
exports.ExtractorRegistry = ExtractorRegistry;
ExtractorRegistry.mappings = [];
// Initialize extractors
ExtractorRegistry.initialize();
//# sourceMappingURL=extractor-registry.js.map