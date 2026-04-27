import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../common/prisma.service';

// BigInt 序列化辅助函数
function serializeBigInt(data: any): any {
  if (data === null || data === undefined) return data;
  if (typeof data === 'bigint') return Number(data);
  if (Array.isArray(data)) return data.map(serializeBigInt);
  if (typeof data === 'object') {
    const result: any = {};
    for (const key of Object.keys(data)) {
      result[key] = serializeBigInt(data[key]);
    }
    return result;
  }
  return data;
}

@Injectable()
export class CodeReviewService {
  constructor(private prisma: PrismaService) {}

  /**
   * 🔴 Bug 3 修复：问题类型英文到中文映射
   */
  private mapIssueTypeToChinese(type: string): string {
    const typeMap: Record<string, string> = {
      'maintainability': '代码可维护性',
      'performance': '性能问题',
      'security': '安全问题',
      'error_handling': '错误处理',
      'type_definition': '类型定义',
      'hardcoded_value': '硬编码常量',
      'code_quality': '代码质量',
      'best_practice': '最佳实践',
      'testing': '测试覆盖',
      'correctness': '代码正确性',
    };
    return typeMap[type] || type;
  }

  /**
   * 解析项目 ID（支持 UUID、项目 ID 或项目名称）
   */
  async resolveProjectId(projectIdOrName: string): Promise<string | null> {
    // 检查是否是 UUID 格式
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidRegex.test(projectIdOrName)) {
      return projectIdOrName;
    }
    
    // 先尝试按 ID 查找（支持非 UUID 格式的 ID，如 project-lego-nuxt）
    const projectById = await this.prisma.$queryRaw`
      SELECT id FROM projects WHERE id = ${projectIdOrName} LIMIT 1
    ` as any[];
    
    if (projectById.length > 0) {
      return projectById[0].id;
    }
    
    // 再按名称查找
    const projectByName = await this.prisma.$queryRaw`
      SELECT id FROM projects WHERE name = ${projectIdOrName} LIMIT 1
    ` as any[];
    
    return projectByName.length > 0 ? projectByName[0].id : null;
  }

  /**
   * 保存代码审查问题
   */
  async saveIssues(analysisId: string, issues: any[]) {
    // 先删除该分析的旧问题
    await this.prisma.$executeRaw`DELETE FROM code_issues WHERE analysis_id = ${analysisId}`;
    
    // 批量插入新问题
    for (const issue of issues) {
      await this.prisma.$executeRaw`
        INSERT INTO code_issues (
          id, analysis_id, file_path, line_start, line_end, 
          issue_type, severity, description, suggestion, code_snippet, committer_name, created_at, updated_at
        ) VALUES (
          gen_random_uuid(), ${analysisId}, ${issue.filePath}, ${issue.lineStart || null}, ${issue.lineEnd || null},
          ${issue.type}, ${issue.severity}, ${issue.description}, ${issue.suggestion || null}, ${issue.codeSnippet || null},
          ${issue.committerName || null},
          NOW(), NOW()
        )
      `;
    }
    
    return { count: issues.length };
  }

  /**
   * 获取项目的代码审查问题
   * 🔴 Bug 3 修复：返回前转换问题类型为中文
   */
  async getProjectIssues(projectId: string, periodType: string, periodValue: string) {
    const issues = await this.prisma.$queryRaw`
      SELECT 
        ci.id, ci.file_path, ci.line_start, ci.line_end,
        ci.issue_type, ci.severity, ci.description, ci.suggestion, 
        ci.code_snippet, ci.code_example, ci.committer_name,
        ci.created_at
      FROM code_issues ci
      JOIN code_analyses ca ON ci.analysis_id = ca.id
      WHERE ca.project_id = ${projectId}
        AND ca.period_type = ${periodType}
        AND ca.period_value = ${periodValue}
      ORDER BY ci.severity, ci.file_path, ci.line_start
    `;
    
    // 🔴 Bug 3 修复：转换问题类型为中文
    return serializeBigInt(issues).map((issue: any) => ({
      ...issue,
      issue_type: this.mapIssueTypeToChinese(issue.issue_type),
    }));
  }

  /**
   * 获取项目的代码审查汇总
   */
  async getProjectReviewSummary(projectId: string, periodType: string, periodValue: string) {
    // 获取问题统计
    const stats = await this.prisma.$queryRaw`
      SELECT 
        severity,
        COUNT(*) as count
      FROM code_issues ci
      JOIN code_analyses ca ON ci.analysis_id = ca.id
      WHERE ca.project_id = ${projectId}
        AND ca.period_type = ${periodType}
        AND ca.period_value = ${periodValue}
      GROUP BY severity
    `;
    
    // 获取问题类型统计
    const typeStats = await this.prisma.$queryRaw`
      SELECT 
        issue_type,
        COUNT(*) as count
      FROM code_issues ci
      JOIN code_analyses ca ON ci.analysis_id = ca.id
      WHERE ca.project_id = ${projectId}
        AND ca.period_type = ${periodType}
        AND ca.period_value = ${periodValue}
      GROUP BY issue_type
      ORDER BY count DESC
    `;
    
    // 获取文件统计
    const fileStats = await this.prisma.$queryRaw`
      SELECT 
        file_path,
        COUNT(*) as issue_count,
        ARRAY_AGG(DISTINCT severity) as severities
      FROM code_issues ci
      JOIN code_analyses ca ON ci.analysis_id = ca.id
      WHERE ca.project_id = ${projectId}
        AND ca.period_type = ${periodType}
        AND ca.period_value = ${periodValue}
      GROUP BY file_path
      ORDER BY issue_count DESC
    `;
    
    // 🔴 Bug 3 修复：转换问题类型为中文
    return {
      stats: serializeBigInt(stats),
      typeStats: serializeBigInt(typeStats).map((item: any) => ({
        ...item,
        issue_type: this.mapIssueTypeToChinese(item.issue_type),
      })),
      fileStats: serializeBigInt(fileStats)
    };
  }

  /**
   * 批量保存审查报告
   */
  async saveReviewReport(projectId: string, periodType: string, periodValue: string, report: {
    overview: any;
    issues: any[];
    commonIssues: any[];
    highlights: any[];
    priority: any[];
  }) {
    // 获取该项目的分析 ID
    const analyses = await this.prisma.$queryRaw`
      SELECT id, user_id FROM code_analyses 
      WHERE project_id = ${projectId}
        AND period_type = ${periodType}
        AND period_value = ${periodValue}
    ` as any[];
    
    if (analyses.length === 0) {
      return { success: false, message: '未找到分析记录' };
    }
    
    // 为每个分析保存问题
    for (const analysis of analyses) {
      const userIssues = report.issues.filter(i => !i.userId || i.userId === analysis.user_id);
      if (userIssues.length > 0) {
        await this.saveIssues(analysis.id, userIssues);
      }
    }
    
    return { success: true, issueCount: report.issues.length };
  }
}