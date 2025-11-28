# -*- coding: utf-8 -*-
"""
MongoDB下载器
"""

import platform
from pathlib import Path
from typing import Optional
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader

logger = structlog.get_logger(__name__)


class MongoDBDownloader(BaseDownloader):
    """MongoDB下载器"""
    
    def __init__(self):
        super().__init__("MongoDB")
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # 标准化架构名称
        if self.arch in ['x86_64', 'amd64']:
            self.arch = 'x86_64'
        elif self.arch in ['arm64', 'aarch64']:
            self.arch = 'arm64'
        else:
            self.arch = 'x86_64'
    
    def get_download_url(self) -> str:
        """获取MongoDB下载链接"""
        version = "7.0.4"
        
        if self.system == 'windows':
            return f"https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-{version}.msi"
        elif self.system == 'darwin':  # macOS
            return f"https://fastdl.mongodb.org/macos/mongodb-macos-{self.arch}-{version}.dmg"
        else:  # Linux
            return f"https://fastdl.mongodb.org/linux/mongodb-linux-{self.arch}-{version}.tgz"
    
    def get_filename(self) -> str:
        """获取下载文件名"""
        version = "7.0.4"
        
        if self.system == 'windows':
            return f"mongodb-windows-x86_64-{version}.msi"
        elif self.system == 'darwin':
            return f"mongodb-macos-{self.arch}-{version}.dmg"
        else:
            return f"mongodb-linux-{self.arch}-{version}.tgz"
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装MongoDB"""
        try:
            # 获取下载链接和文件名
            download_url = self.get_download_url()
            filename = self.get_filename()
            file_path = temp_dir / filename
            
            ui.print_info(f"正在下载 {self.name}...")
            
            # 下载文件
            if not self.download_file(download_url, str(file_path)):
                return False
            
            ui.print_info(f"正在安装 {self.name}...")
            
            # 根据系统执行安装
            if self.system == 'windows':
                # Windows系统
                success = self.run_installer(str(file_path))
            elif self.system == 'darwin':
                # macOS - 提示用户手动安装
                ui.print_info("MongoDB for macOS 需要手动安装")
                ui.print_info(f"请打开下载的文件: {file_path}")
                if ui.confirm("是否打开MongoDB安装包？"):
                    try:
                        import os
                        os.system(f"open '{file_path}'")
                        ui.print_info("已尝试打开安装包，请按照提示完成安装")
                        return True
                    except Exception as e:
                        ui.print_error(f"打开安装包失败: {str(e)}")
                        return False
                return True
            else:
                # Linux - 提示使用包管理器
                ui.print_info("MongoDB for Linux 推荐使用包管理器安装")
                ui.print_info("例如: sudo apt install mongodb (Ubuntu/Debian)")
                ui.print_info("或者: sudo yum install mongodb (CentOS/RHEL)")
                ui.print_info("或者从官方仓库安装最新版本")
                return True
            
            return success
            
        except Exception as e:
            ui.print_error(f"下载 {self.name} 时发生错误：{str(e)}")
            logger.error("MongoDB下载安装失败", error=str(e))
            return False
    
    def check_installation(self) -> tuple[bool, str]:
        """检查MongoDB是否已安装"""
        try:
            import subprocess
            result = subprocess.run(
                ["mongod", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 解析版本信息
                version_line = result.stdout.split('\n')[0]
                return True, f"MongoDB 已安装，版本: {version_line}"
            else:
                return False, "MongoDB 未安装"
                
        except Exception as e:
            return False, f"检查MongoDB安装状态时发生错误: {str(e)}"