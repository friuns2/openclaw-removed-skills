"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.YoutubeExtractor = void 0;
const _base_1 = require("./_base");
class YoutubeExtractor extends _base_1.BaseExtractor {
    constructor(document, url, schemaOrgData) {
        super(document, url, schemaOrgData);
        this.videoElement = document.querySelector('video');
        this.schemaOrgData = schemaOrgData;
    }
    canExtract() {
        return true;
    }
    extract() {
        const videoData = this.getVideoData();
        const channelName = this.getChannelName(videoData);
        const description = videoData.description || '';
        const formattedDescription = this.formatDescription(description);
        const contentHtml = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${this.getVideoId()}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe><br>${formattedDescription}`;
        return {
            content: contentHtml,
            contentHtml: contentHtml,
            extractedContent: {
                videoId: this.getVideoId(),
                author: channelName,
            },
            variables: {
                title: videoData.name || '',
                author: channelName,
                site: 'YouTube',
                image: Array.isArray(videoData.thumbnailUrl) ? videoData.thumbnailUrl[0] || '' : '',
                published: videoData.uploadDate,
                description: description.slice(0, 200).trim(),
            }
        };
    }
    formatDescription(description) {
        return `<p>${description.replace(/\n/g, '<br>')}</p>`;
    }
    getVideoData() {
        if (!this.schemaOrgData)
            return {};
        const videoData = Array.isArray(this.schemaOrgData)
            ? this.schemaOrgData.find(item => item['@type'] === 'VideoObject')
            : this.schemaOrgData['@type'] === 'VideoObject' ? this.schemaOrgData : null;
        return videoData || {};
    }
    getChannelName(videoData) {
        const fromDom = this.getChannelNameFromDom();
        if (fromDom) {
            return fromDom;
        }
        const fromPlayer = this.getChannelNameFromPlayerResponse();
        if (fromPlayer) {
            return fromPlayer;
        }
        return videoData?.author || '';
    }
    getChannelNameFromDom() {
        const ownerSelectors = [
            'ytd-video-owner-renderer #channel-name a[href^="/@"]',
            '#owner-name a[href^="/@"]'
        ];
        for (const selector of ownerSelectors) {
            const element = this.document.querySelector(selector);
            const value = element?.textContent?.trim();
            if (value) {
                return value;
            }
        }
        return this.getChannelNameFromMicrodata();
    }
    getChannelNameFromMicrodata() {
        const authorRoot = this.document.querySelector('[itemprop="author"]');
        if (!authorRoot)
            return '';
        const metaName = authorRoot.querySelector('meta[itemprop="name"]');
        if (metaName?.getAttribute('content')) {
            return metaName.getAttribute('content').trim();
        }
        const linkName = authorRoot.querySelector('link[itemprop="name"]');
        if (linkName?.getAttribute('content')) {
            return linkName.getAttribute('content').trim();
        }
        const text = authorRoot.querySelector('[itemprop="name"], a, span');
        return text?.textContent?.trim() || '';
    }
    getChannelNameFromPlayerResponse() {
        const data = this.parseInlineJson('ytInitialPlayerResponse');
        if (!data)
            return '';
        const fromVideoDetails = data?.videoDetails?.author || data?.videoDetails?.ownerChannelName;
        if (fromVideoDetails) {
            return fromVideoDetails;
        }
        const fromMicroformat = data?.microformat?.playerMicroformatRenderer?.ownerChannelName;
        return fromMicroformat || '';
    }
    parseInlineJson(globalName) {
        const scripts = Array.from(this.document.querySelectorAll('script'));
        for (const script of scripts) {
            const text = script.textContent || '';
            if (!text.includes(globalName))
                continue;
            const startIndex = text.indexOf('{', text.indexOf(globalName));
            if (startIndex === -1)
                continue;
            let depth = 0;
            for (let i = startIndex; i < text.length; i++) {
                const char = text[i];
                if (char === '{') {
                    depth += 1;
                }
                else if (char === '}') {
                    depth -= 1;
                    if (depth === 0) {
                        const jsonText = text.slice(startIndex, i + 1);
                        try {
                            return JSON.parse(jsonText);
                        }
                        catch (error) {
                            console.error('YoutubeExtractor: failed to parse inline JSON', error);
                            break;
                        }
                    }
                }
            }
        }
        return null;
    }
    getVideoId() {
        const url = new URL(this.url);
        if (url.hostname === 'youtu.be') {
            return url.pathname.slice(1);
        }
        return new URLSearchParams(url.search).get('v') || '';
    }
}
exports.YoutubeExtractor = YoutubeExtractor;
//# sourceMappingURL=youtube.js.map