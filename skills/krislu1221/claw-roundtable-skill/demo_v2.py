#!/usr/bin/env python3
"""
RoundTable V2 演示脚本

展示需求分析、专家匹配、议题识别的完整流程
"""

from requirement_analyzer import RequirementAnalyzer, ExpertSelector, EXPERT_PROFILES

def demo_requirement_analysis():
    """演示需求分析"""
    print("\n" + "="*60)
    print("📋 RoundTable V2 需求分析演示")
    print("="*60)
    
    test_cases = [
        "智能待办应用的架构设计",
        "用户认证模块的安全评审",
        "任务管理界面的用户体验优化",
        "AI 智能推荐算法设计",
        "PR 代码审查",
    ]
    
    analyzer = RequirementAnalyzer()
    selector = ExpertSelector()
    
    for topic in test_cases:
        print(f"\n{'='*60}")
        print(f"主题：{topic}")
        print(f"{'='*60}")
        
        # 需求分析
        requirement = analyzer.analyze(topic)
        
        print(f"\n检测到的需求类型：")
        for t in requirement.detected_types:
            print(f"  - {t.value}")
        
        print(f"\n推荐专家：")
        for expert_id in requirement.recommended_experts:
            if expert_id not in requirement.excluded_experts:
                profile = EXPERT_PROFILES.get(expert_id)
                print(f"  ✅ {profile.name} ({profile.role})")
            else:
                profile = EXPERT_PROFILES.get(expert_id)
                print(f"  ❌ {profile.name} (已排除)")
        
        print(f"\n关键议题：")
        for t in requirement.key_topics:
            print(f"  - {t['name']} ({t['priority']})")
        
        print(f"\n排除专家：")
        if requirement.excluded_experts:
            for expert_id in requirement.excluded_experts:
                profile = EXPERT_PROFILES.get(expert_id)
                phases = profile.exclude_phases if profile else []
                print(f"  - {profile.name}（不参与{phases}阶段）")
        else:
            print(f"  无")
    
    print(f"\n{'='*60}")
    print("✅ 演示完成！")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    demo_requirement_analysis()
