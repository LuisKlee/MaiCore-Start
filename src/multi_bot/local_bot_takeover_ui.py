"""
本地Bot接管UI界面
提供用户友好的界面来检测和接管本地运行的Bot
"""
import structlog
from ..ui.interface import ui
from .local_bot_takeover import LocalBotDetector, LocalBotTakeover
from .multi_bot_manager import multi_bot_manager

logger = structlog.get_logger(__name__)


class LocalBotTakeoverUI:
    """
    本地Bot接管用户界面
    """
    
    def __init__(self):
        """初始化UI"""
        self.detector = LocalBotDetector()
        self.takeover_manager = LocalBotTakeover(multi_bot_manager)
        self.detected_bots = {}
    
    def show_detection_menu(self):
        """显示检测菜单"""
        while True:
            ui.clear_screen()
            ui.console.print("\n[bold cyan]━━━━━━ 本地Bot检测与接管 ━━━━━━[/bold cyan]")
            
            ui.console.print("\n请选择操作:")
            ui.console.print(" [A] 检测所有本地运行的Bot")
            ui.console.print(" [B] 按类型检测Bot (MaiBot/MoFox/NapCat)")
            ui.console.print(" [C] 接管检测到的Bot到多Bot管理系统")
            ui.console.print(" [D] 监控已接管的Bot实例")
            ui.console.print(" [E] 查看接管统计信息")
            ui.console.print(" [Q] 返回")
            
            choice = ui.get_choice("请选择操作", ["A", "B", "C", "D", "E", "Q"])
            
            if choice == "Q":
                break
            elif choice == "A":
                self.handle_detect_all()
            elif choice == "B":
                self.handle_detect_by_type()
            elif choice == "C":
                self.handle_takeover()
            elif choice == "D":
                self.handle_monitor()
            elif choice == "E":
                self.handle_show_summary()
    
    def handle_detect_all(self):
        """处理检测所有Bot"""
        ui.print_info("正在检测所有本地运行的Bot...")
        self.detected_bots = self.takeover_manager.detect_and_analyze()
        
        if not self.detected_bots:
            ui.print_warning("未检测到任何本地运行的Bot")
        else:
            self.show_detected_bots()
        
        ui.pause()
    
    def handle_detect_by_type(self):
        """处理按类型检测Bot"""
        ui.clear_screen()
        ui.console.print("\n请选择Bot类型:")
        ui.console.print(" [A] MaiBot")
        ui.console.print(" [B] MoFox_bot")
        ui.console.print(" [C] NapCat")
        
        choice = ui.get_choice("请选择", ["A", "B", "C"])
        
        bot_type_map = {
            "A": "MaiBot",
            "B": "MoFox_bot",
            "C": "NapCat"
        }
        
        bot_type = bot_type_map[choice]
        ui.print_info(f"正在检测 {bot_type} 类型的Bot...")
        
        self.detected_bots = self.detector.detect_bots_by_type(bot_type)
        
        if not self.detected_bots:
            ui.print_warning(f"未检测到任何 {bot_type} 类型的Bot")
        else:
            ui.print_success(f"检测到 {len(self.detected_bots)} 个 {bot_type} 进程:")
            self.show_detected_bots()
        
        ui.pause()
    
    def show_detected_bots(self):
        """显示检测到的Bot列表"""
        ui.console.print("\n[bold]检测到的Bot进程:[/bold]")
        ui.console.print("-" * 100)
        
        for idx, (process_key, bot_info) in enumerate(self.detected_bots.items(), 1):
            ui.console.print(f"\n[{idx}] {process_key}")
            ui.console.print(f"    Bot类型: [cyan]{bot_info['bot_type']}[/cyan]")
            ui.console.print(f"    进程ID: [yellow]{bot_info['pid']}[/yellow]")
            ui.console.print(f"    进程名: {bot_info['name']}")
            ui.console.print(f"    内存占用: {bot_info['memory_mb']:.1f} MB")
            ui.console.print(f"    工作目录: {bot_info['cwd']}")
            if bot_info.get('cmdline'):
                ui.console.print(f"    命令行: {' '.join(bot_info['cmdline'][:3])}...")
            ui.console.print(f"    启动时间: {bot_info['create_time']}")
    
    def handle_takeover(self):
        """处理接管Bot"""
        if not self.detected_bots:
            ui.print_warning("没有检测到任何Bot，请先执行检测操作")
            ui.pause()
            return
        
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━ 接管Bot到多Bot管理系统 ━━━━━[/bold cyan]")
        
        # 显示检测到的Bot
        self.show_detected_bots()
        
        ui.console.print("\n[bold]接管选项:[/bold]")
        ui.console.print(" [A] 单个接管")
        ui.console.print(" [B] 批量接管全部")
        
        choice = ui.get_choice("请选择", ["A", "B"])
        
        if choice == "A":
            self.handle_single_takeover()
        else:
            self.handle_batch_takeover()
        
        ui.pause()
    
    def handle_single_takeover(self):
        """单个接管Bot"""
        process_keys = list(self.detected_bots.keys())
        
        ui.console.print("\n请选择要接管的Bot:")
        for idx, process_key in enumerate(process_keys, 1):
            bot_info = self.detected_bots[process_key]
            ui.console.print(f" [{idx}] {bot_info['bot_type']} (PID: {bot_info['pid']})")
        
        try:
            selected_idx = int(ui.get_input("请输入序号 (1开始): ")) - 1
            if selected_idx < 0 or selected_idx >= len(process_keys):
                ui.print_error("序号无效")
                return
            
            selected_process_key = process_keys[selected_idx]
            bot_info = self.detected_bots[selected_process_key]
            
            # 获取接管信息
            group_name = ui.get_input("请输入组名称 (默认: local_bots): ") or "local_bots"
            instance_id = ui.get_input(f"请输入实例ID (默认: {bot_info['bot_type'].lower()}_001): ") or f"{bot_info['bot_type'].lower()}_001"
            
            # 执行接管
            ui.print_info(f"正在接管 {bot_info['bot_type']} (PID: {bot_info['pid']})...")
            
            success = self.takeover_manager.create_takeover_instance(
                selected_process_key,
                group_name,
                instance_id
            )
            
            if success:
                ui.print_success(f"成功接管Bot到组 '{group_name}' 的实例 '{instance_id}'")
            else:
                ui.print_error("接管失败，请查看日志了解详情")
        
        except ValueError:
            ui.print_error("输入格式错误")
    
    def handle_batch_takeover(self):
        """批量接管所有检测到的Bot"""
        group_name = ui.get_input("请输入组名称 (默认: local_bots): ") or "local_bots"
        instance_prefix = ui.get_input("请输入实例ID前缀 (默认: bot): ") or "bot"
        
        ui.print_info(f"正在批量接管 {len(self.detected_bots)} 个Bot...")
        
        results = self.takeover_manager.batch_takeover(
            list(self.detected_bots.keys()),
            group_name,
            instance_prefix
        )
        
        # 显示结果
        success_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - success_count
        
        ui.console.print("\n[bold]接管结果:[/bold]")
        ui.console.print(f"  成功: {success_count}")
        ui.console.print(f"  失败: {failed_count}")
        
        if failed_count > 0:
            ui.console.print("\n[bold red]失败的接管:[/bold red]")
            for process_key, success in results.items():
                if not success:
                    bot_info = self.detected_bots[process_key]
                    ui.console.print(f"  - {bot_info['bot_type']} (PID: {bot_info['pid']})")
    
    def handle_monitor(self):
        """监控已接管的Bot实例"""
        ui.print_info("正在监控已接管的Bot实例...")
        
        monitoring_results = self.takeover_manager.monitor_takeover_instances()
        
        if not monitoring_results:
            ui.print_warning("没有已接管的Bot实例")
            ui.pause()
            return
        
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 已接管Bot实例监控 ━━━━━━[/bold cyan]")
        ui.console.print("-" * 100)
        
        for result_key, result_info in monitoring_results.items():
            status_color = "green" if result_info["is_running"] else "red"
            status_text = "运行中 ✓" if result_info["is_running"] else "已停止 ✗"
            
            ui.console.print(f"\n[{result_info['group_name']}] {result_info['instance_id']}")
            ui.console.print(f"  状态: [{status_color}]{status_text}[/{status_color}]")
            ui.console.print(f"  PID: {result_info['pid']}")
            
            if result_info["is_running"]:
                ui.console.print(f"  内存: {result_info['memory_mb']:.1f} MB")
                ui.console.print(f"  运行时长: {result_info.get('uptime', 'N/A')}")
        
        ui.pause()
    
    def handle_show_summary(self):
        """显示接管统计信息"""
        summary = self.takeover_manager.get_takeover_summary()
        
        ui.clear_screen()
        ui.console.print("\n[bold cyan]━━━━━━ 接管统计信息 ━━━━━━[/bold cyan]")
        
        ui.console.print(f"\n总接管实例数: [bold yellow]{summary['total_takeover']}[/bold yellow]")
        
        if summary['by_group']:
            ui.console.print("\n[bold]按组分类:[/bold]")
            for group_name, count in summary['by_group'].items():
                ui.console.print(f"  - {group_name}: {count} 个实例")
        else:
            ui.print_warning("暂无已接管的实例")
        
        ui.pause()


# 创建全局UI实例
local_bot_takeover_ui = LocalBotTakeoverUI()
