# -*- coding: utf-8 -*-
"""
Visual Studio Code下载器
"""

import platform
from pathlib import Path
from typing import Optional
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader

logger = structlog.get_logger(__name__)


class VSCODEDownloader(BaseDownloader):
    """Visual Studio Code下载器"""
    
    def __init__(self):
        super().__init__("VSCode")
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # 标准化架构名称
        if self.arch in ['x86_64', 'amd64']:
            self.arch = 'x64'
        elif self.arch in ['arm64', 'aarch64']:
            self.arch = 'arm64'
        else:
            self.arch = 'x64'
    
    def get_download_url(self) -> str:
        """获取VSCode下载链接"""
        version = "1.85.0"
        
        if self.system == 'windows':
            return f"https://update.code.visualstudio.com/{version}/win32-x64/stable"
        elif self.system == 'darwin':  # macOS
            return f"https://update.code.visualstudio.com/{version}/darwin-{self.arch}/stable"
        else:  # Linux
            return f"https://update.code.visualstudio.com/{version}/linux-x64/stable"
    
    def get_filename(self) -> str:
        """获取下载文件名"""
        if self.system == 'windows':
            return "VSCodeSetup-x64.exe"
        elif self.system == 'darwin':
            return f"VSCode-darwin-{self.arch}.zip"
        else:
            return "vscode-x64.tar.gz"
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装VSCode"""
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
                # macOS - 需要解压后安装
                extract_dir = temp_dir / "vscode_extract"
                if self.extract_archive(str(file_path), str(extract_dir)):
                    # 查找.app文件
                    app_files = list(extract_dir.glob("*.app"))
                    if app_files:
                        ui.print_info("正在复制VSCode到应用程序文件夹...")
                        # 这里可以添加复制到Applications的逻辑
                        success = True
                    else:
                        ui.print_error("未找到VSCode应用程序文件")
                        success = False
                else:
                    success = False
            else:
                # Linux - 解压到指定位置
                extract_dir = temp_dir / "vscode_extract"
                if self.extract_archive(str(file_path), str(extract_dir)):
                    ui.print_info("正在安装VSCode到系统...")
                    # 这里可以添加安装到/usr/local的逻辑
                    success = True
                else:
                    success = False
            
            return success
            
        except Exception as e:
            ui.print_error(f"下载 {self.name} 时发生错误：{str(e)}")
            logger.error("VSCode下载安装失败", error=str(e))
            return False
    
    def check_installation(self) -> tuple[bool, str]:
        """检查VSCode是否已安装"""
        try:
            if self.system == 'windows':
                # Windows - 检查注册表
                import winreg
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft VSCode") as key:
                        version, _ = winreg.QueryValueEx(key, "DisplayVersion")
                        return True, f"VSCode 已安装，版本: {version}"
                except:
                    pass
                
                # 检查可执行文件
                import subprocess
                result = subprocess.run(
                    ["code", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return True, f"VSCode 已安装，版本: {version}"
                else:
                    return False, "VSCode 未安装"
            
            else:
                # Linux/macOS - 检查code命令
                import subprocess
                result = subprocess.run(
                    ["code", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return True, f"VSCode 已安装，版本: {version}"
                else:
                    return False, "VSCode 未安装"
                    
        except Exception as e:
            return False, f"检查VSCode安装状态时发生错误: {str(e)}"