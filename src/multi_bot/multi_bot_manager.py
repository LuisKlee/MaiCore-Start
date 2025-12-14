"""
多Bot管理器类
负责多Bot实例的生命周期管理、持久化存储等
"""
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import os
import structlog
from datetime import datetime

from .bot_instance import BotInstance
from .bot_group import BotGroup

logger = structlog.get_logger(__name__)


class MultiBotManager:
    """
    多Bot管理器
    负责管理多个Bot实例的整个生命周期，包括创建、启动、停止、配置持久化等
    """
    
    # 多Bot配置文件位置
    MULTI_BOT_CONFIG_FILE = "config/multi_bot_config.json"
    
    def __init__(self):
        """初始化多Bot管理器"""
        self.groups: Dict[str, BotGroup] = {}
        self.instance_callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_stop": [],
            "on_error": []
        }
        self._load_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = Path(self.MULTI_BOT_CONFIG_FILE).parent
        config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """从文件加载多Bot配置"""
        try:
            if not os.path.exists(self.MULTI_BOT_CONFIG_FILE):
                logger.info("多Bot配置文件不存在，使用默认配置")
                return
            
            with open(self.MULTI_BOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复组和实例
            for group_name, group_data in data.get("groups", {}).items():
                group = BotGroup(
                    group_name,
                    group_data.get("group_config", {})
                )
                
                for instance_id, instance_data in group_data.get("instances", {}).items():
                    config = instance_data.get("config", {})
                    instance = BotInstance(instance_id, config)
                    group.add_instance(instance)
                
                self.groups[group_name] = group
            
            logger.info("成功加载多Bot配置", groups_count=len(self.groups))
        except Exception as e:
            logger.error("加载多Bot配置失败", error=str(e))
    
    def save_config(self):
        """将多Bot配置保存到文件"""
        try:
            self._ensure_config_dir()
            
            data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "groups": {}
            }
            
            for group_name, group in self.groups.items():
                data["groups"][group_name] = group.to_dict()
            
            with open(self.MULTI_BOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("多Bot配置已保存")
        except Exception as e:
            logger.error("保存多Bot配置失败", error=str(e))
    
    def create_group(self, group_name: str, group_config: Optional[Dict[str, Any]] = None) -> BotGroup:
        """
        创建Bot组
        
        Args:
            group_name: 组名称
            group_config: 组配置
        
        Returns:
            创建的BotGroup对象
        """
        if group_name in self.groups:
            logger.warning("组名已存在", group_name=group_name)
            return self.groups[group_name]
        
        group = BotGroup(group_name, group_config or {})
        self.groups[group_name] = group
        self.save_config()
        
        logger.info("创建了新的Bot组", group_name=group_name)
        return group
    
    def delete_group(self, group_name: str) -> bool:
        """
        删除Bot组（需要组中所有实例都已停止）
        
        Args:
            group_name: 组名称
        
        Returns:
            是否删除成功
        """
        if group_name not in self.groups:
            logger.warning("组不存在", group_name=group_name)
            return False
        
        group = self.groups[group_name]
        running_instances = group.get_running_instances()
        
        if running_instances:
            logger.warning(
                "组中存在运行中的实例，无法删除",
                group_name=group_name,
                running_count=len(running_instances)
            )
            return False
        
        del self.groups[group_name]
        self.save_config()
        
        logger.info("删除了Bot组", group_name=group_name)
        return True
    
    def get_group(self, group_name: str) -> Optional[BotGroup]:
        """
        获取Bot组
        
        Args:
            group_name: 组名称
        
        Returns:
            BotGroup对象或None
        """
        return self.groups.get(group_name)
    
    def get_all_groups(self) -> Dict[str, BotGroup]:
        """
        获取所有Bot组
        
        Returns:
            所有BotGroup对象的字典
        """
        return self.groups.copy()
    
    def create_instance(
        self,
        group_name: str,
        instance_id: str,
        config: Dict[str, Any]
    ) -> Optional[BotInstance]:
        """
        创建Bot实例
        
        Args:
            group_name: 所属的组名称
            instance_id: 实例ID
            config: 实例配置
        
        Returns:
            创建的BotInstance对象或None
        """
        if group_name not in self.groups:
            logger.warning("组不存在", group_name=group_name)
            return None
        
        group = self.groups[group_name]
        instance = BotInstance(instance_id, config)
        
        if group.add_instance(instance):
            self.save_config()
            logger.info(
                "创建了新的Bot实例",
                instance_id=instance_id,
                group_name=group_name
            )
            return instance
        
        return None
    
    def delete_instance(self, group_name: str, instance_id: str) -> bool:
        """
        删除Bot实例
        
        Args:
            group_name: 所属的组名称
            instance_id: 实例ID
        
        Returns:
            是否删除成功
        """
        group = self.get_group(group_name)
        if not group:
            logger.warning("组不存在", group_name=group_name)
            return False
        
        if group.remove_instance(instance_id):
            self.save_config()
            logger.info(
                "删除了Bot实例",
                instance_id=instance_id,
                group_name=group_name
            )
            return True
        
        return False
    
    def get_instance(self, group_name: str, instance_id: str) -> Optional[BotInstance]:
        """
        获取Bot实例
        
        Args:
            group_name: 所属的组名称
            instance_id: 实例ID
        
        Returns:
            BotInstance对象或None
        """
        group = self.get_group(group_name)
        if not group:
            return None
        
        return group.get_instance(instance_id)
    
    def register_callback(self, event: str, callback: Callable):
        """
        注册事件回调
        
        Args:
            event: 事件名称 ("on_start", "on_stop", "on_error")
            callback: 回调函数
        """
        if event in self.instance_callbacks:
            self.instance_callbacks[event].append(callback)
            logger.info("注册了事件回调", event=event)
    
    def trigger_callback(self, event: str, *args, **kwargs):
        """
        触发事件回调
        
        Args:
            event: 事件名称
            args: 位置参数
            kwargs: 关键字参数
        """
        if event not in self.instance_callbacks:
            return
        
        for callback in self.instance_callbacks[event]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error("执行回调时出错", event=event, error=str(e))
    
    def get_all_instances(self) -> Dict[str, Dict[str, BotInstance]]:
        """
        获取所有组中的所有实例
        
        Returns:
            {group_name: {instance_id: BotInstance}}
        """
        result = {}
        for group_name, group in self.groups.items():
            result[group_name] = group.get_all_instances()
        
        return result
    
    def get_global_status(self) -> Dict[str, Any]:
        """
        获取全局状态
        
        Returns:
            全局状态字典
        """
        total_instances = 0
        total_running = 0
        total_memory = 0
        groups_status = {}
        
        for group_name, group in self.groups.items():
            group_status = group.get_group_status()
            groups_status[group_name] = group_status
            
            total_instances += group_status["total_instances"]
            total_running += group_status["running_count"]
            total_memory += group_status["total_memory_mb"]
        
        return {
            "total_groups": len(self.groups),
            "total_instances": total_instances,
            "total_running": total_running,
            "total_stopped": total_instances - total_running,
            "total_memory_mb": total_memory,
            "groups": groups_status
        }
    
    def export_config(self, filepath: str) -> bool:
        """
        导出配置到文件
        
        Args:
            filepath: 导出文件路径
        
        Returns:
            是否导出成功
        """
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "groups": {}
            }
            
            for group_name, group in self.groups.items():
                data["groups"][group_name] = group.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("已导出配置", filepath=filepath)
            return True
        except Exception as e:
            logger.error("导出配置失败", error=str(e))
            return False
    
    def import_config(self, filepath: str) -> bool:
        """
        从文件导入配置
        
        Args:
            filepath: 导入文件路径
        
        Returns:
            是否导入成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for group_name, group_data in data.get("groups", {}).items():
                if group_name in self.groups:
                    logger.warning("组已存在，跳过导入", group_name=group_name)
                    continue
                
                group = BotGroup(
                    group_name,
                    group_data.get("group_config", {})
                )
                
                for instance_id, instance_data in group_data.get("instances", {}).items():
                    config = instance_data.get("config", {})
                    instance = BotInstance(instance_id, config)
                    group.add_instance(instance)
                
                self.groups[group_name] = group
            
            self.save_config()
            logger.info("成功导入配置", filepath=filepath)
            return True
        except Exception as e:
            logger.error("导入配置失败", error=str(e))
            return False
    
    def __repr__(self) -> str:
        total = sum(len(g.instances) for g in self.groups.values())
        running = sum(len(g.get_running_instances()) for g in self.groups.values())
        return f"<MultiBotManager groups={len(self.groups)} instances={running}/{total}>"


# 全局多Bot管理器实例
multi_bot_manager = MultiBotManager()
