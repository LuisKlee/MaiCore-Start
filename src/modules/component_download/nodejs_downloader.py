# -*- coding: utf-8 -*-
"""
Node.js下载器
"""

import platform
from pathlib import Path
from typing import Optional
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader

logger = structlog.get_logger(__name__)


class NodeJSDownloader(BaseDownloader):
    """Node.js下载器"""
    
    def __init__(self):
        super().__init__("Node.js")
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # 标准化架构名称
        if self.arch in ['x86_64', 'amd64']:
            self.arch = 'x64'
        elif self.arch in ['arm64', 'aarch64']:
            self.arch = 'arm64'
        else:
            self.arch = 'x64'  # 默认使用x64
    
    def get_download_url(self) -> str:
        """获取Node.js下载链接"""
        # 使用Node.js官方LTS版本
        if self.system == 'windows':
            return f"https://nodejs.org/dist/v20.11.0/node-v20.11.0-{self.arch}.msi"
        elif self.system == 'darwin':  # macOS
            return f"https://nodejs.org/dist/v20.11.0/node-v20.11.0-{self.arch}.pkg"
        else:  # Linux
            return f"https://nodejs.org/dist/v20.11.0/node-v20.11.0-{self.arch}.tar.gz"
    
    def get_filename(self) -> str:
        """获取下载文件名"""
        if self.system == 'windows':
            return f"nodejs-v20.11.0-{self.arch}.msi"
        elif self.system == 'darwin':
            return f"nodejs-v20.11.0-{self.arch}.pkg"
        else:
            return f"nodejs-v20.11.0-{self.arch}.tar.gz"
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装Node.js"""
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
                # Windows系统使用MSI安装包
                success = self.run_installer(str(file_path))
            elif self.system == 'darwin':
                # macOS系统使用PKG安装包
                success = self.run_installer(str(file_path))
            else:
                # Linux系统需要解压和编译安装
                success = self._install_from_source(file_path, temp_dir)
            
            return success
            
        except Exception as e:
            ui.print_error(f"下载 {self.name} 时发生错误：{str(e)}")
            logger.error("Node.js下载安装失败", error=str(e))
            return False
    
    def _install_from_source(self, file_path: Path, temp_dir: Path) -> bool:
        """从源码安装Node.js（Linux）"""
        try:
            ui.print_info("正在解压Node.js源码...")
            
            # 解压源码
            extract_dir = temp_dir / "nodejs_source"
            if not self.extract_archive(str(file_path), str(extract_dir)):
                return False
            
            # 查找解压后的目录
            node_dirs = list(extract_dir.glob("node-v*"))
            if not node_dirs:
                ui.print_error("未找到Node.js源码目录")
                return False
            
            source_dir = node_dirs[0]
            
            ui.print_info(f"正在编译安装Node.js到 {source_dir}...")
            
            # 配置、编译和安装
            configure_cmd = ["./configure", f"--prefix=/usr/local"]
            make_cmd = ["make", "-j", str(Path.cpu_count() or 4)]
            install_cmd = ["sudo", "make", "install"]
            
            # 运行配置
            ui.print_info("运行 ./configure...")
            result = subprocess.run(configure_cmd, cwd=source_dir, capture_output=True, text=True)
            if result.returncode != 0:
                ui.print_error(f"配置失败: {result.stderr}")
                return False
            
            # 编译
            ui.print_info("编译Node.js...")
            result = subprocess.run(make_cmd, cwd=source_dir, capture_output=True, text=True)
            if result.returncode != 0:
                ui.print_error(f"编译失败: {result.stderr}")
                return False
            
            # 安装
            ui.print_info("安装Node.js...")
            result = subprocess.run(install_cmd, cwd=source_dir, capture_output=True, text=True)
            if result.returncode != 0:
                ui.print_error(f"安装失败: {result.stderr}")
                return False
            
            ui.print_success(f"{self.name} 安装完成")
            return True
            
        except Exception as e:
            ui.print_error(f"从源码安装 {self.name} 失败：{str(e)}")
            logger.error("Node.js源码安装失败", error=str(e))
            return False
    
    def check_installation(self) -> tuple[bool, str]:
        """检查Node.js是否已安装"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Node.js 已安装，版本: {version}"
            else:
                return False, "Node.js 未安装"
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Node.js 未安装"
        except Exception as e:
            return False, f"检查安装状态时发生错误: {str(e)}"