#!/usr/bin/env python3
"""
RoundTable 模型选择器 - 极简安全版
"""

import os
from typing import Optional, List, Dict


class ModelSelector:
    """RoundTable 模型选择器 - 极简安全版"""
    
    # 标准单一模型配置（降级方案）
    FALLBACK_MODEL = {
        'id': 'bailian/qwen3.5-plus',
        'name': 'Qwen3.5 Plus',
        'tags': ['balanced', 'fast', 'general'],
        'priority': 3
    }
    
    def __init__(self, user_models: List[Dict] = None, config_path: str = None, primary_model: str = None):
        """
        初始化模型选择器
        
        Args:
            user_models: 用户指定的模型列表
            config_path: 配置文件路径（已废弃）
            primary_model: 主模型 ID
        """
        self.user_models = user_models
        self.config_path = config_path
        self.primary_model = primary_model
        self.available_models = []
        
        # 优先级 1: 用户指定模型列表
        if user_models:
            self.available_models = user_models
            print(f"✅ 使用用户指定的 {len(user_models)} 个模型")
            self.primary_model = user_models[0]['id'] if user_models else None
            return
        
        # 优先级 2: 主模型指定
        if primary_model:
            self.primary_model = primary_model
            print(f"📌 使用指定模型：{primary_model}")
            return
        
        # 优先级 3: 环境变量
        env_models = os.environ.get('OPENCLAW_MODELS')
        env_primary = os.environ.get('OPENCLAW_PRIMARY_MODEL')
        
        if env_models:
            try:
                import json
                self.available_models = json.loads(env_models)
                print(f"✅ 从环境变量加载 {len(self.available_models)} 个模型")
                if env_primary:
                    self.primary_model = env_primary
                return
            except json.JSONDecodeError:
                print("⚠️ 环境变量格式错误")
        
        if env_primary:
            self.primary_model = env_primary
            print(f"📌 使用环境变量模型：{env_primary}")
            return
        
        # 优先级 4: 降级到标准单一模型
        print("⚠️ 降级到标准单一模型配置")
        self.primary_model = self.FALLBACK_MODEL['id']
        print(f"📌 单一模型配置，所有专家都使用：{self.primary_model}")
    
    def select_model_for_role(self, role: str) -> Optional[str]:
        """为专家角色选择模型"""
        # 如果有多个模型，根据标签匹配
        if self.available_models:
            role_tags = {
                "engineering": ["code", "technical", "engineering"],
                "design": ["creative", "long-context", "design"],
                "testing": ["balanced", "fast", "qa"],
                "host": ["logic", "summary", "decision"],
            }
            
            tags = role_tags.get(role, [])
            best_model = None
            best_score = 0
            
            for model in self.available_models:
                score = 0
                for tag in tags:
                    if tag in model.get('tags', []):
                        score += 10
                
                if score > best_score:
                    best_score = score
                    best_model = model['id']
            
            if best_model:
                return best_model
            return self.available_models[0]['id']
        
        # 否则使用主模型
        return self.primary_model
    
    def get_model_config_summary(self) -> str:
        """获取模型配置摘要"""
        if self.primary_model:
            return f"使用指定模型：{self.primary_model}"
        elif self.available_models:
            if len(self.available_models) == 1:
                return f"使用模型：{self.available_models[0]['id']}"
            else:
                return f"配置 {len(self.available_models)} 个模型"
        else:
            return "使用 OpenClaw 默认模型"


# 快捷函数
def get_model_selector(user_models: List[Dict] = None, primary_model: str = None) -> ModelSelector:
    """获取模型选择器实例"""
    return ModelSelector(user_models, primary_model=primary_model)


def select_model_for_role(role: str, user_models: List[Dict] = None, primary_model: str = None) -> Optional[str]:
    """为角色选择模型"""
    selector = ModelSelector(user_models, primary_model=primary_model)
    return selector.select_model_for_role(role)


def list_available_models(user_models: List[Dict] = None) -> List[Dict]:
    """列出所有可用模型"""
    selector = ModelSelector(user_models)
    return selector.available_models if selector.available_models else [selector.FALLBACK_MODEL]


# 测试
if __name__ == "__main__":
    print("🧪 RoundTable 模型选择器测试\n")
    
    # 测试 1: 使用环境变量或降级
    print("测试 1: 自动获取模型")
    print("-"*60)
    selector = ModelSelector()
    print(f"结果：{selector.get_model_config_summary()}\n")
    
    # 测试 2: 指定主模型
    print("测试 2: 指定主模型")
    print("-"*60)
    selector2 = ModelSelector(primary_model="bailian/glm-5")
    print(f"结果：{selector2.get_model_config_summary()}\n")
    
    # 测试 3: 模型匹配
    print("测试 3: 模型匹配测试")
    print("-"*60)
    test_roles = ["engineering", "design", "testing", "host"]
    for role in test_roles:
        model = selector.select_model_for_role(role)
        print(f"{role:15} → {model}")
