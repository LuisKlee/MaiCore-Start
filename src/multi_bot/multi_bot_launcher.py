"""
多Bot启动器集成模块
将多Bot管理系统与现有的启动器集成
"""
from typing import Dict, Any, Optional, Tuple
import structlog
import time

from .multi_bot_manager import multi_bot_manager

logger = structlog.get_logger(__name__)


class MultiBotLauncher:
    """
    多Bot启动器
    负责启动和管理多个Bot实例
    """
    
    def __init__(self, process_manager):
        """
        初始化多Bot启动器
        
        Args:
            process_manager: 进程管理器实例
        """
        self.multi_bot_manager = multi_bot_manager
        self.process_manager = process_manager
        self.launch_callbacks: Dict[str, callable] = {}
    
    def launch_instance(
        self,
        group_name: str,
        instance_id: str,
        command: str,
        cwd: str,
        title: str
    ) -> Tuple[bool, Optional[int]]:
        """
        启动单个Bot实例
        
        Args:
            group_name: 所属组名称
            instance_id: 实例ID
            command: 启动命令
            cwd: 工作目录
            title: 窗口标题
        
        Returns:
            (是否成功, 进程ID)
        """
        try:
            # 获取实例
            instance = self.multi_bot_manager.get_instance(group_name, instance_id)
            if not instance:
                logger.error("实例不存在", group_name=group_name, instance_id=instance_id)
                return False, None
            
            # 使用进程管理器启动
            process = self.process_manager.start_in_new_cmd(command, cwd, title)
            
            if not process:
                instance.set_error(f"启动命令执行失败: {command}")
                self.multi_bot_manager.trigger_callback(
                    "on_error",
                    group_name=group_name,
                    instance_id=instance_id,
                    error="启动失败"
                )
                return False, None
            
            # 更新实例状态
            process_info = {
                "pid": process.pid,
                "command": command,
                "cwd": cwd,
                "title": title
            }
            instance.start(process_info)
            
            # 触发回调
            self.multi_bot_manager.trigger_callback(
                "on_start",
                group_name=group_name,
                instance_id=instance_id,
                pid=process.pid
            )
            
            logger.info(
                "Bot实例已启动",
                group_name=group_name,
                instance_id=instance_id,
                pid=process.pid
            )
            
            return True, process.pid
        
        except Exception as e:
            logger.error(
                "启动Bot实例时出错",
                group_name=group_name,
                instance_id=instance_id,
                error=str(e)
            )
            return False, None
    
    def launch_group(
        self,
        group_name: str,
        launch_config: Dict[str, Any]
    ) -> Dict[str, Tuple[bool, Optional[int]]]:
        """
        启动组中的多个实例
        
        Args:
            group_name: 组名称
            launch_config: 启动配置
                {
                    instance_id_1: {
                        "command": "...",
                        "cwd": "...",
                        "title": "..."
                    },
                    ...
                }
        
        Returns:
            {instance_id: (是否成功, 进程ID)}
        """
        results = {}
        group = self.multi_bot_manager.get_group(group_name)
        
        if not group:
            logger.error("组不存在", group_name=group_name)
            return results
        
        # 按顺序启动实例（可根据配置调整）
        interval = group.group_config.get("launch_interval", 1)  # 启动间隔
        
        for instance_id, config in launch_config.items():
            success, pid = self.launch_instance(
                group_name,
                instance_id,
                config["command"],
                config["cwd"],
                config["title"]
            )
            results[instance_id] = (success, pid)
            
            # 如果配置了启动间隔，则等待
            if interval > 0 and instance_id != list(launch_config.keys())[-1]:
                time.sleep(interval)
        
        return results
    
    def stop_instance(self, group_name: str, instance_id: str) -> bool:
        """
        停止单个Bot实例
        
        Args:
            group_name: 所属组名称
            instance_id: 实例ID
        
        Returns:
            是否停止成功
        """
        try:
            instance = self.multi_bot_manager.get_instance(group_name, instance_id)
            if not instance:
                logger.error("实例不存在", group_name=group_name, instance_id=instance_id)
                return False
            
            if not instance.is_running:
                logger.warning("实例未运行", group_name=group_name, instance_id=instance_id)
                return False
            
            pid = instance.pid
            if pid:
                # 使用进程管理器停止
                success = self.process_manager.stop_process(pid)
            else:
                # 直接标记为已停止
                success = instance.stop()
            
            if success:
                instance.stop()
                self.multi_bot_manager.trigger_callback(
                    "on_stop",
                    group_name=group_name,
                    instance_id=instance_id
                )
                logger.info(
                    "Bot实例已停止",
                    group_name=group_name,
                    instance_id=instance_id
                )
            
            return success
        
        except Exception as e:
            logger.error(
                "停止Bot实例时出错",
                group_name=group_name,
                instance_id=instance_id,
                error=str(e)
            )
            return False
    
    def stop_group(self, group_name: str) -> Dict[str, bool]:
        """
        停止组中的所有实例
        
        Args:
            group_name: 组名称
        
        Returns:
            {instance_id: 是否停止成功}
        """
        results = {}
        group = self.multi_bot_manager.get_group(group_name)
        
        if not group:
            logger.error("组不存在", group_name=group_name)
            return results
        
        for instance_id in group.get_all_instances().keys():
            success = self.stop_instance(group_name, instance_id)
            results[instance_id] = success
        
        return results
    
    def restart_instance(
        self,
        group_name: str,
        instance_id: str,
        command: str,
        cwd: str,
        title: str
    ) -> Tuple[bool, Optional[int]]:
        """
        重启单个Bot实例
        
        Args:
            group_name: 所属组名称
            instance_id: 实例ID
            command: 启动命令
            cwd: 工作目录
            title: 窗口标题
        
        Returns:
            (是否成功, 新进程ID)
        """
        logger.info(
            "正在重启Bot实例",
            group_name=group_name,
            instance_id=instance_id
        )
        
        # 停止实例
        if not self.stop_instance(group_name, instance_id):
            return False, None
        
        # 等待进程完全退出
        time.sleep(1)
        
        # 重新启动
        return self.launch_instance(
            group_name,
            instance_id,
            command,
            cwd,
            title
        )
    
    def get_group_status(self, group_name: str) -> Optional[Dict[str, Any]]:
        """
        获取组状态
        
        Args:
            group_name: 组名称
        
        Returns:
            组状态字典
        """
        group = self.multi_bot_manager.get_group(group_name)
        if not group:
            return None
        
        return group.get_group_status()
    
    def get_global_status(self) -> Dict[str, Any]:
        """
        获取全局状态
        
        Returns:
            全局状态字典
        """
        return self.multi_bot_manager.get_global_status()
