"""
Bot端口分配和管理模块
自动分配和管理各Bot实例的端口
"""
import socket
import structlog
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

logger = structlog.get_logger(__name__)


class PortAllocator:
    """
    端口分配器
    自动分配可用的端口，避免冲突
    """
    
    # 默认端口范围
    DEFAULT_PORT_RANGE_START = 8000
    DEFAULT_PORT_RANGE_END = 9000
    
    # 保留端口（不分配）
    RESERVED_PORTS = {
        22, 23, 25, 53, 67, 68, 80, 123, 143, 161, 162, 389, 443, 465, 587,
        636, 993, 995, 3306, 3389, 5432, 5984, 6379, 27017, 27018, 27019, 27020,
        3000, 4200, 5000, 5005, 8080, 8443, 9000, 9090, 9200, 9300
    }
    
    def __init__(self, start_port: int = DEFAULT_PORT_RANGE_START, end_port: int = DEFAULT_PORT_RANGE_END):
        """
        初始化端口分配器
        
        Args:
            start_port: 起始端口
            end_port: 结束端口
        """
        self.start_port = start_port
        self.end_port = end_port
        self.allocated_ports: Set[int] = set()
        self.port_mappings: Dict[str, int] = {}  # instance_id -> port
    
    def is_port_available(self, port: int) -> bool:
        """
        检查端口是否可用
        
        Args:
            port: 端口号
        
        Returns:
            是否可用
        """
        # 检查是否已分配
        if port in self.allocated_ports:
            return False
        
        # 检查是否为保留端口
        if port in self.RESERVED_PORTS:
            return False
        
        # 检查系统中端口是否被占用
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0
        except Exception as e:
            logger.warning(f"检查端口 {port} 可用性时出错", port=port, error=str(e))
            return False
    
    def allocate_port(self, instance_id: str, preferred_port: Optional[int] = None) -> Optional[int]:
        """
        为实例分配端口
        
        Args:
            instance_id: 实例ID
            preferred_port: 首选端口（可选）
        
        Returns:
            分配的端口或None
        """
        # 如果已分配过该实例，返回原端口
        if instance_id in self.port_mappings:
            return self.port_mappings[instance_id]
        
        # 尝试首选端口
        if preferred_port and self.is_port_available(preferred_port):
            self.allocated_ports.add(preferred_port)
            self.port_mappings[instance_id] = preferred_port
            logger.info(
                "为Bot实例分配端口",
                instance_id=instance_id,
                port=preferred_port,
                source="preferred"
            )
            return preferred_port
        
        # 从范围内找可用端口
        for port in range(self.start_port, self.end_port):
            if self.is_port_available(port):
                self.allocated_ports.add(port)
                self.port_mappings[instance_id] = port
                logger.info(
                    "为Bot实例分配端口",
                    instance_id=instance_id,
                    port=port,
                    source="automatic"
                )
                return port
        
        logger.error(
            "无法为Bot实例分配端口，端口范围内无可用端口",
            instance_id=instance_id,
            port_range=f"{self.start_port}-{self.end_port}"
        )
        return None
    
    def release_port(self, instance_id: str) -> bool:
        """
        释放实例的端口
        
        Args:
            instance_id: 实例ID
        
        Returns:
            是否释放成功
        """
        if instance_id not in self.port_mappings:
            logger.warning("未找到该实例的端口分配", instance_id=instance_id)
            return False
        
        port = self.port_mappings.pop(instance_id)
        self.allocated_ports.discard(port)
        
        logger.info("释放Bot实例的端口", instance_id=instance_id, port=port)
        return True
    
    def get_port(self, instance_id: str) -> Optional[int]:
        """
        获取实例已分配的端口
        
        Args:
            instance_id: 实例ID
        
        Returns:
            端口号或None
        """
        return self.port_mappings.get(instance_id)
    
    def get_all_ports(self) -> Dict[str, int]:
        """
        获取所有已分配的端口映射
        
        Returns:
            {instance_id: port}
        """
        return self.port_mappings.copy()
    
    def get_next_available_port(self) -> Optional[int]:
        """
        获取下一个可用的端口（不分配）
        
        Returns:
            可用的端口号或None
        """
        for port in range(self.start_port, self.end_port):
            if self.is_port_available(port):
                return port
        return None
    
    def find_conflicting_ports(self) -> Dict[int, List[str]]:
        """
        查找冲突的端口（多个实例使用相同端口）
        
        Returns:
            {port: [instance_id_list]}
        """
        conflicts = {}
        port_to_instances = {}
        
        for instance_id, port in self.port_mappings.items():
            if port not in port_to_instances:
                port_to_instances[port] = []
            port_to_instances[port].append(instance_id)
        
        for port, instances in port_to_instances.items():
            if len(instances) > 1:
                conflicts[port] = instances
        
        return conflicts


