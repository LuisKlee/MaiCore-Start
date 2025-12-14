"""
Bot实例类
代表单个机器人实例的状态和操作
"""
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class BotInstance:
    """
    Bot实例类
    代表一个独立的机器人实例，包含其运行状态和配置信息
    """
    
    def __init__(self, instance_id: str, config: Dict[str, Any]):
        """
        初始化Bot实例
        
        Args:
            instance_id: 实例唯一ID
            config: 配置字典，包含bot_path, adapter_path, napcat_path等信息
        """
        self.instance_id = instance_id
        self.config = config
        self.is_running = False
        self.process_info = None  # 存储进程信息
        self.start_time = None
        self.stop_time = None
        self.status = "stopped"  # stopped, running, paused, error
        self.error_message = None
        self.pid = None  # 进程ID
        self.resource_usage = {}  # CPU, Memory等资源占用
        self.last_update = None
    
    def start(self, process_info: Dict[str, Any]) -> bool:
        """
        标记实例为运行状态
        
        Args:
            process_info: 进程信息字典
        
        Returns:
            是否成功启动
        """
        try:
            self.is_running = True
            self.status = "running"
            self.process_info = process_info
            self.pid = process_info.get("pid")
            self.start_time = datetime.now()
            self.error_message = None
            self.last_update = datetime.now()
            
            logger.info(
                "Bot实例启动成功",
                instance_id=self.instance_id,
                pid=self.pid
            )
            return True
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            logger.error(
                "Bot实例启动失败",
                instance_id=self.instance_id,
                error=str(e)
            )
            return False
    
    def stop(self) -> bool:
        """
        标记实例为停止状态
        
        Returns:
            是否成功停止
        """
        try:
            self.is_running = False
            self.status = "stopped"
            self.stop_time = datetime.now()
            self.pid = None
            self.process_info = None
            self.last_update = datetime.now()
            
            logger.info(
                "Bot实例已停止",
                instance_id=self.instance_id
            )
            return True
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            logger.error(
                "Bot实例停止失败",
                instance_id=self.instance_id,
                error=str(e)
            )
            return False
    
    def pause(self) -> bool:
        """
        暂停实例
        
        Returns:
            是否成功暂停
        """
        if not self.is_running:
            return False
        
        self.status = "paused"
        self.last_update = datetime.now()
        logger.info("Bot实例已暂停", instance_id=self.instance_id)
        return True
    
    def resume(self) -> bool:
        """
        恢复实例运行
        
        Returns:
            是否成功恢复
        """
        if self.status != "paused":
            return False
        
        self.status = "running"
        self.last_update = datetime.now()
        logger.info("Bot实例已恢复", instance_id=self.instance_id)
        return True
    
    def set_error(self, error_message: str):
        """
        设置错误状态
        
        Args:
            error_message: 错误信息
        """
        self.status = "error"
        self.error_message = error_message
        self.last_update = datetime.now()
        logger.error(
            "Bot实例发生错误",
            instance_id=self.instance_id,
            error=error_message
        )
    
    def update_resource_usage(self, cpu_percent: float, memory_mb: float):
        """
        更新资源占用信息
        
        Args:
            cpu_percent: CPU使用百分比
            memory_mb: 内存占用（MB）
        """
        self.resource_usage = {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "update_time": datetime.now()
        }
        self.last_update = datetime.now()
    
    def get_uptime(self) -> Optional[str]:
        """
        获取运行时长
        
        Returns:
            运行时长字符串，如未运行返回None
        """
        if not self.is_running or not self.start_time:
            return None
        
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m {seconds}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将实例转换为字典
        
        Returns:
            实例信息字典
        """
        return {
            "instance_id": self.instance_id,
            "config": self.config,
            "is_running": self.is_running,
            "status": self.status,
            "pid": self.pid,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "uptime": self.get_uptime(),
            "error_message": self.error_message,
            "resource_usage": self.resource_usage,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def __repr__(self) -> str:
        return f"<BotInstance id={self.instance_id} status={self.status} pid={self.pid}>"
