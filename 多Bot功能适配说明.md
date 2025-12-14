# 多Bot功能适配说明

## 概述
本次更新为MaiCore-Start项目添加了完整的多Bot管理功能支持，并对现有的统计系统进行了适配。

## 更新时间
2025-12-14

## 主要更新内容

### 1. HTML统计页面多Bot支持 (`maibot_statistics.html`)

#### 新增功能：
- **实例选择器**：在页面顶部工具栏添加了Bot实例下拉选择器
- **动态数据加载**：支持通过API动态切换和加载不同Bot实例的统计数据
- **实时更新**：统计时间动态更新，支持多实例数据查看

#### 技术实现：
```javascript
// 主要新增的JavaScript函数：
- loadInstanceList()           // 从API加载所有Bot实例列表
- updateInstanceSelector()     // 更新实例选择器UI
- switchInstance(instanceName) // 切换当前查看的实例
- loadInstanceData(instanceName) // 加载指定实例的统计数据
- updateStatsDisplay(data)     // 更新页面显示的数据
```

#### API端点依赖：
- `GET /api/instances` - 获取所有Bot实例列表
- `GET /api/statistics/{instance_name}` - 获取指定实例的统计数据

---

### 2. 实例统计管理器增强 (`src/modules/instance_statistics.py`)

#### 新增方法：

##### `get_all_instances_data()` 
- **功能**：获取所有实例的统计数据聚合
- **返回值**：包含所有实例信息的字典
- **用途**：为统计页面提供实例列表

##### `aggregate_statistics(instance_names=None)`
- **功能**：聚合多个实例的统计数据
- **参数**：
  - `instance_names`: 可选，指定要聚合的实例名称列表
  - 不指定时聚合所有实例
- **返回值**：聚合统计数据，包含：
  - `total_instances`: 实例总数
  - `instances`: 各实例的详细信息
  - `aggregated_stats`: 聚合统计（在线时间、消息数、花费等）

#### 配置读取：
- 从 `config/config.toml` 读取实例配置
- 跳过 `global` 和 `default` 配置段
- 验证实例路径和统计文件存在性

---

### 3. WebUI后端API增强 (`webui/backend/api/statistics.py`)

#### 新增API端点：

##### `GET /api/instances`
```python
返回格式：
{
  "instances": {
    "instance1": {
      "display_name": "麦麦实例1",
      "bot_type": "MaiBot",
      "path": "/path/to/instance",
      "qq_account": "123456789"
    },
    ...
  }
}
```

##### `GET /api/statistics/summary`
```python
返回格式：
{
  "total_instances": 3,
  "instances": {
    "instance1": {
      "status": "available",
      "data": { ... }
    },
    "instance2": {
      "status": "unavailable",
      "error": "统计文件不存在"
    }
  },
  "aggregated_stats": {
    "total_cost": 0.0,
    "total_tokens": 0,
    "total_messages": 0,
    "total_requests": 0
  }
}
```

#### 新增辅助函数：

##### `get_all_instances()`
- 从配置文件读取所有可用实例
- 验证实例路径有效性
- 返回实例信息字典

---

### 4. 主菜单集成 (`src/ui/menus.py`)

#### 菜单更新：
```
====>>多Bot管理<<====
 [G] 🚀 多Bot管理系统
 [H] 📊 本地Bot检测与接管
 [I] ⚙ Bot端口管理

====>>进程管理<<====
 [J] 📊 查看运行状态

====>>杂项类<<====
 [K] ⚙ 杂项（关于/程序设置）
```

#### 原有选项字母调整：
- `G`: 查看运行状态 → `J`
- `H`: 杂项 → `K`

---

### 5. 主程序集成 (`main_refactored.py`)

#### 新增处理方法：

##### `handle_multi_bot_menu()`
```python
功能：进入多Bot管理系统主菜单
实现：调用 src.multi_bot.examples.main()
异常处理：捕获导入错误和运行时错误
```

##### `handle_local_bot_detection()`
```python
功能：启动本地Bot检测与接管系统
实现：创建 LocalBotTakeoverUI 实例并显示菜单
用途：检测本地运行的Bot进程并接管到管理系统
```