class BotPortManager:
    """
    Bot端口管理器
    与多Bot系统集成，自动管理Bot实例的端口分配
    """
    
    def __init__(self, multi_bot_manager, start_port: int = 8000, end_port: int = 9000):
        """
        初始化Bot端口管理器
        
        Args:
            multi_bot_manager: MultiBotManager实例
            start_port: 起始端口
            end_port: 结束端口
        """
        self.multi_bot_manager = multi_bot_manager
        self.port_allocator = PortAllocator(start_port, end_port)
        self.env_file_template = ".env"
    
    def allocate_port_for_instance(
        self,
        group_name: str,
        instance_id: str,
        preferred_port: Optional[int] = None
    ) -> Optional[int]:
        """
        为Bot实例分配端口
        
        Args:
            group_name: 组名称
            instance_id: 实例ID
            preferred_port: 首选端口（可选）
        
        Returns:
            分配的端口或None
        """
        # 生成唯一的实例标识
        unique_id = f"{group_name}_{instance_id}"
        
        # 分配端口
        port = self.port_allocator.allocate_port(unique_id, preferred_port)
        
        if port:
            # 获取实例并更新配置
            instance = self.multi_bot_manager.get_instance(group_name, instance_id)
            if instance:
                if "ports" not in instance.config:
                    instance.config["ports"] = {}
                instance.config["ports"]["api"] = port
                logger.info(
                    "为Bot实例更新端口配置",
                    group_name=group_name,
                    instance_id=instance_id,
                    port=port
                )
            
            # 保存配置
            self.multi_bot_manager.save_config()
        
        return port
    
    def get_instance_port(self, group_name: str, instance_id: str) -> Optional[int]:
        """
        获取实例的端口
        
        Args:
            group_name: 组名称
            instance_id: 实例ID
        
        Returns:
            端口号或None
        """
        unique_id = f"{group_name}_{instance_id}"
        return self.port_allocator.get_port(unique_id)
    
    def setup_env_file(
        self,
        bot_cwd: str,
        port: int,
        additional_vars: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        设置Bot的.env文件
        
        Args:
            bot_cwd: Bot工作目录
            port: 分配的端口
            additional_vars: 额外的环境变量
        
        Returns:
            是否设置成功
        """
        try:
            env_path = Path(bot_cwd) / self.env_file_template
            
            # 读取现有的.env文件（如果存在）
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = ""
            
            # 更新PORT值
            import re
            if 'PORT=' in content:
                content = re.sub(r'PORT=\d+', f'PORT={port}', content)
            else:
                content += f"\nPORT={port}\n"
            
            # 添加额外的环境变量
            if additional_vars:
                for key, value in additional_vars.items():
                    pattern = f'{key}=.*'
                    if re.search(pattern, content):
                        content = re.sub(pattern, f'{key}={value}', content)
                    else:
                        content += f"\n{key}={value}\n"
            
            # 写入.env文件
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(
                "Bot .env文件配置成功",
                bot_cwd=bot_cwd,
                port=port
            )
            return True
        
        except Exception as e:
            logger.error(
                "设置Bot .env文件失败",
                bot_cwd=bot_cwd,
                error=str(e)
            )
            return False
    
    def get_port_info(self, group_name: str) -> Dict[str, Any]:
        """
        获取组内所有实例的端口信息
        
        Args:
            group_name: 组名称
        
        Returns:
            {instance_id: {port, status, ...}}
        """
        group = self.multi_bot_manager.get_group(group_name)
        if not group:
            return {}
        
        info = {}
        for instance_id, instance in group.get_all_instances().items():
            port = self.get_instance_port(group_name, instance_id)
            info[instance_id] = {
                "port": port,
                "instance_status": instance.status,
                "is_running": instance.is_running
            }
        
        return info
    
    def get_global_port_status(self) -> Dict[str, Any]:
        """
        获取全局端口分配状态
        
        Returns:
            {
                "allocated_ports": {instance_id: port},
                "available_ports": count,
                "conflicts": {port: [instance_list]},
                "next_available": port
            }
        """
        return {
            "allocated_ports": self.port_allocator.get_all_ports(),
            "available_ports": self.port_allocator.end_port - self.port_allocator.start_port - len(self.port_allocator.allocated_ports),
            "conflicts": self.port_allocator.find_conflicting_ports(),
            "next_available": self.port_allocator.get_next_available_port(),
            "port_range": f"{self.port_allocator.start_port}-{self.port_allocator.end_port}"
        }
    
    def release_group_ports(self, group_name: str) -> Dict[str, bool]:
        """
        释放组内所有实例的端口
        
        Args:
            group_name: 组名称
        
        Returns:
            {instance_id: success}
        """
        group = self.multi_bot_manager.get_group(group_name)
        if not group:
            return {}
        
        results = {}
        for instance_id in group.get_all_instances().keys():
            unique_id = f"{group_name}_{instance_id}"
            success = self.port_allocator.release_port(unique_id)
            results[instance_id] = success
        
        self.multi_bot_manager.save_config()
        return results


# 创建全局端口分配器实例
port_allocator = PortAllocator()
