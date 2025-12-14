# 25.10.11

- [X]  退出时对程序所管辖的进程执行什么动作（询问，一律关闭，一律保留）
- [ ]  可视化设置程序
- [X]  组件下载
- [X]  部署模块拆分
- [ ]  所管辖的机器人数据统计
- [X]  日志系统完善

# 25.11.24

- [ ]  模组化自定义部署

# 25.11.29

- [X]  每日一言

# 25.12.12

- [X]  系统通知
- [X]  托盘


为我设计实例多开功能，当用户启动完一次实例后，将原本的运行实例选项字样改为实例多开选项。多开选项逻辑如下：
在实例根目录下有一个名为.env的环境变量配置文件，

```env
# 麦麦主程序配置
HOST=127.0.0.1
PORT=8000

# WebUI 独立服务器配置
WEBUI_ENABLED=true
WEBUI_MODE=production   # 模式: development(开发) 或 production(生产)
WEBUI_HOST=0.0.0.0      # WebUI 服务器监听地址
WEBUI_PORT=8001         # WebUI 服务器端口
```

当实例类型为MaiBot时，其中的PORT字段存储的是实例主程序与适配器的通信端口，WEBUI_PORT字段存储的是主程序与webui服务器的通信端口，他们两个不能相同，在适配器的根目录下则有一个config.toml文件，这里我列出重要的配置内容，不代表该文件不存在其他配置内容，所以不要直接覆盖配置文件

```toml

[napcat_server] # Napcat连接的ws服务设置
host = "localhost"      # Napcat设定的主机地址
port = 8095             # Napcat设定的端口 
token = ""              # Napcat设定的访问令牌，若无则留空
heartbeat_interval = 30 # 与Napcat设置的心跳相同（按秒计）

[maibot_server] # 连接麦麦的ws服务设置
host = "localhost" # 麦麦在.env文件中设置的主机地址，即HOST字段
port = 8000        # 麦麦在.env文件中设置的端口，即PORT字段
```
你需要更改的是Napcat设定的端口——它不能和第一个启动的实例相同，和麦麦在.env文件中设置的端口，即PORT字段，你需要让它于实例根目录下的.env文件中的PORT字段保持一致。
。

当实例类型为MoFox_bot时，.env文件同样位于实例根目录下

```env
HOST=127.0.0.1
PORT=8000
EULA_CONFIRMED=false
```
你同样需要更改PORT字段使其与先前启动的实例不同，MoFox_bot的适配器配置文件位于根目录下的<根目录>\config\plugins\napcat_adapter\config.toml

```toml



当实例启动时，你可以通过配置集@/config/config.toml @/src/core/config.py 的mofox_path或mai_path获得实例主程序根目录的位置。
当多个实例启动时@/src/modules/launcher.py ，他们的所有端口都不能相同（除了特殊的适配器与主程序链接的端口，它要相同），多开就意味着你需要更改端口后再启动