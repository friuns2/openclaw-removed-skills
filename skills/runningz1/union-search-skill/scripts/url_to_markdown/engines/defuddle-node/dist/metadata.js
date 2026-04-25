"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetadataExtractor = void 0;
class MetadataExtractor {
    static extract(doc, schemaOrgData, metaTags) {
        let domain = '';
        let url = '';
        try {
            // Try to get URL from document location
            url = doc.location?.href || '';
            // If no URL from location, try other sources
            if (!url) {
                url = this.getMetaContent(metaTags, "property", "og:url") ||
                    this.getMetaContent(metaTags, "property", "twitter:url") ||
                    this.getSchemaProperty(schemaOrgData, 'url') ||
                    this.getSchemaProperty(schemaOrgData, 'mainEntityOfPage.url') ||
                    this.getSchemaProperty(schemaOrgData, 'mainEntity.url') ||
                    this.getSchemaProperty(schemaOrgData, 'WebSite.url') ||
                    doc.querySelector('link[rel="canonical"]')?.getAttribute('href') || '';
            }
            if (url) {
                try {
                    domain = new URL(url).hostname.replace(/^www\./, '');
                }
                catch (e) {
                    console.warn('Failed to parse URL:', e);
                }
            }
        }
        catch (e) {
            // If URL parsing fails, try to get from base tag
            const baseTag = doc.querySelector('base[href]');
            if (baseTag) {
                try {
                    url = baseTag.getAttribute('href') || '';
                    domain = new URL(url).hostname.replace(/^www\./, '');
                }
                catch (e) {
                    console.warn('Failed to parse base URL:', e);
                }
            }
        }
        return {
            title: this.getTitle(doc, schemaOrgData, metaTags),
            description: this.getDescription(doc, schemaOrgData, metaTags),
            domain,
            favicon: this.getFavicon(doc, url, metaTags),
            image: this.getImage(doc, schemaOrgData, metaTags),
            published: this.getPublished(doc, schemaOrgData, metaTags),
            author: this.getAuthor(doc, schemaOrgData, metaTags),
            site: this.getSite(doc, schemaOrgData, metaTags),
            schemaOrgData,
            wordCount: 0,
            parseTime: 0
        };
    }
    static getAuthor(doc, schemaOrgData, metaTags) {
        let authorsString;
        // Meta tags - typically expect a single string, possibly comma-separated
        authorsString = this.getMetaContent(metaTags, "name", "sailthru.author") ||
            this.getMetaContent(metaTags, "property", "author") ||
            this.getMetaContent(metaTags, "name", "author") ||
            this.getMetaContent(metaTags, "name", "byl") ||
            this.getMetaContent(metaTags, "name", "authorList");
        if (authorsString)
            return authorsString;
        // Conventions for research paper meta tags
        let authorsStrings = this.getMetaContents(metaTags, "name", "citation_author");
        if (authorsStrings.length === 0) {
            authorsStrings = this.getMetaContents(metaTags, "property", "dc.creator");
        }
        if (authorsStrings.length > 0) {
            authorsString = authorsStrings.map(s => {
                if (!s.includes(','))
                    return s.trim();
                const parts = /(.*),\s(.*)/.exec(s);
                if (parts && parts.length === 3) {
                    return `${parts[2]} ${parts[1]}`;
                }
                return s.trim();
            }).join(', ');
            return authorsString;
        }
        // 2. Schema.org data - deduplicate if it's a list
        let schemaAuthors = this.getSchemaProperty(schemaOrgData, 'author.name') ||
            this.getSchemaProperty(schemaOrgData, 'author.[].name');
        if (schemaAuthors) {
            const parts = schemaAuthors.split(',')
                .map(part => part.trim().replace(/,$/, '').trim())
                .filter(Boolean);
            if (parts.length > 0) {
                let uniqueSchemaAuthors = [...new Set(parts)];
                if (uniqueSchemaAuthors.length > 10) {
                    uniqueSchemaAuthors = uniqueSchemaAuthors.slice(0, 10);
                }
                return uniqueSchemaAuthors.join(', ');
            }
        }
        // 3. DOM elements
        const collectedAuthorsFromDOM = [];
        const addDomAuthor = (value) => {
            if (!value)
                return;
            value.split(',').forEach(namePart => {
                const cleanedName = namePart.trim().replace(/,$/, '').trim();
                const lowerCleanedName = cleanedName.toLowerCase();
                if (cleanedName && lowerCleanedName !== 'author' && lowerCleanedName !== 'authors') {
                    collectedAuthorsFromDOM.push(cleanedName);
                }
            });
        };
        // maxMatches: skip ambiguous selectors with too many matches
        // (e.g. testimonials, comments, contributor lists)
        const domAuthorSelectors = [
            { selector: '[itemprop="author"]' },
            { selector: '.author', maxMatches: 3 },
            { selector: '[href*="/author/"]', maxMatches: 3 },
            { selector: '.authors a', maxMatches: 3 },
        ];
        for (const { selector, maxMatches } of domAuthorSelectors) {
            const matches = doc.querySelectorAll(selector);
            if (maxMatches && matches.length > maxMatches)
                continue;
            matches.forEach(el => addDomAuthor(el.textContent));
        }
        if (collectedAuthorsFromDOM.length > 0) {
            let uniqueAuthors = [...new Set(collectedAuthorsFromDOM.map(name => name.trim()).filter(Boolean))];
            if (uniqueAuthors.length > 0) {
                if (uniqueAuthors.length > 10) {
                    uniqueAuthors = uniqueAuthors.slice(0, 10);
                }
                return uniqueAuthors.join(', ');
            }
        }
        // 4. Author near article heading (byline patterns and date-adjacent names)
        const h1 = doc.querySelector('h1');
        if (h1) {
            // Check siblings of h1 for date-adjacent author names
            let sibling = h1.nextElementSibling;
            for (let i = 0; i < 3 && sibling; i++) {
                const siblingText = sibling.textContent?.trim() || '';
                if (this.parseDateText(siblingText)) {
                    const links = sibling.querySelectorAll('a');
                    for (const link of links) {
                        const linkText = (link.textContent?.trim() || '').replace(/\u00a0/g, ' ');
                        if (linkText.length > 0 && linkText.length < 100 && !this.parseDateText(linkText)) {
                            return linkText;
                        }
                    }
                }
                sibling = sibling.nextElementSibling;
            }
            // Search for "By ..." bylines near h1: check siblings of h1
            // and siblings of its ancestor containers (up to 3 levels)
            let bylineScope = h1;
            for (let depth = 0; depth < 3 && bylineScope; depth++) {
                let bylineCandidate = bylineScope.previousElementSibling;
                // Check a few siblings before
                for (let i = 0; i < 3 && bylineCandidate; i++) {
                    const bylineResult = this.extractByline(bylineCandidate);
                    if (bylineResult)
                        return bylineResult;
                    bylineCandidate = bylineCandidate.previousElementSibling;
                }
                // Check a few siblings after
                bylineCandidate = bylineScope.nextElementSibling;
                for (let i = 0; i < 3 && bylineCandidate; i++) {
                    const bylineResult = this.extractByline(bylineCandidate);
                    if (bylineResult)
                        return bylineResult;
                    bylineCandidate = bylineCandidate.nextElementSibling;
                }
                bylineScope = bylineScope.parentElement;
            }
        }
        // 5. Fall back to site name
        return this.getSiteName(schemaOrgData, metaTags);
    }
    static extractByline(el) {
        // Check the element itself and its direct children for "By ..." text
        const candidates = [el, ...el.querySelectorAll('p, span, address')];
        for (const candidate of candidates) {
            const text = (candidate.textContent?.trim() || '').replace(/\u00a0/g, ' ');
            if (text.length > 0 && text.length < 50) {
                const bylineMatch = text.match(/^By\s+([A-Z].+)$/i);
                if (bylineMatch) {
                    return bylineMatch[1].trim();
                }
            }
        }
        return null;
    }
    static getSiteName(schemaOrgData, metaTags) {
        return (this.getSchemaProperty(schemaOrgData, 'publisher.name') ||
            this.getMetaContent(metaTags, "property", "og:site_name") ||
            this.getSchemaProperty(schemaOrgData, 'WebSite.name') ||
            this.getSchemaProperty(schemaOrgData, 'sourceOrganization.name') ||
            this.getMetaContent(metaTags, "name", "copyright") ||
            this.getSchemaProperty(schemaOrgData, 'copyrightHolder.name') ||
            this.getSchemaProperty(schemaOrgData, 'isPartOf.name') ||
            this.getMetaContent(metaTags, "name", "application-name") ||
            '');
    }
    static getSite(doc, schemaOrgData, metaTags) {
        return (this.getSiteName(schemaOrgData, metaTags) ||
            this.getAuthor(doc, schemaOrgData, metaTags) ||
            '');
    }
    static getTitle(doc, schemaOrgData, metaTags) {
        const rawTitle = (this.getMetaContent(metaTags, "property", "og:title") ||
            this.getMetaContent(metaTags, "name", "twitter:title") ||
            this.getSchemaProperty(schemaOrgData, 'headline') ||
            this.getMetaContent(metaTags, "name", "title") ||
            this.getMetaContent(metaTags, "name", "sailthru.title") ||
            doc.querySelector('title')?.textContent?.trim() ||
            '');
        return this.cleanTitle(rawTitle, this.getSite(doc, schemaOrgData, metaTags));
    }
    static cleanTitle(title, siteName) {
        if (!title || !siteName)
            return title;
        // Remove site name if it exists
        const siteNameEscaped = siteName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const patterns = [
            `\\s*[\\|\\-–—]\\s*${siteNameEscaped}\\s*$`, // Title | Site Name
            `^\\s*${siteNameEscaped}\\s*[\\|\\-–—]\\s*`, // Site Name | Title
        ];
        for (const pattern of patterns) {
            const regex = new RegExp(pattern, 'i');
            if (regex.test(title)) {
                title = title.replace(regex, '');
                break;
            }
        }
        return title.trim();
    }
    static getDescription(doc, schemaOrgData, metaTags) {
        return (this.getMetaContent(metaTags, "name", "description") ||
            this.getMetaContent(metaTags, "property", "description") ||
            this.getMetaContent(metaTags, "property", "og:description") ||
            this.getSchemaProperty(schemaOrgData, 'description') ||
            this.getMetaContent(metaTags, "name", "twitter:description") ||
            this.getMetaContent(metaTags, "name", "sailthru.description") ||
            '');
    }
    static getImage(doc, schemaOrgData, metaTags) {
        return (this.getMetaContent(metaTags, "property", "og:image") ||
            this.getMetaContent(metaTags, "name", "twitter:image") ||
            this.getSchemaProperty(schemaOrgData, 'image.url') ||
            this.getMetaContent(metaTags, "name", "sailthru.image.full") ||
            '');
    }
    static getFavicon(doc, baseUrl, metaTags) {
        const iconFromMeta = this.getMetaContent(metaTags, "property", "og:image:favicon");
        if (iconFromMeta)
            return iconFromMeta;
        const iconLink = doc.querySelector("link[rel='icon']")?.getAttribute("href");
        if (iconLink)
            return iconLink;
        const shortcutLink = doc.querySelector("link[rel='shortcut icon']")?.getAttribute("href");
        if (shortcutLink)
            return shortcutLink;
        // Only try to construct favicon URL if we have a valid HTTP base URL
        if (baseUrl && /^https?:\/\//.test(baseUrl)) {
            try {
                return new URL("/favicon.ico", baseUrl).href;
            }
            catch (e) {
                // Silently fail for invalid URLs
            }
        }
        return '';
    }
    static getPublished(doc, schemaOrgData, metaTags) {
        const result = this.getSchemaProperty(schemaOrgData, 'datePublished') ||
            this.getMetaContent(metaTags, "name", "publishDate") ||
            this.getMetaContent(metaTags, "property", "article:published_time") ||
            doc.querySelector('abbr[itemprop="datePublished"]')?.title?.trim() ||
            this.getTimeElement(doc) ||
            this.getMetaContent(metaTags, "name", "sailthru.date");
        if (result)
            return result;
        // Look for date text near the article heading
        const h1 = doc.querySelector('h1');
        if (h1) {
            let sibling = h1.nextElementSibling;
            for (let i = 0; i < 3 && sibling; i++) {
                const parsed = this.parseDateText(sibling.textContent?.trim() || '');
                if (parsed)
                    return parsed;
                sibling = sibling.nextElementSibling;
            }
        }
        return '';
    }
    static getMetaContent(metaTags, attr, value) {
        return this.getMetaContents(metaTags, attr, value)[0] ?? "";
    }
    static getMetaContents(metaTags, attr, value) {
        return metaTags.filter(tag => {
            const attributeValue = attr === 'name' ? tag.name : tag.property;
            return attributeValue?.toLowerCase() === value.toLowerCase();
        }).map(tag => tag.content?.trim() ?? "");
    }
    static getTimeElement(doc) {
        const selector = `time`;
        const element = Array.from(doc.querySelectorAll(selector))[0];
        const content = element ? (element.getAttribute("datetime")?.trim() ?? element.textContent?.trim() ?? "") : "";
        return content;
    }
    static parseDateText(text) {
        // "26 February 2025" or "Wednesday, 26 February 2025"
        let match = text.match(/\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b/i);
        if (match) {
            const day = match[1].padStart(2, '0');
            const month = this.MONTH_MAP[match[2].toLowerCase()];
            return `${match[3]}-${month}-${day}T00:00:00+00:00`;
        }
        // "February 26, 2025" or "June 5, 2023"
        match = text.match(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b/i);
        if (match) {
            const month = this.MONTH_MAP[match[1].toLowerCase()];
            const day = match[2].padStart(2, '0');
            return `${match[3]}-${month}-${day}T00:00:00+00:00`;
        }
        return '';
    }
    static getSchemaProperty(schemaOrgData, property, defaultValue = '') {
        if (!schemaOrgData)
            return defaultValue;
        const searchSchema = (data, props, fullPath, isExactMatch = true) => {
            if (typeof data === 'string') {
                return props.length === 0 ? [data] : [];
            }
            if (!data || typeof data !== 'object') {
                return [];
            }
            if (Array.isArray(data)) {
                const currentProp = props[0];
                if (/^\[\d+\]$/.test(currentProp)) {
                    const index = parseInt(currentProp.slice(1, -1));
                    if (data[index]) {
                        return searchSchema(data[index], props.slice(1), fullPath, isExactMatch);
                    }
                    return [];
                }
                if (props.length === 0 && data.every(item => typeof item === 'string' || typeof item === 'number')) {
                    return data.map(String);
                }
                return data.flatMap(item => searchSchema(item, props, fullPath, isExactMatch));
            }
            const [currentProp, ...remainingProps] = props;
            if (!currentProp) {
                if (typeof data === 'string')
                    return [data];
                if (typeof data === 'object' && data.name) {
                    return [data.name];
                }
                return [];
            }
            if (data.hasOwnProperty(currentProp)) {
                return searchSchema(data[currentProp], remainingProps, fullPath ? `${fullPath}.${currentProp}` : currentProp, true);
            }
            if (!isExactMatch) {
                const nestedResults = [];
                for (const key in data) {
                    if (typeof data[key] === 'object') {
                        const results = searchSchema(data[key], props, fullPath ? `${fullPath}.${key}` : key, false);
                        nestedResults.push(...results);
                    }
                }
                if (nestedResults.length > 0) {
                    return nestedResults;
                }
            }
            return [];
        };
        try {
            let results = searchSchema(schemaOrgData, property.split('.'), '', true);
            if (results.length === 0) {
                results = searchSchema(schemaOrgData, property.split('.'), '', false);
            }
            const result = results.length > 0 ? results.filter(Boolean).join(', ') : defaultValue;
            return result;
        }
        catch (error) {
            console.error(`Error in getSchemaProperty for ${property}:`, error);
            return defaultValue;
        }
    }
}
exports.MetadataExtractor = MetadataExtractor;
MetadataExtractor.MONTH_MAP = {
    'january': '01', 'february': '02', 'march': '03', 'april': '04',
    'may': '05', 'june': '06', 'july': '07', 'august': '08',
    'september': '09', 'october': '10', 'november': '11', 'december': '12'
};
//# sourceMappingURL=metadata.js.map