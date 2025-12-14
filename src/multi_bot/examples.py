"""
多Bot示例使用代码
展示如何使用多Bot管理系统
"""

from src.multi_bot import MultiBotManager


def example_1_basic_management():
    """示例1: 基本的Bot管理操作"""
    print("=" * 50)
    print("示例1: 基本的Bot管理操作")
    print("=" * 50)
    
    # 创建管理器
    manager = MultiBotManager()
    
    # 创建Bot组
    group = manager.create_group("primary_bots", {
        "launch_interval": 2,  # 启动间隔2秒
        "max_instances": 5
    })
    print(f"✓ 创建组: {group}")
    
    # 创建多个Bot实例
    for i in range(3):
        instance_id = f"bot_{i+1:03d}"
        config = {
            "bot_path": f"D:\\Bots\\bot_{i+1}",
            "adapter_path": f"D:\\Bots\\bot_{i+1}\\adapter",
            "napcat_path": "D:\\NapCat",
            "qq_account": f"1234567890{i}",
            "version": "0.10.0"
        }
        
        instance = manager.create_instance("primary_bots", instance_id, config)
        print(f"✓ 创建实例: {instance}")
    
    # 获取组状态
    status = group.get_group_status()
    print("\n组状态:")
    print(f"  - 总实例数: {status['total_instances']}")
    print(f"  - 运行中: {status['running_count']}")
    print(f"  - 已停止: {status['stopped_count']}")
    
    # 获取全局状态
    global_status = manager.get_global_status()
    print("\n全局状态:")
    print(f"  - 组数: {global_status['total_groups']}")
    print(f"  - 实例总数: {global_status['total_instances']}")
    print(f"  - 运行中: {global_status['total_running']}")
    
    # 保存配置
    manager.save_config()
    print("\n✓ 配置已保存")


def example_2_startup_management():
    """示例2: 启动管理"""
    print("\n" + "=" * 50)
    print("示例2: 启动管理")
    print("=" * 50)
    
    manager = MultiBotManager()
    group = manager.get_group("primary_bots")
    
    if not group:
        print("❌ 组不存在，请先运行示例1")
        return
    
    # 准备启动配置
    launch_config = {}
    for instance_id in group.get_all_instances().keys():
        launch_config[instance_id] = {
            "command": f"python run.py --instance {instance_id}",
            "cwd": f"D:\\Bots\\{instance_id}",
            "title": f"MaiBot-{instance_id}"
        }
    
    print(f"准备启动 {len(launch_config)} 个Bot实例:")
    for instance_id in launch_config.keys():
        print(f"  - {instance_id}")
    
    # 注意：实际启动需要提供真实的进程管理器
    # 以下代码展示如何调用
    """
    launcher = MultiBotLauncher(process_manager)
    results = launcher.launch_group("primary_bots", launch_config)
    
    print(f"\n启动结果:")
    for instance_id, (success, pid) in results.items():
        if success:
            print(f"  ✓ {instance_id}: PID {pid}")
        else:
            print(f"  ❌ {instance_id}: 启动失败")
    """
    
    print("\n💡 注意：实际启动需要提供真实的进程管理器实例")


def example_3_event_callbacks():
    """示例3: 事件回调"""
    print("\n" + "=" * 50)
    print("示例3: 事件回调")
    print("=" * 50)
    
    manager = MultiBotManager()
    
    # 定义回调函数
    def on_start(group_name, instance_id, pid):
        print(f"✓ [{group_name}] {instance_id} 已启动 (PID: {pid})")
    
    def on_stop(group_name, instance_id):
        print(f"✓ [{group_name}] {instance_id} 已停止")
    
    def on_error(group_name, instance_id, error):
        print(f"❌ [{group_name}] {instance_id} 发生错误: {error}")
    
    # 注册回调
    manager.register_callback("on_start", on_start)
    manager.register_callback("on_stop", on_stop)
    manager.register_callback("on_error", on_error)
    
    print("✓ 已注册事件回调")
    print("  - on_start: Bot启动时触发")
    print("  - on_stop: Bot停止时触发")
    print("  - on_error: Bot出错时触发")


