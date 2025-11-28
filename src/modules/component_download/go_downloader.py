# -*- coding: utf-8 -*-
"""
Go下载器
"""

import platform
import os
from pathlib import Path
from typing import Optional
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader

logger = structlog.get_logger(__name__)


class GoDownloader(BaseDownloader):
    """Go下载器"""
    
    def __init__(self):
        super().__init__("Go")
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # 标准化架构名称
        if self.arch in ['x86_64', 'amd64']:
            self.arch = 'amd64'
        elif self.arch in ['arm64', 'aarch64']:
            self.arch = 'arm64'
        else:
            self.arch = 'amd64'
    
    def get_download_url(self) -> str:
        """获取Go下载链接"""
        version = "1.21.5"
        
        if self.system == 'windows':
            return f"https://go.dev/dl/go{version}.windows-{self.arch}.msi"
        elif self.system == 'darwin':  # macOS
            return f"https://go.dev/dl/go{version}.darwin-{self.arch}.pkg"
        else:  # Linux
            return f"https://go.dev/dl/go{version}.linux-{self.arch}.tar.gz"
    
    def get_filename(self) -> str:
        """获取下载文件名"""
        version = "1.21.5"
        
        if self.system == 'windows':
            return f"go{version}.windows-{self.arch}.msi"
        elif self.system == 'darwin':
            return f"go{version}.darwin-{self.arch}.pkg"
        else:
            return f"go{version}.linux-{self.arch}.tar.gz"
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装Go"""
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
                # macOS
                success = self.run_installer(str(file_path))
            else:
                # Linux - 需要手动解压和设置环境变量
                success = self._install_go_linux(file_path, temp_dir)
            
            return success
            
        except Exception as e:
            ui.print_error(f"下载 {self.name} 时发生错误：{str(e)}")
            logger.error("Go下载安装失败", error=str(e))
            return False
    
    def _install_go_linux(self, file_path: Path, temp_dir: Path) -> bool:
        """在Linux上安装Go"""
        try:
            ui.print_info("正在解压Go安装包...")
            
            # 解压到临时目录
            extract_dir = temp_dir / "go_extract"
            if not self.extract_archive(str(file_path), str(extract_dir)):
                return False
            
            # 查找Go目录
            go_dirs = list(extract_dir.glob("go"))
            if not go_dirs:
                ui.print_error("未找到Go目录")
                return False
            
            go_dir = go_dirs[0]
            
            # 移动到系统位置
            target_dir = Path("/usr/local/go")
            
            ui.print_info(f"正在安装Go到 {target_dir}...")
            
            # 需要sudo权限
            if os.geteuid() != 0:
                ui.print_info("需要sudo权限来安装Go")
                ui.print_info("请手动执行以下命令：")
                ui.print_info(f"sudo rm -rf {target_dir}")
                ui.print_info(f"sudo mv {go_dir} {target_dir}")
                ui.print_info("然后设置环境变量：")
                ui.print_info("export PATH=$PATH:/usr/local/go/bin")
                return True
            else:
                # 移除旧版本
                if target_dir.exists():
                    ui.print_info("移除旧版本Go...")
                    os.system(f"rm -rf {target_dir}")
                
                # 移动新版本
                os.system(f"mv {go_dir} {target_dir}")
                
                # 设置环境变量
                ui.print_info("正在设置Go环境变量...")
                self._set_go_environment()
                
                ui.print_success(f"{self.name} 安装完成")
                return True
            
        except Exception as e:
            ui.print_error(f"安装Go失败：{str(e)}")
            logger.error("Go Linux安装失败", error=str(e))
            return False
    
    def _set_go_environment(self):
        """设置Go环境变量"""
        go_home = "/usr/local/go"
        
        # 检查是否已经设置
        if "GOPATH" in os.environ and "GOROOT" in os.environ:
            ui.print_info("Go环境变量已设置")
            return
        
        ui.print_info("正在设置Go环境变量...")
        
        # 设置GOROOT
        os.environ["GOROOT"] = go_home
        
        # 设置GOPATH
        gopath = os.path.expanduser("~/go")
        os.environ["GOPATH"] = gopath
        
        # 创建GOPATH目录
        Path(gopath).mkdir(exist_ok=True)
        
        # 添加到PATH
        current_path = os.environ.get("PATH", "")
        if go_home + "/bin" not in current_path:
            os.environ["PATH"] = f"{go_home}/bin:{current_path}"
        
        ui.print_info(f"Go安装路径: {go_home}")
        ui.print_info(f"Go工作目录: {gopath}")
        ui.print_info("请将以下内容添加到您的shell配置文件（如 ~/.bashrc 或 ~/.zshrc）：")
        ui.print_info(f"export GOROOT={go_home}")
        ui.print_info(f"export GOPATH={gopath}")
        ui.print_info(f"export PATH=$PATH:$GOROOT/bin:$GOPATH/bin")
    
    def check_installation(self) -> tuple[bool, str]:
        """检查Go是否已安装"""
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Go 已安装，版本: {version}"
            else:
                return False, "Go 未安装"
                
        except Exception as e:
            return False, f"检查Go安装状态时发生错误: {str(e)}"