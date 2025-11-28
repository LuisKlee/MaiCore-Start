# -*- coding: utf-8 -*-
"""
NapCat下载器
与deployment.py中的逻辑保持一致
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import structlog

from ...ui.interface import ui
from .base_downloader import BaseDownloader
from ...modules.deployment import deployment_manager

logger = structlog.get_logger(__name__)


class NapCatDownloader(BaseDownloader):
    """NapCat下载器"""
    
    def __init__(self):
        super().__init__("NapCat")
        self.deployment_manager = deployment_manager
    
    def get_napcat_versions(self) -> List[Dict]:
        """获取NapCat版本列表"""
        try:
            # 使用deployment_manager的方法
            versions = self.deployment_manager.get_napcat_versions()
            return versions
        except Exception as e:
            ui.print_error(f"获取NapCat版本列表失败：{str(e)}")
            logger.error("获取NapCat版本列表失败", error=str(e))
            # 返回默认版本
            return self._get_default_versions()
    
    def _get_default_versions(self) -> List[Dict]:
        """获取默认版本列表"""
        return [
            {
                "name": "v4.8.90-shell",
                "display_name": "v4.8.90 基础版 (推荐)",
                "description": "最推荐的版本，适合大多数用户",
                "download_url": "https://github.com/NapNeko/NapCatQQ/releases/download/v4.8.90/NapCat.Shell.zip",
                "asset_name": "NapCat.Shell.zip",
                "version": "v4.8.90"
            },
            {
                "name": "v4.8.90-framework-onekey",
                "display_name": "v4.8.90 有头一键包",
                "description": "带QQ界面的一键包版本，适合挂机器人的同时附体发消息",
                "download_url": "https://github.com/NapNeko/NapCatQQ/releases/download/v4.8.90/NapCat.Framework.Windows.OneKey.zip",
                "asset_name": "NapCat.Framework.Windows.OneKey.zip",
                "version": "v4.8.90"
            },
            {
                "name": "v4.8.90-shell-onekey",
                "display_name": "v4.8.90 无头一键包",
                "description": "无界面的一键包版本",
                "download_url": "https://github.com/NapNeko/NapCatQQ/releases/download/v4.8.90/NapCat.Shell.Windows.OneKey.zip",
                "asset_name": "NapCat.Shell.Windows.OneKey.zip",
                "version": "v4.8.90"
            }
        ]
    
    def select_version(self) -> Optional[Dict]:
        """选择NapCat版本"""
        try:
            # 获取版本列表
            versions = self.get_napcat_versions()
            
            if not versions:
                ui.print_error("未找到可用的NapCat版本")
                return None
            
            # 显示版本选择菜单
            ui.clear_screen()
            ui.components.show_title("选择NapCat版本", symbol="🐱")
            
            # 创建版本表格
            from rich.table import Table
            table = Table(
                show_header=True,
                header_style=ui.colors["table_header"],
                title="[bold]NapCat 可用版本[/bold]",
                title_style=ui.colors["primary"],
                border_style=ui.colors["border"],
                show_lines=True
            )
            table.add_column("选项", style="cyan", width=6, justify="center")
            table.add_column("版本", style=ui.colors["primary"], width=20)
            table.add_column("类型", style="yellow", width=15, justify="center")
            table.add_column("说明", style="green")
            
            # 显示版本信息
            for i, version in enumerate(versions, 1):
                # 提取版本类型
                version_type = "基础版" if "shell" in version["name"] and "onekey" not in version["name"] else \
                               "有头一键包" if "framework" in version["name"] else \
                               "无头一键包" if "shell" in version["name"] and "onekey" in version["name"] else "未知"
                
                table.add_row(
                    f"[{i}]",
                    version["display_name"],
                    version_type,
                    version["description"]
                )
            
            ui.console.print(table)
            ui.console.print("\n[Enter] 使用默认版本(第一个选项)  [Q] 跳过NapCat下载", style=ui.colors["info"])
            ui.console.print("提示：推荐使用基础版，适合大多数用户", style=ui.colors["success"])
            
            while True:
                choice = ui.get_input("请选择NapCat版本(直接回车使用默认版本)：").strip()
                
                # 如果用户直接按回车，使用默认版本(第一个选项)
                if choice == "":
                    ui.print_info("使用默认版本: " + versions[0]["display_name"])
                    return versions[0]
                
                if choice.upper() == 'Q':
                    return None
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(versions):
                        selected_version = versions[choice_num - 1]
                        ui.print_info("已选择版本: " + selected_version["display_name"])
                        return selected_version
                    else:
                        ui.print_error("无效选项，请重新选择")
                except ValueError:
                    ui.print_error("请输入有效的数字或直接回车使用默认版本")
                    
        except Exception as e:
            ui.print_error(f"选择NapCat版本时发生错误：{str(e)}")
            logger.error("NapCat版本选择失败", error=str(e))
            return None
    
    def download_and_install(self, temp_dir: Path) -> bool:
        """下载并安装NapCat"""
        try:
            # 选择版本
            selected_version = self.select_version()
            if not selected_version:
                ui.print_info("已跳过NapCat下载")
                return True
            
            # 获取下载链接
            download_url = selected_version["download_url"]
            asset_name = selected_version.get("asset_name", "NapCat.zip")
            
            # 创建临时文件
            with tempfile.TemporaryDirectory() as temp_download_dir:
                temp_file = Path(temp_download_dir) / asset_name
                
                ui.print_info(f"开始下载NapCat {selected_version['display_name']}...")
                
                # 下载文件
                if not self.download_file(download_url, str(temp_file)):
                    return False
                
                # 解压到临时目录
                extract_dir = temp_dir / "NapCat_extract"
                extract_dir.mkdir(exist_ok=True)
                
                ui.print_info("正在解压NapCat...")
                
                if asset_name.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                else:
                    # 如果不是zip文件，直接复制
                    import shutil
                    shutil.copy2(temp_file, extract_dir)
                
                ui.print_success("NapCat下载完成")
                logger.info("NapCat下载成功", version=selected_version['display_name'], path=str(extract_dir))
                
                # 查找NapCat安装程序
                installer_exe = None
                napcat_exe = None
                
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        # 查找安装程序
                        if file.lower() == 'napcatinstaller.exe':
                            installer_exe = os.path.join(root, file)
                        # 查找NapCat可执行文件
                        elif file.lower().endswith('.exe') and 'napcat' in file.lower():
                            napcat_exe = os.path.join(root, file)
                
                # 如果找到安装程序，询问是否自动安装
                if installer_exe and os.path.exists(installer_exe):
                    ui.print_info(f"找到NapCat安装程序: {installer_exe}")
                    
                    if ui.confirm("是否自动运行NapCat安装程序？"):
                        installer_success = self._run_installer(installer_exe, extract_dir)
                        if installer_success:
                            ui.print_success("NapCat安装程序已成功启动")
                            return True
                        else:
                            ui.print_error("NapCat安装程序启动失败")
                            return False
                    else:
                        ui.print_info("您可以稍后手动运行安装程序")
                        ui.print_info(f"安装程序位置: {installer_exe}")
                        ui.print_info("安装完成后，系统将自动检测NapCat位置")
                        return True
                else:
                    ui.print_warning("未找到NapCat安装程序")
                    ui.print_info(f"NapCat文件已解压到: {extract_dir}")
                    ui.print_info("请手动处理NapCat文件")
                    return True
                
        except Exception as e:
            ui.print_error(f"下载NapCat时发生错误：{str(e)}")
            logger.error("NapCat下载安装失败", error=str(e))
            return False
    
    def _run_installer(self, installer_path: str, extract_dir: Path) -> bool:
        """运行NapCat安装程序"""
        try:
            ui.print_info("正在启动NapCat安装程序...")
            
            # 使用deployment_manager的方法
            return self.deployment_manager.run_napcat_installer(installer_path)
            
        except Exception as e:
            ui.print_error(f"运行NapCat安装程序失败：{str(e)}")
            logger.error("NapCat安装程序运行失败", error=str(e))
            return False
    
    def check_installation(self) -> tuple[bool, str]:
        """检查NapCat是否已安装"""
        try:
            # 使用deployment_manager的方法
            napcat_path = self.deployment_manager.find_installed_napcat("")
            if napcat_path:
                return True, f"NapCat 已安装，位置: {napcat_path}"
            else:
                return False, "NapCat 未安装"
                
        except Exception as e:
            ui.print_error(f"检查NapCat安装状态时发生错误：{str(e)}")
            logger.error("NapCat安装状态检查失败", error=str(e))
            return False, f"检查安装状态时发生错误: {str(e)}"
    
    def download_and_install_to_directory(self, target_dir: Path) -> bool:
        """下载并安装NapCat到指定目录"""
        try:
            # 获取版本列表
            versions = self.get_napcat_versions()
            if not versions:
                ui.print_error("未找到可用的NapCat版本")
                return False
            
            # 让用户选择版本
            selected_version = self.select_version()
            if not selected_version:
                ui.print_info("用户取消了版本选择")
                return True
            
            # 下载并安装
            return self._download_and_install_version(selected_version, target_dir)
            
        except Exception as e:
            ui.print_error(f"下载并安装NapCat到目录失败：{str(e)}")
            logger.error("NapCat目录安装失败", error=str(e))
            return False
    
    def _download_and_install_version(self, version: Dict, target_dir: Path) -> bool:
        """下载并安装指定版本的NapCat"""
        try:
            download_url = version["download_url"]
            asset_name = version.get("asset_name", "NapCat.zip")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = Path(temp_dir) / asset_name
                
                ui.print_info(f"正在下载NapCat {version['display_name']}...")
                
                # 下载文件
                if not self.download_file(download_url, str(temp_file)):
                    return False
                
                # 解压到目标目录
                ui.print_info("正在解压NapCat文件...")
                
                if asset_name.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                        zip_ref.extractall(target_dir)
                else:
                    # 如果不是zip文件，直接复制
                    import shutil
                    shutil.copy2(temp_file, target_dir / asset_name)
                
                ui.print_success(f"NapCat {version['display_name']} 已下载到: {target_dir}")
                logger.info("NapCat版本下载成功", version=version['display_name'], path=str(target_dir))
                
                return True
                
        except Exception as e:
            ui.print_error(f"下载NapCat版本失败：{str(e)}")
            logger.error("NapCat版本下载失败", error=str(e))
            return False