def example_4_import_export():
    """示例4: 导入导出配置"""
    print("\n" + "=" * 50)
    print("示例4: 导入导出配置")
    print("=" * 50)
    
    manager = MultiBotManager()
    
    # 导出配置
    export_path = "config/multi_bot_backup.json"
    success = manager.export_config(export_path)
    if success:
        print(f"✓ 配置已导出到: {export_path}")
    else:
        print("❌ 导出失败")
    
    # 导入配置
    print("\n导入配置演示 (需要准备好源配置文件):")
    print("  import_path = 'config/multi_bot_backup.json'")
    print("  success = manager.import_config(import_path)")


def example_5_status_monitoring():
    """示例5: 状态监控"""
    print("\n" + "=" * 50)
    print("示例5: 状态监控")
    print("=" * 50)
    
    manager = MultiBotManager()
    
    # 获取全局状态
    status = manager.get_global_status()
    
    print("全局状态信息:")
    print(f"  - 组数: {status['total_groups']}")
    print(f"  - 实例总数: {status['total_instances']}")
    print(f"  - 运行中: {status['total_running']}")
    print(f"  - 已停止: {status['total_stopped']}")
    print(f"  - 内存占用: {status['total_memory_mb']:.2f} MB")
    
    # 按组显示详细信息
    if status['groups']:
        print("\n各组详细信息:")
        for group_name, group_status in status['groups'].items():
            print(f"\n  [{group_name}]")
            print(f"    - 实例数: {group_status['total_instances']}")
            print(f"    - 运行中: {group_status['running_count']}")
            print(f"    - 内存: {group_status['total_memory_mb']:.2f} MB")
            
            for inst_id, inst_status in group_status['instances'].items():
                print(f"      * {inst_id}")
                print(f"        状态: {inst_status['status']}")
                print(f"        PID: {inst_status['pid']}")
                print(f"        运行时长: {inst_status['uptime']}")


def example_6_instance_operations():
    """示例6: 实例级别操作"""
    print("\n" + "=" * 50)
    print("示例6: 实例级别操作")
    print("=" * 50)
    
    manager = MultiBotManager()
    
    # 获取实例
    instance = manager.get_instance("primary_bots", "bot_001")
    
    if instance:
        print(f"实例信息: {instance}")
        
        # 查看当前状态
        print("\n当前状态:")
        print(f"  - 运行状态: {'运行中' if instance.is_running else '已停止'}")
        print(f"  - 状态: {instance.status}")
        print(f"  - PID: {instance.pid}")
        
        # 模拟启动（仅更新状态）
        print("\n启动实例...")
        process_info = {
            "pid": 12345,
            "command": "python run.py",
            "cwd": "D:\\Bots\\bot_001",
            "title": "MaiBot-001"
        }
        instance.start(process_info)
        
        print("  ✓ 已启动")
        print(f"    - 运行时长: {instance.get_uptime()}")
        
        # 更新资源占用
        print("\n更新资源占用...")
        instance.update_resource_usage(cpu_percent=15.5, memory_mb=256.8)
        print("  ✓ 已更新")
        print(f"    - CPU: {instance.resource_usage['cpu_percent']:.1f}%")
        print(f"    - 内存: {instance.resource_usage['memory_mb']:.1f} MB")
        
        # 暂停实例
        print("\n暂停实例...")
        instance.pause()
        print(f"  ✓ 已暂停，状态: {instance.status}")
        
        # 恢复实例
        print("\n恢复实例...")
        instance.resume()
        print(f"  ✓ 已恢复，状态: {instance.status}")
        
        # 设置错误
        print("\n设置错误状态...")
        instance.set_error("模拟错误信息")
        print(f"  ✓ 已设置错误，状态: {instance.status}")
        print(f"    - 错误信息: {instance.error_message}")
        
        # 转换为字典
        print("\n实例数据:")
        import json
        print(json.dumps(instance.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("❌ 实例不存在")


def main():
    """多Bot管理系统主函数"""
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 10 + "多Bot管理系统 - 使用示例" + " " * 14 + "║")
    print("╚" + "=" * 48 + "╝")
    
    try:
        example_1_basic_management()
        example_2_startup_management()
        example_3_event_callbacks()
        example_4_import_export()
        example_5_status_monitoring()
        example_6_instance_operations()
        
        print("\n" + "=" * 50)
        print("✓ 所有示例执行完成")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"\n❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
