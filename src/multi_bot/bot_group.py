"""
Bot组管理类
管理多个Bot实例的集合
"""
from typing import Dict, List, Optional, Any
from .bot_instance import BotInstance
import structlog

logger = structlog.get_logger(__name__)


class BotGroup:
    """
    Bot组管理类
    管理一组相关的Bot实例
    """
    
    def __init__(self, group_name: str, group_config: Optional[Dict[str, Any]] = None):
        """
        初始化Bot组
        
        Args:
            group_name: 组名称
            group_config: 组配置（如资源限制、启动顺序等）
        """
        self.group_name = group_name
        self.group_config = group_config or {}
        self.instances: Dict[str, BotInstance] = {}
        self.created_time = None
    
    def add_instance(self, instance: BotInstance) -> bool:
        """
        添加Bot实例到组
        
        Args:
            instance: BotInstance对象
        
        Returns:
            是否添加成功
        """
        if instance.instance_id in self.instances:
            logger.warning(
                "实例ID已存在",
                instance_id=instance.instance_id,
                group=self.group_name
            )
            return False
        
        self.instances[instance.instance_id] = instance
        logger.info(
            "已添加实例到组",
            instance_id=instance.instance_id,
            group=self.group_name
        )
        return True
    
    def remove_instance(self, instance_id: str) -> bool:
        """
        从组中移除Bot实例
        
        Args:
            instance_id: 实例ID
        
        Returns:
            是否移除成功
        """
        if instance_id not in self.instances:
            logger.warning(
                "实例ID不存在",
                instance_id=instance_id,
                group=self.group_name
            )
            return False
        
        instance = self.instances.pop(instance_id)
        if instance.is_running:
            instance.stop()
        
        logger.info(
            "已从组中移除实例",
            instance_id=instance_id,
            group=self.group_name
        )
        return True
    
    def get_instance(self, instance_id: str) -> Optional[BotInstance]:
        """
        获取组中的实例
        
        Args:
            instance_id: 实例ID
        
        Returns:
            BotInstance对象或None
        """
        return self.instances.get(instance_id)
    
    def get_all_instances(self) -> Dict[str, BotInstance]:
        """
        获取组中所有实例
        
        Returns:
            实例字典
        """
        return self.instances.copy()
    
    def get_running_instances(self) -> List[BotInstance]:
        """
        获取组中所有运行中的实例
        
        Returns:
            运行中的实例列表
        """
        return [inst for inst in self.instances.values() if inst.is_running]
    
    def get_stopped_instances(self) -> List[BotInstance]:
        """
        获取组中所有已停止的实例
        
        Returns:
            已停止的实例列表
        """
        return [inst for inst in self.instances.values() if not inst.is_running]
    
    def get_group_status(self) -> Dict[str, Any]:
        """
        获取组的整体状态
        
        Returns:
            组状态字典
        """
        running = self.get_running_instances()
        stopped = self.get_stopped_instances()
        
        total_memory = sum(
            inst.resource_usage.get("memory_mb", 0) 
            for inst in running
        )
        
        return {
            "group_name": self.group_name,
            "total_instances": len(self.instances),
            "running_count": len(running),
            "stopped_count": len(stopped),
            "total_memory_mb": total_memory,
            "instances": {
                inst_id: inst.to_dict()
                for inst_id, inst in self.instances.items()
            }
        }
    
    def start_all(self, callback=None) -> Dict[str, bool]:
        """
        启动组中所有实例
        
        Args:
            callback: 启动回调函数 (instance_id, success) -> None
        
        Returns:
            实例ID -> 是否成功的字典
        """
        results = {}
        for instance_id, instance in self.instances.items():
            if not instance.is_running:
                # 这里实际的启动逻辑由MultiBotManager处理
                # 此处只是标记状态
                success = True
                results[instance_id] = success
                if callback:
                    callback(instance_id, success)
        
        return results
    
    def stop_all(self, callback=None) -> Dict[str, bool]:
        """
        停止组中所有实例
        
        Args:
            callback: 停止回调函数 (instance_id, success) -> None
        
        Returns:
            实例ID -> 是否成功的字典
        """
        results = {}
        for instance_id, instance in self.instances.items():
            if instance.is_running:
                success = instance.stop()
                results[instance_id] = success
                if callback:
                    callback(instance_id, success)
        
        return results
    
    def get_instance_count(self) -> int:
        """
        获取组中实例总数
        
        Returns:
            实例总数
        """
        return len(self.instances)
    
    def get_running_count(self) -> int:
        """
        获取组中运行中的实例数
        
        Returns:
            运行中的实例数
        """
        return len(self.get_running_instances())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将组转换为字典
        
        Returns:
            组信息字典
        """
        return {
            "group_name": self.group_name,
            "group_config": self.group_config,
            "instances": {
                inst_id: inst.to_dict()
                for inst_id, inst in self.instances.items()
            },
            "status": self.get_group_status()
        }
    
    def __repr__(self) -> str:
        running = len(self.get_running_instances())
        total = len(self.instances)
        return f"<BotGroup name={self.group_name} running={running}/{total}>"
