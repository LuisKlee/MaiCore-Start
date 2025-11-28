# -*- coding: utf-8 -*-
"""
Git下载器
"""

import platform
from pathlib import Path
from typing import Optional
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader

logger = structlog.get_logger(__name__)


class GitDownloader(BaseDownloader):
    """Git下载器"""
    
    def __init__(self):
        super().__init__("Git")
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # 标准化架构名称
        if self.arch in ['x86_64', 'amd64']:
            self.arch = '64'
        elif self.arch in ['arm64', 'aarch64']:
            self.arch = 'arm64'
        else:
            self.arch = '64'
    
    def get_download_url(self) -> str:
        """获取Git下载链接"""
        if self.system == 'windows':
            return f"https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-{self.arch}-2.43.0.0-64-bit.exe"
        elif self.system == 'darwin':  # macOS
            return f"https://sourceforge.net/projects/git-osx-installer/files/git-2.43.0-intel-universal-mavericks.dmg/download"
        else:  # Linux
            return "https://github.com/git/git/archive/refs/tags/v2.43.0.tar.gz"
    
    def get_filename(self) -> str:
        """获取下载文件名"""
        if self.system == 'windows':
            return f"Git-{self.arch}-2.43.0.0.exe"
        elif self.system == 'darwin':
            return "git-2.43.0.dmg"
        else:
            return "git-2.43.0.tar.gz"
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装Git"""
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
                ui.print_info("Git for macOS 需要手动安装")
                ui.print_info(f"请打开下载的文件: {file_path}")
                if ui.confirm("是否打开Git安装包？"):
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
                ui.print_info("Git for Linux 推荐使用包管理器安装")
                ui.print_info("例如: sudo apt install git (Ubuntu/Debian)")
                ui.print_info("或者: sudo yum install git (CentOS/RHEL)")
                return True
            
            return success
            
        except Exception as e:
            ui.print_error(f"下载 {self.name} 时发生错误：{str(e)}")
            logger.error("Git下载安装失败", error=str(e))
            return False
    
    def check_installation(self) -> tuple[bool, str]:
        """检查Git是否已安装"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Git 已安装，版本: {version}"
            else:
                return False, "Git 未安装"
                
        except Exception as e:
            return False, f"检查Git安装状态时发生错误: {str(e)}"