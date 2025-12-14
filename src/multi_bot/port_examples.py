"""
Bot端口管理使用示例

演示如何使用端口管理系统为多个Bot实例自动分配端口
"""

from src.multi_bot import (
    MultiBotManager,
    BotPortManager,
    PortAllocator
)


def example_1_basic_port_allocation():
    """示例1: 基本的端口分配"""
    print("=" * 50)
    print("示例1: 基本的端口分配")
    print("=" * 50)
    
    # 创建管理器和端口管理器
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    # 创建Bot组和实例
    manager.create_group("my_bots", {
        "launch_interval": 2,
        "max_instances": 5
    })
    
    print("✓ 创建Bot组")
    
    # 为多个实例分配端口
    for i in range(3):
        instance_id = f"bot_{i+1:03d}"
        config = {
            "bot_path": f"D:\\Bots\\bot_{i+1}",
            "qq_account": f"1234567890{i}"
        }
        
        manager.create_instance("my_bots", instance_id, config)
        port = port_manager.allocate_port_for_instance("my_bots", instance_id)
        
        print(f"  ✓ {instance_id}: 分配端口 {port}")
    
    # 保存配置
    manager.save_config()
    print("✓ 配置已保存")


def example_2_preferred_port():
    """示例2: 指定首选端口"""
    print("\n" + "=" * 50)
    print("示例2: 指定首选端口")
    print("=" * 50)
    
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    manager.create_group("special_bots")
    
    # 为特定实例指定首选端口
    preferred_ports = {
        "api_bot": 8000,
        "event_bot": 8001,
        "manager_bot": 8002
    }
    
    for instance_id, preferred_port in preferred_ports.items():
        config = {"bot_path": f"D:\\Bots\\{instance_id}"}
        manager.create_instance("special_bots", instance_id, config)
        
        port = port_manager.allocate_port_for_instance(
            "special_bots",
            instance_id,
            preferred_port=preferred_port
        )
        
        print(f"  {instance_id}: 分配端口 {port}")
    
    manager.save_config()


def example_3_port_status():
    """示例3: 查看端口分配状态"""
    print("\n" + "=" * 50)
    print("示例3: 查看端口分配状态")
    print("=" * 50)
    
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    # 获取全局端口状态
    status = port_manager.get_global_port_status()
    
    print("\n全局端口分配状态:")
    print(f"  端口范围: {status['port_range']}")
    print(f"  已分配端口数: {len(status['allocated_ports'])}")
    print(f"  可用端口数: {status['available_ports']}")
    print(f"  下一个可用端口: {status['next_available']}")
    
    if status['allocated_ports']:
        print("\n已分配的端口:")
        for instance_id, port in sorted(status['allocated_ports'].items()):
            print(f"    {instance_id}: {port}")
    
    if status['conflicts']:
        print("\n⚠ 端口冲突:")
        for port, instances in status['conflicts'].items():
            print(f"  端口 {port}:")
            for instance_id in instances:
                print(f"    - {instance_id}")


def example_4_env_file_setup():
    """示例4: 配置.env文件"""
    print("\n" + "=" * 50)
    print("示例4: 配置.env文件")
    print("=" * 50)
    
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    # 为Bot配置.env文件
    bot_path = "D:\\Bots\\test_bot"
    port = 8000
    
    print(f"为 {bot_path} 配置 .env 文件...")
    
    success = port_manager.setup_env_file(
        bot_path,
        port,
        additional_vars={
            "LOG_LEVEL": "INFO",
            "DEBUG": "false"
        }
    )
    
    if success:
        print(f"✓ .env 配置成功 (PORT={port})")
    else:
        print("✗ .env 配置失败")


def example_5_group_port_info():
    """示例5: 查看组内端口信息"""
    print("\n" + "=" * 50)
    print("示例5: 查看组内端口信息")
    print("=" * 50)
    
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    # 创建组和实例
    manager.create_group("test_group")
    
    for i in range(2):
        instance_id = f"bot_{i+1}"
        config = {"bot_path": f"D:\\Bots\\{instance_id}"}
        manager.create_instance("test_group", instance_id, config)
        port_manager.allocate_port_for_instance("test_group", instance_id)
    
    # 获取组内端口信息
    info = port_manager.get_port_info("test_group")
    
    print("\n组 'test_group' 的端口信息:")
    for instance_id, port_info in info.items():
        port = port_info['port']
        is_running = port_info['is_running']
        
        status_text = "运行中" if is_running else "已停止"
        port_text = str(port) if port else "未分配"
        
        print(f"  {instance_id}")
        print(f"    端口: {port_text}")
        print(f"    状态: {status_text}")


def example_6_port_conflict_check():
    """示例6: 检查端口冲突"""
    print("\n" + "=" * 50)
    print("示例6: 检查端口冲突")
    print("=" * 50)
    
    # 创建端口分配器
    allocator = PortAllocator()
    
    # 手动分配一些端口（模拟冲突）
    allocator.allocate_port("bot_001", 8000)
    allocator.allocate_port("bot_002", 8001)
    allocator.allocate_port("bot_003", 8000)  # 冲突！
    
    # 查找冲突
    conflicts = allocator.find_conflicting_ports()
    
    if conflicts:
        print("✗ 检测到端口冲突:")
        for port, instances in conflicts.items():
            print(f"  端口 {port}:")
            for instance_id in instances:
                print(f"    - {instance_id}")
    else:
        print("✓ 没有端口冲突")


def example_7_release_ports():
    """示例7: 释放端口"""
    print("\n" + "=" * 50)
    print("示例7: 释放端口")
    print("=" * 50)
    
    manager = MultiBotManager()
    port_manager = BotPortManager(manager)
    
    # 创建组和实例
    manager.create_group("release_test")
    
    for i in range(2):
        instance_id = f"bot_{i+1}"
        config = {"bot_path": f"D:\\Bots\\{instance_id}"}
        manager.create_instance("release_test", instance_id, config)
        port_manager.allocate_port_for_instance("release_test", instance_id)
    
    print("✓ 已为 2 个实例分配端口")
    
    # 释放端口
    results = port_manager.release_group_ports("release_test")
    
    success_count = sum(1 for s in results.values() if s)
    print(f"✓ 已释放 {success_count} 个端口")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║" + " " * 12 + "Bot端口管理系统 - 使用示例" + " " * 12 + "║")
    print("╚" + "=" * 48 + "╝")
    
    try:
        example_1_basic_port_allocation()
        example_2_preferred_port()
        example_3_port_status()
        example_4_env_file_setup()
        example_5_group_port_info()
        example_6_port_conflict_check()
        example_7_release_ports()
        
        print("\n" + "=" * 50)
        print("✓ 所有示例执行完成")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"\n❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
