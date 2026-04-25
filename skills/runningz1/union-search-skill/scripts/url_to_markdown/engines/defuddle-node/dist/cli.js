#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const commander_1 = require("commander");
const node_1 = require("./node");
const promises_1 = require("fs/promises");
const path_1 = require("path");
// ANSI color helpers (avoids chalk dependency which is ESM-only)
const useColor = process.stdout.isTTY ?? false;
const ansi = {
    red: (s) => useColor ? `\x1b[31m${s}\x1b[39m` : s,
    green: (s) => useColor ? `\x1b[32m${s}\x1b[39m` : s,
};
// Read version from package.json
const version = require('../package.json').version;
const program = new commander_1.Command();
program
    .name('defuddle')
    .description('Extract article content from web pages')
    .version(version);
program
    .command('parse')
    .description('Parse HTML content from a file or URL')
    .argument('<source>', 'HTML file path or URL to parse')
    .option('-o, --output <file>', 'Output file path (default: stdout)')
    .option('-m, --markdown', 'Convert content to markdown format')
    .option('--md', 'Alias for --markdown')
    .option('-j, --json', 'Output as JSON with metadata and content')
    .option('-p, --property <name>', 'Extract a specific property (e.g., title, description, domain)')
    .option('--debug', 'Enable debug mode')
    .action(async (source, options) => {
    try {
        // Handle --md alias
        if (options.md) {
            options.markdown = true;
        }
        let JSDOM;
        try {
            JSDOM = (await Promise.resolve().then(() => __importStar(require('jsdom')))).JSDOM;
        }
        catch {
            console.error(ansi.red('Error: jsdom is required for the CLI. Install it with: npm install jsdom'));
            process.exit(1);
        }
        let dom;
        // Determine if source is a URL or file path
        if (source.startsWith('http://') || source.startsWith('https://')) {
            dom = await JSDOM.fromURL(source);
        }
        else {
            const filePath = (0, path_1.resolve)(process.cwd(), source);
            dom = await JSDOM.fromFile(filePath);
        }
        const result = await (0, node_1.Defuddle)(dom, source.startsWith('http') ? source : undefined, {
            debug: options.debug,
            markdown: options.markdown
        });
        // Format output
        let output;
        if (options.property) {
            const property = options.property;
            if (property in result) {
                output = result[property]?.toString() || '';
            }
            else {
                console.error(ansi.red(`Error: Property "${property}" not found in response`));
                process.exit(1);
            }
        }
        else if (options.json) {
            output = JSON.stringify({
                content: result.content,
                title: result.title,
                description: result.description,
                domain: result.domain,
                favicon: result.favicon,
                image: result.image,
                metaTags: result.metaTags,
                parseTime: result.parseTime,
                published: result.published,
                author: result.author,
                site: result.site,
                schemaOrgData: result.schemaOrgData,
                wordCount: result.wordCount
            }, null, 2);
        }
        else {
            output = result.content;
        }
        // Handle output
        if (options.output) {
            const outputPath = (0, path_1.resolve)(process.cwd(), options.output);
            await (0, promises_1.writeFile)(outputPath, output, 'utf-8');
            console.log(ansi.green(`Output written to ${options.output}`));
        }
        else {
            console.log(output);
        }
    }
    catch (error) {
        console.error(ansi.red('Error:'), error instanceof Error ? error.message : 'Unknown error occurred');
        process.exit(1);
    }
});
program.parse();
//# sourceMappingURL=cli.js.map