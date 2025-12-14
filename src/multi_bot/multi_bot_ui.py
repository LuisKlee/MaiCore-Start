"""
多Bot管理系统UI界面
提供用户友好的交互式界面来管理多个Bot实例
"""
import structlog
from ..ui.interface import ui
from .multi_bot_manager import multi_bot_manager
from rich.table import Table
from rich.panel import Panel
import json

logger = structlog.get_logger(__name__)


class MultiBotUI:
    """
    多Bot管理用户界面
    """
    
    def __init__(self):
        """初始化UI"""
        self.manager = multi_bot_manager
    
    def show_main_menu(self):
        """显示主菜单"""
        while True:
            ui.clear_screen()
            ui.console.print("\n[bold cyan]━━━━━━ 多Bot管理系统 ━━━━━━[/bold cyan]")
            
            # 显示快速状态概览
            self._show_quick_status()
            
            ui.console.print("\n[bold]请选择操作:[/bold]")
            ui.console.print(" [1] 查看所有Bot组")
            ui.console.print(" [2] 创建新Bot组")
            ui.console.print(" [3] 管理Bot组")
            ui.console.print(" [4] 管理Bot实例")
            ui.console.print(" [5] 查看全局状态")
            ui.console.print(" [6] 启动/停止操作")
            ui.console.print(" [7] 配置管理")
            ui.console.print(" [8] 导入/导出配置")
            ui.console.print(" [Q] 返回主菜单")
            
            choice = ui.get_choice("请选择操作", ["1", "2", "3", "4", "5", "6", "7", "8", "Q"])
            
            if choice == "Q":
                break
            elif choice == "1":
                self.handle_view_groups()
            elif choice == "2":
                self.handle_create_group()
            elif choice == "3":
                self.handle_manage_group()
            elif choice == "4":
                self.handle_manage_instances()
            elif choice == "5":
                self.handle_view_global_status()
            elif choice == "6":
                self.handle_start_stop_operations()
            elif choice == "7":
                self.handle_config_management()
            elif choice == "8":
                self.handle_import_export()
    
    def _show_quick_status(self):
        """显示快速状态概览"""
        try:
            status = self.manager.get_global_status()
            
            status_text = f"组数: [cyan]{status['total_groups']}[/cyan] | " \
                         f"实例总数: [cyan]{status['total_instances']}[/cyan] | " \
                         f"运行中: [green]{status['total_running']}[/green] | " \
                         f"已停止: [yellow]{status['total_stopped']}[/yellow]"
            
            ui.console.print(Panel(status_text, title="系统状态", border_style="blue"))
        except Exception as e:
            logger.debug("获取快速状态失败", error=str(e))
    
    def handle_view_groups(self):
        """处理查看所有Bot组"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ Bot组列表 ━━━━━━[/bold cyan]\n")
        
        groups = self.manager.get_all_groups()
        
        if not groups:
            ui.print_warning("当前没有任何Bot组")
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("组名", style="cyan")
            table.add_column("实例数", justify="right")
            table.add_column("运行中", justify="right", style="green")
            table.add_column("已停止", justify="right", style="yellow")
            table.add_column("启动间隔", justify="right")
            table.add_column("最大实例数", justify="right")
            
            for group_name, group in groups.items():
                status = group.get_group_status()
                table.add_row(
                    group_name,
                    str(status['total_instances']),
                    str(status['running_count']),
                    str(status['stopped_count']),
                    f"{group.group_config.get('launch_interval', 0)}秒",
                    str(group.group_config.get('max_instances', 'N/A'))
                )
            
            ui.console.print(table)
        
        ui.pause()
    
    def handle_create_group(self):
        """处理创建新Bot组"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 创建新Bot组 ━━━━━━[/bold cyan]\n")
        
        # 获取组名
        group_name = ui.get_input("请输入组名")
        if not group_name:
            ui.print_warning("组名不能为空")
            ui.pause()
            return
        
        # 检查是否已存在
        if self.manager.get_group(group_name):
            ui.print_error(f"组 '{group_name}' 已存在")
            ui.pause()
            return
        
        # 获取配置
        ui.console.print("\n[bold]组配置:[/bold]")
        
        try:
            launch_interval = ui.get_input("启动间隔(秒, 默认2)", default="2")
            launch_interval = int(launch_interval)
            
            max_instances = ui.get_input("最大实例数(默认10)", default="10")
            max_instances = int(max_instances)
            
            config = {
                "launch_interval": launch_interval,
                "max_instances": max_instances
            }
            
            # 创建组
            group = self.manager.create_group(group_name, config)
            ui.print_success(f"✓ 成功创建组: {group_name}")
            
            # 保存配置
            self.manager.save_config()
            ui.print_success("✓ 配置已保存")
            
        except ValueError:
            ui.print_error("输入的数值格式不正确")
        except Exception as e:
            ui.print_error(f"创建组失败: {e}")
            logger.error("创建组失败", error=str(e))
        
        ui.pause()
    
    def handle_manage_group(self):
        """处理管理Bot组"""
        groups = self.manager.get_all_groups()
        
        if not groups:
            ui.print_warning("当前没有任何Bot组")
            ui.pause()
            return
        
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 选择要管理的组 ━━━━━━[/bold cyan]\n")
        
        group_names = list(groups.keys())
        for idx, name in enumerate(group_names, 1):
            ui.console.print(f" [{idx}] {name}")
        ui.console.print(" [Q] 返回")
        
        choices = [str(i) for i in range(1, len(group_names) + 1)] + ["Q"]
        choice = ui.get_choice("请选择组", choices)
        
        if choice == "Q":
            return
        
        group_name = group_names[int(choice) - 1]
        self._show_group_menu(group_name)
    
    def _show_group_menu(self, group_name):
        """显示组管理菜单"""
        while True:
            ui.clear_screen()
            ui.console.print(f"\n[bold cyan]━━━━━━ 管理组: {group_name} ━━━━━━[/bold cyan]\n")
            
            group = self.manager.get_group(group_name)
            if not group:
                ui.print_error(f"组 '{group_name}' 不存在")
                ui.pause()
                return
            
            # 显示组状态
            status = group.get_group_status()
            ui.console.print(f"实例总数: {status['total_instances']} | "
                           f"运行中: [green]{status['running_count']}[/green] | "
                           f"已停止: [yellow]{status['stopped_count']}[/yellow]\n")
            
            ui.console.print("[bold]请选择操作:[/bold]")
            ui.console.print(" [1] 查看组中的所有实例")
            ui.console.print(" [2] 添加新实例到组")
            ui.console.print(" [3] 启动组中所有实例")
            ui.console.print(" [4] 停止组中所有实例")
            ui.console.print(" [5] 删除此组")
            ui.console.print(" [Q] 返回")
            
            choice = ui.get_choice("请选择操作", ["1", "2", "3", "4", "5", "Q"])
            
            if choice == "Q":
                break
            elif choice == "1":
                self._view_group_instances(group_name)
            elif choice == "2":
                self._add_instance_to_group(group_name)
            elif choice == "3":
                self._start_all_in_group(group_name)
            elif choice == "4":
                self._stop_all_in_group(group_name)
            elif choice == "5":
                if self._delete_group(group_name):
                    break
    
    def _view_group_instances(self, group_name):
        """查看组中的所有实例"""
        ui.clear_screen()
        ui.console.print(f"\n[bold cyan]━━━━━━ 组 '{group_name}' 的实例 ━━━━━━[/bold cyan]\n")
        
        group = self.manager.get_group(group_name)
        instances = group.get_all_instances()
        
        if not instances:
            ui.print_warning("该组中没有实例")
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("实例ID", style="cyan")
            table.add_column("状态", justify="center")
            table.add_column("PID", justify="right")
            table.add_column("QQ号", justify="right")
            table.add_column("运行时长")
            
            for instance_id, instance in instances.items():
                status_color = "green" if instance.is_running else "yellow"
                table.add_row(
                    instance_id,
                    f"[{status_color}]{instance.status}[/{status_color}]",
                    str(instance.pid) if instance.pid else "-",
                    instance.config.get('qq_account', 'N/A'),
                    instance.get_uptime() or "-"
                )
            
            ui.console.print(table)
        
        ui.pause()
    
    def _add_instance_to_group(self, group_name):
        """添加新实例到组"""
        ui.clear_screen()
        ui.console.print(f"\n[bold cyan]━━━━━━ 添加实例到组: {group_name} ━━━━━━[/bold cyan]\n")
        
        # 获取实例ID
        instance_id = ui.get_input("请输入实例ID (如: bot_001)")
        if not instance_id:
            ui.print_warning("实例ID不能为空")
            ui.pause()
            return
        
        # 检查是否已存在
        if self.manager.get_instance(group_name, instance_id):
            ui.print_error(f"实例 '{instance_id}' 已存在于组 '{group_name}' 中")
            ui.pause()
            return
        
        # 获取配置
        ui.console.print("\n[bold]实例配置:[/bold]")
        
        bot_path = ui.get_input("Bot路径 (如: D:\\Bots\\bot_001)", default="")
        adapter_path = ui.get_input("适配器路径", default="")
        napcat_path = ui.get_input("NapCat路径", default="")
        qq_account = ui.get_input("QQ账号", default="")
        version = ui.get_input("版本号 (默认: 0.10.0)", default="0.10.0")
        
        config = {
            "bot_path": bot_path,
            "adapter_path": adapter_path,
            "napcat_path": napcat_path,
            "qq_account": qq_account,
            "version": version
        }
        
        try:
            instance = self.manager.create_instance(group_name, instance_id, config)
            ui.print_success(f"✓ 成功添加实例: {instance_id}")
            
            # 保存配置
            self.manager.save_config()
            ui.print_success("✓ 配置已保存")
            
        except Exception as e:
            ui.print_error(f"添加实例失败: {e}")
            logger.error("添加实例失败", error=str(e))
        
        ui.pause()
    
    def _start_all_in_group(self, group_name):
        """启动组中所有实例"""
        ui.print_info(f"启动组 '{group_name}' 中的所有实例...")
        ui.print_warning("注意: 实际启动功能需要配合启动器使用")
        ui.print_info("提示: 请使用多Bot启动功能或手动启动实例")
        ui.pause()
    
    def _stop_all_in_group(self, group_name):
        """停止组中所有实例"""
        ui.print_info(f"停止组 '{group_name}' 中的所有实例...")
        ui.print_warning("注意: 实际停止功能需要配合进程管理器使用")
        ui.print_info("提示: 请使用任务管理器或进程管理功能")
        ui.pause()
    
    def _delete_group(self, group_name):
        """删除组"""
        ui.console.print(f"\n[bold red]警告: 即将删除组 '{group_name}'[/bold red]")
        confirm = ui.get_input("确认删除? (yes/no)", default="no")
        
        if confirm.lower() == "yes":
            try:
                self.manager.delete_group(group_name)
                ui.print_success(f"✓ 已删除组: {group_name}")
                self.manager.save_config()
                ui.pause()
                return True
            except Exception as e:
                ui.print_error(f"删除组失败: {e}")
                ui.pause()
        else:
            ui.print_info("已取消删除操作")
            ui.pause()
        
        return False
    
    def handle_manage_instances(self):
        """处理管理Bot实例"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 管理Bot实例 ━━━━━━[/bold cyan]\n")
        
        # 获取所有实例
        all_instances = []
        for group_name, group in self.manager.get_all_groups().items():
            for instance_id, instance in group.get_all_instances().items():
                all_instances.append((group_name, instance_id, instance))
        
        if not all_instances:
            ui.print_warning("当前没有任何Bot实例")
            ui.pause()
            return
        
        # 显示所有实例
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("编号", justify="right")
        table.add_column("组名", style="cyan")
        table.add_column("实例ID", style="cyan")
        table.add_column("状态", justify="center")
        table.add_column("QQ号", justify="right")
        
        for idx, (group_name, instance_id, instance) in enumerate(all_instances, 1):
            status_color = "green" if instance.is_running else "yellow"
            table.add_row(
                str(idx),
                group_name,
                instance_id,
                f"[{status_color}]{instance.status}[/{status_color}]",
                instance.config.get('qq_account', 'N/A')
            )
        
        ui.console.print(table)
        
        ui.console.print("\n[bold]操作:[/bold]")
        ui.console.print(" 输入实例编号查看详情")
        ui.console.print(" 输入 Q 返回")
        
        choice = ui.get_input("请选择")
        
        if choice.upper() == "Q":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_instances):
                group_name, instance_id, instance = all_instances[idx]
                self._show_instance_detail(group_name, instance_id)
        except ValueError:
            ui.print_error("无效的选择")
            ui.pause()
    
    def _show_instance_detail(self, group_name, instance_id):
        """显示实例详情"""
        ui.clear_screen()
        ui.console.print(f"\n[bold cyan]━━━━━━ 实例详情 ━━━━━━[/bold cyan]\n")
        
        instance = self.manager.get_instance(group_name, instance_id)
        if not instance:
            ui.print_error("实例不存在")
            ui.pause()
            return
        
        # 显示实例信息
        info = instance.to_dict()
        ui.console.print(Panel(
            json.dumps(info, indent=2, ensure_ascii=False),
            title=f"实例: {instance_id}",
            border_style="cyan"
        ))
        
        ui.pause()
    
    def handle_view_global_status(self):
        """处理查看全局状态"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 全局状态 ━━━━━━[/bold cyan]\n")
        
        try:
            status = self.manager.get_global_status()
            
            # 基本统计
            ui.console.print("[bold]系统统计:[/bold]")
            ui.console.print(f"  组数: {status['total_groups']}")
            ui.console.print(f"  实例总数: {status['total_instances']}")
            ui.console.print(f"  运行中: [green]{status['total_running']}[/green]")
            ui.console.print(f"  已停止: [yellow]{status['total_stopped']}[/yellow]")
            ui.console.print(f"  内存占用: {status['total_memory_mb']:.2f} MB")
            
            # 各组详情
            if status['groups']:
                ui.console.print("\n[bold]各组详情:[/bold]")
                
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("组名", style="cyan")
                table.add_column("实例数", justify="right")
                table.add_column("运行中", justify="right", style="green")
                table.add_column("内存(MB)", justify="right")
                
                for group_name, group_status in status['groups'].items():
                    table.add_row(
                        group_name,
                        str(group_status['total_instances']),
                        str(group_status['running_count']),
                        f"{group_status['total_memory_mb']:.2f}"
                    )
                
                ui.console.print(table)
            
        except Exception as e:
            ui.print_error(f"获取状态失败: {e}")
            logger.error("获取全局状态失败", error=str(e))
        
        ui.pause()
    
    def handle_start_stop_operations(self):
        """处理启动/停止操作"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 启动/停止操作 ━━━━━━[/bold cyan]\n")
        
        ui.console.print("[bold yellow]提示:[/bold yellow]")
        ui.console.print("实际的启动/停止功能需要配合进程管理器和启动器使用。")
        ui.console.print("当前版本主要用于配置管理和状态监控。")
        ui.console.print("\n建议使用:")
        ui.console.print("  1. 使用主菜单中的 '多Bot启动' 功能")
        ui.console.print("  2. 手动启动Bot实例")
        ui.console.print("  3. 使用系统任务管理器管理进程")
        
        ui.pause()
    
    def handle_config_management(self):
        """处理配置管理"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 配置管理 ━━━━━━[/bold cyan]\n")
        
        ui.console.print("[bold]请选择操作:[/bold]")
        ui.console.print(" [1] 保存当前配置")
        ui.console.print(" [2] 重新加载配置")
        ui.console.print(" [3] 查看配置文件路径")
        ui.console.print(" [Q] 返回")
        
        choice = ui.get_choice("请选择操作", ["1", "2", "3", "Q"])
        
        if choice == "Q":
            return
        elif choice == "1":
            try:
                self.manager.save_config()
                ui.print_success("✓ 配置已保存")
            except Exception as e:
                ui.print_error(f"保存配置失败: {e}")
        elif choice == "2":
            try:
                self.manager.load_config()
                ui.print_success("✓ 配置已重新加载")
            except Exception as e:
                ui.print_error(f"重新加载配置失败: {e}")
        elif choice == "3":
            ui.console.print(f"\n配置文件路径: {self.manager.config_path}")
        
        ui.pause()
    
    def handle_import_export(self):
        """处理导入/导出配置"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 导入/导出配置 ━━━━━━[/bold cyan]\n")
        
        ui.console.print("[bold]请选择操作:[/bold]")
        ui.console.print(" [1] 导出配置到文件")
        ui.console.print(" [2] 从文件导入配置")
        ui.console.print(" [Q] 返回")
        
        choice = ui.get_choice("请选择操作", ["1", "2", "Q"])
        
        if choice == "Q":
            return
        elif choice == "1":
            export_path = ui.get_input("导出文件路径", default="config/multi_bot_backup.json")
            try:
                if self.manager.export_config(export_path):
                    ui.print_success(f"✓ 配置已导出到: {export_path}")
                else:
                    ui.print_error("导出失败")
            except Exception as e:
                ui.print_error(f"导出配置失败: {e}")
        elif choice == "2":
            import_path = ui.get_input("导入文件路径")
            try:
                if self.manager.import_config(import_path):
                    ui.print_success(f"✓ 配置已从 {import_path} 导入")
                else:
                    ui.print_error("导入失败")
            except Exception as e:
                ui.print_error(f"导入配置失败: {e}")
        
        ui.pause()


def main():
    """多Bot管理UI主函数"""
    ui_instance = MultiBotUI()
    ui_instance.show_main_menu()


if __name__ == "__main__":
    main()
