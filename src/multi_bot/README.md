"""
多Bot管理使用说明文档

本模块提供了完整的多Bot实例管理功能，支持同时运行和管理多个机器人实例。

## 核心概念

### 1. Bot实例 (BotInstance)
- 代表一个独立的机器人实例
- 包含配置信息、运行状态、进程信息等
- 提供启动、停止、暂停、恢复等操作

### 2. Bot组 (BotGroup)
- 管理一组相关的Bot实例
- 支持批量启动、停止等操作
- 支持组级别的配置和限制

### 3. 多Bot管理器 (MultiBotManager)
- 核心管理器，负责全局的Bot实例和组的管理
- 支持配置的持久化存储
- 支持事件回调机制

### 4. 本地Bot检测与接管 (LocalBotDetector & LocalBotTakeover)
- 自动检测系统中运行的本地Bot进程
- 将现有的运行中的Bot接管到多Bot管理系统
- 支持单个或批量接管
- 实时监控已接管的实例

### 5. Bot端口管理 (PortAllocator & BotPortManager)
- 自动分配可用的端口给Bot实例
- 避免端口冲突
- 自动配置Bot的.env文件
- 支持首选端口指定
- 实时监控端口占用情况

## 快速开始

### 基本使用流程

```python
from src.multi_bot import MultiBotManager, BotInstance, BotGroup

# 1. 获取全局管理器
manager = MultiBotManager()

# 2. 创建Bot组
group = manager.create_group("my_bots", {
    "launch_interval": 2,  # 启动间隔（秒）
    "max_instances": 10     # 最大实例数
})

# 3. 创建Bot实例
config = {
    "bot_path": "/path/to/maibot",
    "adapter_path": "/path/to/adapter",
    "napcat_path": "/path/to/napcat",
    "qq_account": "123456789"
}

instance = manager.create_instance("my_bots", "bot_001", config)

# 4. 启动实例（需要与启动器集成）
# 通过 MultiBotLauncher 进行启动
```

### 本地Bot检测与接管

```python
from src.multi_bot import LocalBotDetector, LocalBotTakeover, multi_bot_manager

# 1. 检测本地运行的Bot
detector = LocalBotDetector()
detected_bots = detector.detect_all_bots()

# 2. 创建接管管理器
takeover = LocalBotTakeover(multi_bot_manager)

# 3. 接管单个Bot
takeover.create_takeover_instance(
    process_key="MaiBot_12345",
    group_name="local_bots",
    instance_id="bot_001"
)

# 4. 批量接管
results = takeover.batch_takeover(
    process_keys=list(detected_bots.keys()),
    group_name="local_bots"
)

# 5. 监控已接管的实例
monitoring = takeover.monitor_takeover_instances()

# 5. 监控已接管的实例
monitoring = takeover.monitor_takeover_instances()

# 6. 查看接管统计
summary = takeover.get_takeover_summary()
```

### Bot端口管理

```python
from src.multi_bot import BotPortManager, multi_bot_manager

# 1. 创建端口管理器
port_manager = BotPortManager(multi_bot_manager)

# 2. 为实例分配端口
port = port_manager.allocate_port_for_instance(
    group_name="my_bots",
    instance_id="bot_001",
    preferred_port=8000  # 可选
)

# 3. 获取实例端口
instance_port = port_manager.get_instance_port("my_bots", "bot_001")

# 4. 配置.env文件
port_manager.setup_env_file(
    bot_cwd="/path/to/bot",
    port=port,
    additional_vars={"LOG_LEVEL": "INFO"}
)

# 5. 查看端口分配状态
status = port_manager.get_global_port_status()

# 6. 查看组内端口信息
group_ports = port_manager.get_port_info("my_bots")

# 7. 检查端口冲突
conflicts = status['conflicts']

# 8. 释放组内所有端口
results = port_manager.release_group_ports("my_bots")
```

# 6. 保存配置
manager.save_config()
```

### 与现有启动器集成

```python
from src.multi_bot import MultiBotLauncher

# 获取进程管理器实例（从启动器中获取）
launcher = MultiBotLauncher(process_manager)

# 启动单个实例
success, pid = launcher.launch_instance(
    group_name="my_bots",
    instance_id="bot_001",
    command="python run.py",
    cwd="/path/to/bot",
    title="MaiBot-001"
)

# 启动整个组
launch_config = {
    "bot_001": {
        "command": "python run.py",
        "cwd": "/path/to/bot_001",
        "title": "MaiBot-001"
    },
    "bot_002": {
        "command": "python run.py",
        "cwd": "/path/to/bot_002",
        "title": "MaiBot-002"
    }
}

results = launcher.launch_group("my_bots", launch_config)
```

## 配置文件格式

多Bot配置保存在 `config/multi_bot_config.json`，格式如下：

```json
{
  "version": "1.0",
  "created_at": "2025-01-01T12:00:00",
  "groups": {
    "group_name": {
      "group_name": "group_name",
      "group_config": {
        "launch_interval": 2,
        "max_instances": 10
      },
      "instances": {
        "instance_id": {
          "instance_id": "instance_id",
          "config": {
            "bot_path": "...",
            "qq_account": "..."
          },
          "is_running": false,
          "status": "stopped",
          "pid": null,
          "uptime": null,
          "error_message": null,
          "resource_usage": {},
          "last_update": null
        }
      },
      "status": {
        ...
      }
    }
  }
}
```

## 事件回调

多Bot管理器支持以下事件回调：

- `on_start`: 实例启动时触发
- `on_stop`: 实例停止时触发
- `on_error`: 实例发生错误时触发

```python
def on_bot_start(group_name, instance_id, pid):
    print(f"Bot {instance_id} 已启动，PID: {pid}")

manager.register_callback("on_start", on_bot_start)
```

## API 参考

### MultiBotManager

#### 组管理
- `create_group(group_name, group_config)` - 创建组
- `delete_group(group_name)` - 删除组
- `get_group(group_name)` - 获取组
- `get_all_groups()` - 获取所有组

#### 实例管理
- `create_instance(group_name, instance_id, config)` - 创建实例
- `delete_instance(group_name, instance_id)` - 删除实例
- `get_instance(group_name, instance_id)` - 获取实例
- `get_all_instances()` - 获取所有实例

#### 持久化
- `save_config()` - 保存配置
- `export_config(filepath)` - 导出配置
- `import_config(filepath)` - 导入配置

#### 状态查询
- `get_global_status()` - 获取全局状态

### BotInstance

- `start(process_info)` - 启动实例
- `stop()` - 停止实例
- `pause()` - 暂停实例
- `resume()` - 恢复实例
- `set_error(error_message)` - 设置错误状态
- `update_resource_usage(cpu_percent, memory_mb)` - 更新资源占用
- `get_uptime()` - 获取运行时长
- `to_dict()` - 转换为字典

### BotGroup

- `add_instance(instance)` - 添加实例
- `remove_instance(instance_id)` - 移除实例
- `get_instance(instance_id)` - 获取实例
- `get_all_instances()` - 获取所有实例
- `get_running_instances()` - 获取运行中的实例
- `get_stopped_instances()` - 获取已停止的实例
- `get_group_status()` - 获取组状态
- `start_all(callback)` - 启动所有实例
- `stop_all(callback)` - 停止所有实例

### MultiBotLauncher

- `launch_instance(group_name, instance_id, command, cwd, title)` - 启动单个实例
- `launch_group(group_name, launch_config)` - 启动整个组
- `stop_instance(group_name, instance_id)` - 停止单个实例
- `stop_group(group_name)` - 停止整个组
- `restart_instance(group_name, instance_id, command, cwd, title)` - 重启单个实例
- `get_group_status(group_name)` - 获取组状态
- `get_global_status()` - 获取全局状态

### LocalBotDetector

- `detect_all_bots()` - 检测所有运行中的机器人进程
- `detect_bots_by_type(bot_type)` - 按类型检测Bot（MaiBot/MoFox_bot/NapCat）
- `get_detected_process(process_key)` - 获取单个进程信息
- `get_all_detected()` - 获取所有检测到的进程

### LocalBotTakeover

- `detect_and_analyze()` - 检测并分析本地运行的Bot
- `create_takeover_instance(process_key, group_name, instance_id, config_override)` - 接管单个Bot
- `batch_takeover(process_keys, group_name, instance_prefix)` - 批量接管Bot
- `monitor_takeover_instances()` - 监控已接管的实例
- `get_takeover_summary()` - 获取接管统计信息

### LocalBotTakeoverUI

- `show_detection_menu()` - 显示检测菜单
- `handle_detect_all()` - 检测所有Bot
- `handle_detect_by_type()` - 按类型检测
- `handle_takeover()` - 接管Bot
- `handle_monitor()` - 监控实例
- `handle_show_summary()` - 显示统计

### PortAllocator

- `is_port_available(port)` - 检查端口是否可用
- `allocate_port(instance_id, preferred_port)` - 分配端口
- `release_port(instance_id)` - 释放端口
- `get_port(instance_id)` - 获取已分配的端口
- `get_all_ports()` - 获取所有端口映射
- `get_next_available_port()` - 获取下一个可用端口
- `find_conflicting_ports()` - 查找冲突的端口

### BotPortManager

- `allocate_port_for_instance(group_name, instance_id, preferred_port)` - 为实例分配端口
- `get_instance_port(group_name, instance_id)` - 获取实例端口
- `setup_env_file(bot_cwd, port, additional_vars)` - 配置.env文件
- `get_port_info(group_name)` - 获取组内端口信息
- `get_global_port_status()` - 获取全局端口状态
- `release_group_ports(group_name)` - 释放组内所有端口

### PortManagerUI

- `show_port_menu()` - 显示端口管理菜单
- `handle_allocate_port()` - 分配端口
- `handle_show_status()` - 显示分配状态
- `handle_show_group_info()` - 显示组内端口信息
- `handle_check_conflicts()` - 检查冲突
- `handle_release_ports()` - 释放端口

## 注意事项

1. **线程安全** - 当前实现不是线程安全的，如需在多线程环境中使用，需要添加锁机制
2. **资源监控** - 需要定期调用 `update_resource_usage()` 来更新实例的CPU和内存占用
3. **进程管理** - 进程管理与系统底层进程关联，需要正确处理进程生命周期
4. **配置持久化** - 配置保存为JSON格式，在导入前需要验证格式的正确性

## 扩展建议

1. 添加数据库持久化（代替JSON文件）
2. 实现Web管理界面
3. 添加定期检查实例状态的守护进程
4. 实现自动重启失败的实例
5. 添加性能监控和告警功能
6. 实现配置版本控制和回滚功能
"""

# 导出主要类
from .multi_bot_manager import MultiBotManager, multi_bot_manager
from .multi_bot_launcher import MultiBotLauncher
from .bot_instance import BotInstance
from .bot_group import BotGroup

__all__ = [
    "MultiBotManager",
    "multi_bot_manager",
    "MultiBotLauncher",
    "BotInstance",
    "BotGroup"
]