##### `handle_port_management()`
```python
功能：启动Bot端口管理系统
实现：创建 PortManagerUI 实例并显示菜单
用途：管理Bot实例的端口分配和冲突检测
```

#### 菜单选择映射更新：
```python
# 新增的选项映射
"G" -> handle_multi_bot_menu()
"H" -> handle_local_bot_detection()
"I" -> handle_port_management()

# 调整的选项映射
"J" -> handle_process_status()    # 原 "G"
"K" -> handle_misc_menu()          # 原 "H"
```

---

## 代码质量验证

所有修改的文件已通过 Ruff 代码质量检查：
```bash
python -m ruff check src/modules/instance_statistics.py webui/backend/api/statistics.py src/ui/menus.py
# 结果：All checks passed!
```

---

## 使用说明

### 1. 查看多Bot统计
1. 启动WebUI后端服务
2. 在浏览器中打开统计页面
3. 使用顶部的实例选择器切换不同Bot实例的数据

### 2. 多Bot管理
1. 在主菜单选择 `[G] 多Bot管理系统`
2. 进入多Bot管理菜单，可以：
   - 创建/删除Bot组
   - 创建/删除Bot实例
   - 启动/停止Bot实例
   - 查看Bot运行状态

### 3. 本地Bot检测
1. 在主菜单选择 `[H] 本地Bot检测与接管`
2. 系统会扫描本地运行的Bot进程
3. 可以将检测到的Bot接管到管理系统中

### 4. 端口管理
1. 在主菜单选择 `[I] Bot端口管理`
2. 可以进行：
   - 为新实例分配端口
   - 查看端口分配状态
   - 检查端口冲突
   - 释放不用的端口

---

## 架构说明

### 数据流向
```
┌─────────────┐
│   用户界面   │
│  (浏览器)   │
└──────┬──────┘
       │
       │ HTTP Request
       ▼
┌─────────────────┐
│  WebUI Backend  │
│   (FastAPI)     │
└──────┬──────────┘
       │
       │ 读取配置/HTML
       ▼
┌──────────────────┐
│  Instance Stats  │
│    Manager       │
└──────┬───────────┘
       │
       │ 聚合数据
       ▼
┌──────────────────┐
│   Multi-Bot      │
│    Manager       │
└──────────────────┘
```

### 配置文件依赖
- `config/config.toml` - 主配置文件，存储所有实例信息
- `config/multi_bot_config.json` - 多Bot管理配置
- `{instance_path}/maibot_statistics.html` - 各实例的统计页面
- `{instance_path}/.env` - 实例环境配置（端口等）

---

## 注意事项

1. **向后兼容**：所有新增功能都不会破坏现有功能
2. **配置位置**：确保 `config/config.toml` 中正确配置了实例路径
3. **端口冲突**：使用端口管理功能时，系统会自动检测并避免冲突
4. **统计文件**：只有生成了 `maibot_statistics.html` 的实例才能在统计页面中查看

---

## 相关文件清单

### 修改的文件：
1. `maibot_statistics.html` - 添加实例选择器和动态加载功能
2. `src/modules/instance_statistics.py` - 添加数据聚合方法
3. `webui/backend/api/statistics.py` - 添加多实例API端点
4. `src/ui/menus.py` - 更新主菜单显示
5. `main_refactored.py` - 添加新功能处理方法

### 依赖的新模块：
1. `src/multi_bot/` - 多Bot管理核心模块（已存在）
2. `src/multi_bot/local_bot_takeover_ui.py` - 本地Bot检测UI
3. `src/multi_bot/port_manager_ui.py` - 端口管理UI
4. `src/multi_bot/examples.py` - 多Bot管理示例和主菜单

---

## 下一步计划

可选的增强功能：
1. 添加实例之间的统计数据对比功能
2. 实现实例组的批量统计分析
3. 添加统计数据导出功能（CSV/Excel）
4. 增加实时统计数据推送（WebSocket）
5. 添加统计数据可视化图表聚合

---

## 联系方式

如有问题或建议，请通过项目仓库提交 Issue。
