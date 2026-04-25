interface SkillRequest {
    action: string;
    params?: Record<string, string>;
}
interface SkillResponse {
    success: boolean;
    data?: unknown;
    error?: string;
}
export declare function handleSkillRequest(request: SkillRequest): Promise<SkillResponse>;
export {};
