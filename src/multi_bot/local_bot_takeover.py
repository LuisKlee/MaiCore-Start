"""
本地Bot进程检测和接管模块
用于检测、监控和接管本地运行的Bot实例
"""
import psutil
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = structlog.get_logger(__name__)


class LocalBotDetector:
    """
    本地Bot进程检测器
    检测当前系统中运行的机器人进程
    """
    
    # 常见的Bot进程名称关键词
    BOT_PROCESS_KEYWORDS = {
        "MaiBot": ["maibot", "mai_bot", "main.py"],
        "MoFox_bot": ["mofox", "mofox_bot"],
        "NapCat": ["napcat", "qq"],
    }
    
    def __init__(self):
        """初始化检测器"""
        self.detected_processes: Dict[str, Dict[str, Any]] = {}
    
    def detect_all_bots(self) -> Dict[str, Dict[str, Any]]:
        """
        检测所有运行中的机器人进程
        
        Returns:
            {process_name: {pid, name, exe, cwd, memory_mb, create_time, ...}}
        """
        self.detected_processes = {}
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cwd', 'cmdline']):
                try:
                    pinfo = proc.as_dict(attrs=['pid', 'name', 'exe', 'cwd', 'cmdline', 'memory_info', 'create_time'])
                    bot_type = self._identify_bot_type(pinfo)
                    
                    if bot_type:
                        process_key = f"{bot_type}_{pinfo['pid']}"
                        self.detected_processes[process_key] = {
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "bot_type": bot_type,
                            "exe": pinfo['exe'],
                            "cwd": pinfo['cwd'],
                            "cmdline": pinfo['cmdline'],
                            "memory_mb": pinfo['memory_info'].rss / (1024 * 1024),
                            "create_time": datetime.fromtimestamp(pinfo['create_time']),
                            "process_key": process_key
                        }
                        
                        logger.info(
                            "检测到Bot进程",
                            process_key=process_key,
                            pid=pinfo['pid'],
                            bot_type=bot_type
                        )
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            logger.info("Bot进程检测完成", detected_count=len(self.detected_processes))
            return self.detected_processes
        
        except Exception as e:
            logger.error("检测Bot进程时出错", error=str(e))
            return {}
    
    def detect_bots_by_type(self, bot_type: str) -> Dict[str, Dict[str, Any]]:
        """
        按类型检测特定的Bot进程
        
        Args:
            bot_type: Bot类型 ("MaiBot", "MoFox_bot", "NapCat")
        
        Returns:
            该类型的所有运行进程
        """
        self.detect_all_bots()
        return {
            key: info for key, info in self.detected_processes.items()
            if info.get("bot_type") == bot_type
        }
    
    def _identify_bot_type(self, pinfo: Dict[str, Any]) -> Optional[str]:
        """
        根据进程信息识别Bot类型
        
        Args:
            pinfo: 进程信息字典
        
        Returns:
            Bot类型或None
        """
        process_name = pinfo.get("name", "").lower()
        exe = pinfo.get("exe", "").lower()
        cwd = pinfo.get("cwd", "").lower()
        cmdline = pinfo.get("cmdline", [])
        
        # 组合所有可搜索的文本
        searchable_text = f"{process_name} {exe} {cwd} {' '.join(cmdline)}".lower()
        
        # 按优先级检查
        for bot_type, keywords in self.BOT_PROCESS_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in searchable_text:
                    return bot_type
        
        return None
    
    def get_detected_process(self, process_key: str) -> Optional[Dict[str, Any]]:
        """
        获取检测到的单个进程信息
        
        Args:
            process_key: 进程标识键
        
        Returns:
            进程信息或None
        """
        return self.detected_processes.get(process_key)
    
    def get_all_detected(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有检测到的进程
        
        Returns:
            所有检测到的进程信息
        """
        return self.detected_processes.copy()


class LocalBotTakeover:
    """
    本地Bot接管管理器
    将检测到的本地运行的Bot接管到多Bot管理系统
    """
    
    def __init__(self, multi_bot_manager):
        """
        初始化接管管理器
        
        Args:
            multi_bot_manager: MultiBotManager实例
        """
        self.multi_bot_manager = multi_bot_manager
        self.detector = LocalBotDetector()
        self.takeover_records: Dict[str, Dict[str, Any]] = {}
    
    def detect_and_analyze(self) -> Dict[str, Dict[str, Any]]:
        """
        检测并分析本地运行的Bot
        
        Returns:
            检测到的Bot进程信息
        """
        logger.info("开始检测本地运行的Bot...")
        return self.detector.detect_all_bots()
    
    def create_takeover_instance(
        self,
        process_key: str,
        group_name: str,
        instance_id: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        将检测到的本地Bot转换为多Bot实例
        
        Args:
            process_key: 进程标识键
            group_name: 所属组名称
            instance_id: 实例ID
            config_override: 配置覆盖（可选）
        
        Returns:
            是否接管成功
        """
        try:
            # 获取进程信息
            process_info = self.detector.get_detected_process(process_key)
            if not process_info:
                logger.error("未找到指定的进程", process_key=process_key)
                return False
            
            # 构建实例配置
            instance_config = {
                "process_key": process_key,
                "pid": process_info["pid"],
                "bot_type": process_info["bot_type"],
                "name": process_info.get("name", ""),
                "cwd": process_info.get("cwd", ""),
                "cmdline": process_info.get("cmdline", []),
                "detect_time": process_info["create_time"].isoformat(),
                "is_detected": True
            }
            
            # 应用配置覆盖
            if config_override:
                instance_config.update(config_override)
            
            # 创建多Bot组（如果不存在）
            if not self.multi_bot_manager.get_group(group_name):
                self.multi_bot_manager.create_group(group_name)
            
            # 创建实例
            instance = self.multi_bot_manager.create_instance(
                group_name,
                instance_id,
                instance_config
            )
            
            if instance:
                # 更新实例状态为正在运行
                process_status_info = {
                    "pid": process_info["pid"],
                    "command": " ".join(process_info.get("cmdline", [])),
                    "cwd": process_info.get("cwd", ""),
                    "title": f"{process_info['bot_type']}-{instance_id}"
                }
                instance.start(process_status_info)
                
                # 记录接管信息
                self.takeover_records[process_key] = {
                    "group_name": group_name,
                    "instance_id": instance_id,
                    "takeover_time": datetime.now().isoformat(),
                    "original_process_info": process_info
                }
                
                # 保存配置
                self.multi_bot_manager.save_config()
                
                logger.info(
                    "成功接管本地Bot",
                    process_key=process_key,
                    group_name=group_name,
                    instance_id=instance_id
                )
                return True
            else:
                logger.error("创建实例失败", group_name=group_name, instance_id=instance_id)
                return False
        
        except Exception as e:
            logger.error("接管本地Bot失败", process_key=process_key, error=str(e))
            return False
    
    def batch_takeover(
        self,
        process_keys: List[str],
        group_name: str,
        instance_prefix: str = "bot"
    ) -> Dict[str, bool]:
        """
        批量接管多个本地Bot
        
        Args:
            process_keys: 进程标识键列表
            group_name: 所属组名称
            instance_prefix: 实例ID前缀
        
        Returns:
            {process_key: 是否成功}
        """
        results = {}
        
        # 创建或获取组
        if not self.multi_bot_manager.get_group(group_name):
            self.multi_bot_manager.create_group(group_name)
        
        for idx, process_key in enumerate(process_keys):
            instance_id = f"{instance_prefix}_{idx + 1:03d}"
            success = self.create_takeover_instance(
                process_key,
                group_name,
                instance_id
            )
            results[process_key] = success
        
        return results
    
    def monitor_takeover_instances(self) -> Dict[str, Dict[str, Any]]:
        """
        监控已接管的实例，检查进程是否仍在运行
        
        Returns:
            {instance_key: {is_running, pid, memory_mb, uptime, ...}}
        """
        monitoring_results = {}
        
        try:
            for process_key, takeover_info in self.takeover_records.items():
                group_name = takeover_info["group_name"]
                instance_id = takeover_info["instance_id"]
                original_pid = takeover_info["original_process_info"]["pid"]
                
                # 获取实例
                instance = self.multi_bot_manager.get_instance(group_name, instance_id)
                if not instance:
                    continue
                
                # 检查进程是否仍在运行
                try:
                    proc = psutil.Process(original_pid)
                    is_running = proc.is_running()
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                    
                    result_key = f"{group_name}_{instance_id}"
                    monitoring_results[result_key] = {
                        "group_name": group_name,
                        "instance_id": instance_id,
                        "is_running": is_running,
                        "pid": original_pid,
                        "memory_mb": memory_mb,
                        "uptime": instance.get_uptime(),
                        "status": instance.status
                    }
                    
                    # 更新资源占用
                    if is_running:
                        instance.update_resource_usage(0, memory_mb)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程已不存在
                    instance.stop()
                    monitoring_results[f"{group_name}_{instance_id}"] = {
                        "group_name": group_name,
                        "instance_id": instance_id,
                        "is_running": False,
                        "pid": original_pid,
                        "status": "stopped"
                    }
            
            logger.info("监控接管实例完成", monitored_count=len(monitoring_results))
            return monitoring_results
        
        except Exception as e:
            logger.error("监控接管实例时出错", error=str(e))
            return {}
    
    def get_takeover_summary(self) -> Dict[str, Any]:
        """
        获取接管情况总结
        
        Returns:
            接管统计信息
        """
        total_takeover = len(self.takeover_records)
        
        # 统计按组分类
        by_group = {}
        for takeover_info in self.takeover_records.values():
            group = takeover_info["group_name"]
            by_group[group] = by_group.get(group, 0) + 1
        
        return {
            "total_takeover": total_takeover,
            "by_group": by_group,
            "takeover_records": self.takeover_records
        }
