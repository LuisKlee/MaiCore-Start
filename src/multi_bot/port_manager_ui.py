"""
端口管理UI界面
提供用户友好的界面来管理Bot的端口分配
"""
import structlog
from ..ui.interface import ui
from .port_manager import BotPortManager
from .multi_bot_manager import multi_bot_manager

logger = structlog.get_logger(__name__)


class PortManagerUI:
    """
    端口管理用户界面
    """
    
    def __init__(self):
        """初始化UI"""
        self.port_manager = BotPortManager(multi_bot_manager)
    
    def show_port_menu(self):
        """显示端口管理菜单"""
        while True:
            ui.clear_screen()
            ui.console.print("\n[bold cyan]━━━━━━ Bot端口管理 ━━━━━━[/bold cyan]")
            
            ui.console.print("\n请选择操作:")
            ui.console.print(" [A] 为新实例分配端口")
            ui.console.print(" [B] 查看端口分配状态")
            ui.console.print(" [C] 查看组内端口信息")
            ui.console.print(" [D] 检查端口冲突")
            ui.console.print(" [E] 释放组内端口")
            ui.console.print(" [Q] 返回")
            
            choice = ui.get_choice("请选择操作", ["A", "B", "C", "D", "E", "Q"])
            
            if choice == "Q":
                break
            elif choice == "A":
                self.handle_allocate_port()
            elif choice == "B":
                self.handle_show_status()
            elif choice == "C":
                self.handle_show_group_info()
            elif choice == "D":
                self.handle_check_conflicts()
            elif choice == "E":
                self.handle_release_ports()
    
    def handle_allocate_port(self):
        """处理端口分配"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 为Bot实例分配端口 ━━━━━[/bold cyan]")
        
        # 列出所有组
        groups = self.port_manager.multi_bot_manager.get_all_groups()
        if not groups:
            ui.print_warning("没有任何Bot组，请先创建Bot组")
            ui.pause()
            return
        
        group_names = list(groups.keys())
        ui.console.print("\n可用的Bot组:")
        for idx, group_name in enumerate(group_names, 1):
            ui.console.print(f" [{idx}] {group_name}")
        
        try:
            group_idx = int(ui.get_input("请选择组 (序号): ")) - 1
            if group_idx < 0 or group_idx >= len(group_names):
                ui.print_error("序号无效")
                ui.pause()
                return
            
            selected_group = group_names[group_idx]
            
            # 列出组内实例
            group = groups[selected_group]
            instances = group.get_all_instances()
            
            if not instances:
                ui.print_warning(f"组 '{selected_group}' 中没有任何实例")
                ui.pause()
                return
            
            instance_ids = list(instances.keys())
            ui.console.print(f"\n组 '{selected_group}' 中的实例:")
            for idx, instance_id in enumerate(instance_ids, 1):
                current_port = self.port_manager.get_instance_port(selected_group, instance_id)
                port_info = f" (已分配: {current_port})" if current_port else " (未分配)"
                ui.console.print(f" [{idx}] {instance_id}{port_info}")
            
            inst_idx = int(ui.get_input("请选择实例 (序号): ")) - 1
            if inst_idx < 0 or inst_idx >= len(instance_ids):
                ui.print_error("序号无效")
                ui.pause()
                return
            
            selected_instance = instance_ids[inst_idx]
            
            # 是否指定首选端口
            use_preferred = ui.confirm("是否指定首选端口? (默认自动分配)")
            preferred_port = None
            
            if use_preferred:
                try:
                    preferred_port = int(ui.get_input("请输入首选端口: "))
                except ValueError:
                    ui.print_error("端口号必须是数字")
                    ui.pause()
                    return
            
            # 分配端口
            ui.print_info(f"正在为 {selected_instance} 分配端口...")
            port = self.port_manager.allocate_port_for_instance(
                selected_group,
                selected_instance,
                preferred_port
            )
            
            if port:
                ui.print_success(f"成功分配端口 {port} 给实例 {selected_instance}")
                
                # 是否设置.env文件
                if ui.confirm("是否为该实例配置 .env 文件?"):
                    instance = group.get_instance(selected_instance)
                    if instance and instance.config.get("cwd"):
                        self.port_manager.setup_env_file(
                            instance.config["cwd"],
                            port
                        )
                        ui.print_success("已配置 .env 文件")
            else:
                ui.print_error("端口分配失败，请查看日志")
        
        except ValueError:
            ui.print_error("输入格式错误")
        
        ui.pause()
    
    def handle_show_status(self):
        """显示全局端口分配状态"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 全局端口分配状态 ━━━━━[/bold cyan]")
        
        status = self.port_manager.get_global_port_status()
        
        ui.console.print(f"\n[bold]端口范围:[/bold] {status['port_range']}")
        ui.console.print(f"[bold]已分配端口数:[/bold] {len(status['allocated_ports'])}")
        ui.console.print(f"[bold]可用端口数:[/bold] {status['available_ports']}")
        ui.console.print(f"[bold]下一个可用端口:[/bold] {status['next_available'] or '无'}")
        
        if status['allocated_ports']:
            ui.console.print("\n[bold]已分配的端口:[/bold]")
            for instance_id, port in sorted(status['allocated_ports'].items(), key=lambda x: x[1]):
                ui.console.print(f"  {instance_id}: {port}")
        
        if status['conflicts']:
            ui.console.print("\n[bold red]⚠ 端口冲突:[/bold red]")
            for port, instances in status['conflicts'].items():
                ui.console.print(f"  端口 {port} 被以下实例使用:")
                for instance_id in instances:
                    ui.console.print(f"    - {instance_id}")
        
        ui.pause()
    
    def handle_show_group_info(self):
        """显示组内端口信息"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 查看组内端口信息 ━━━━━[/bold cyan]")
        
        groups = self.port_manager.multi_bot_manager.get_all_groups()
        if not groups:
            ui.print_warning("没有任何Bot组")
            ui.pause()
            return
        
        group_names = list(groups.keys())
        ui.console.print("\n可用的Bot组:")
        for idx, group_name in enumerate(group_names, 1):
            ui.console.print(f" [{idx}] {group_name}")
        
        try:
            group_idx = int(ui.get_input("请选择组 (序号): ")) - 1
            if group_idx < 0 or group_idx >= len(group_names):
                ui.print_error("序号无效")
                ui.pause()
                return
            
            selected_group = group_names[group_idx]
            info = self.port_manager.get_port_info(selected_group)
            
            if not info:
                ui.print_warning(f"组 '{selected_group}' 中没有任何实例")
                ui.pause()
                return
            
            ui.console.print(f"\n[bold]组 '{selected_group}' 的端口信息:[/bold]")
            ui.console.print("-" * 80)
            
            for instance_id, port_info in info.items():
                port = port_info['port']
                status = port_info['instance_status']
                is_running = port_info['is_running']
                
                status_color = "green" if is_running else "red"
                status_text = "运行中 ✓" if is_running else "已停止 ✗"
                
                port_text = f"{port}" if port else "[yellow]未分配[/yellow]"
                
                ui.console.print(f"\n{instance_id}")
                ui.console.print(f"  端口: {port_text}")
                ui.console.print(f"  状态: [{status_color}]{status_text}[/{status_color}]")
                ui.console.print(f"  实例状态: {status}")
        
        except ValueError:
            ui.print_error("输入格式错误")
        
        ui.pause()
    
    def handle_check_conflicts(self):
        """检查端口冲突"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 检查端口冲突 ━━━━━[/bold cyan]")
        
        status = self.port_manager.get_global_port_status()
        conflicts = status['conflicts']
        
        if not conflicts:
            ui.print_success("✓ 没有端口冲突，所有实例的端口分配正确")
        else:
            ui.print_error(f"❌ 检测到 {len(conflicts)} 个端口冲突:")
            ui.console.print("")
            for port, instances in sorted(conflicts.items()):
                ui.console.print(f"[bold red]端口 {port} 冲突:[/bold red]")
                for instance_id in instances:
                    ui.console.print(f"  - {instance_id}")
        
        ui.pause()
    
    def handle_release_ports(self):
        """释放组内端口"""
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 释放组内端口 ━━━━━[/bold cyan]")
        
        groups = self.port_manager.multi_bot_manager.get_all_groups()
        if not groups:
            ui.print_warning("没有任何Bot组")
            ui.pause()
            return
        
        group_names = list(groups.keys())
        ui.console.print("\n可用的Bot组:")
        for idx, group_name in enumerate(group_names, 1):
            ui.console.print(f" [{idx}] {group_name}")
        
        try:
            group_idx = int(ui.get_input("请选择要释放端口的组 (序号): ")) - 1
            if group_idx < 0 or group_idx >= len(group_names):
                ui.print_error("序号无效")
                ui.pause()
                return
            
            selected_group = group_names[group_idx]
            
            if not ui.confirm(f"确认要释放组 '{selected_group}' 的所有端口吗?"):
                ui.print_info("已取消")
                ui.pause()
                return
            
            ui.print_info(f"正在释放 '{selected_group}' 的端口...")
            results = self.port_manager.release_group_ports(selected_group)
            
            success_count = sum(1 for s in results.values() if s)
            failed_count = len(results) - success_count
            
            ui.console.print("\n[bold]释放结果:[/bold]")
            ui.console.print(f"  成功: {success_count}")
            ui.console.print(f"  失败: {failed_count}")
            
            if failed_count > 0:
                ui.console.print("\n[bold red]失败的实例:[/bold red]")
                for instance_id, success in results.items():
                    if not success:
                        ui.console.print(f"  - {instance_id}")
        
        except ValueError:
            ui.print_error("输入格式错误")
        
        ui.pause()


# 创建全局UI实例
port_manager_ui = PortManagerUI()
