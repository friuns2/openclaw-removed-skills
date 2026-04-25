"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BaseExtractor = void 0;
class BaseExtractor {
    constructor(document, url, schemaOrgData) {
        this.document = document;
        this.url = url;
        this.schemaOrgData = schemaOrgData;
    }
    canExtractAsync() {
        return false;
    }
    async extractAsync() {
        return this.extract();
    }
}
exports.BaseExtractor = BaseExtractor;
//# sourceMappingURL=_base.js.map