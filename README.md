# 韩国演唱会抢票系统

这是一个用于韩国演唱会抢票的自动化系统，包含Python和Go语言两个版本。

## 系统架构

### Python版本 (GUI界面)
- **位置**: `python/` 目录
- **功能**: 提供图形用户界面，支持演唱会管理、抢票监控、日志查看等
- **技术栈**: PyQt5 + Selenium + Python

### Go版本 (命令行工具)
- **位置**: `go/` 目录  
- **功能**: 高性能的命令行抢票工具，适合自动化部署
- **技术栈**: Go + ChromeDP + HTTP客户端

## 功能特性

### 共同功能
- ✅ 支持多个票务网站 (Interpark, Yes24, Melon Ticket)
- ✅ 自动登录票务网站
- ✅ 智能监控票务可用性
- ✅ 自动选择座位和购买
- ✅ 多种通知方式 (邮件、Telegram、桌面通知)
- ✅ 验证码自动识别
- ✅ 代理支持
- ✅ 详细的日志记录

### Python版本特有功能
- 🖥️ 图形用户界面
- 📊 演唱会管理界面
- 📈 实时抢票进度显示
- 🔧 可视化配置管理
- 📋 系统托盘支持

### Go版本特有功能
- ⚡ 更高的性能和并发处理
- 🚀 更快的响应速度
- 💻 命令行界面，适合服务器部署
- 🔄 更好的错误恢复机制

## 快速开始

### Python版本

1. **安装依赖**
   ```bash
   # 激活虚拟环境
   venv\Scripts\activate
   
   # 安装依赖
   pip install -r python/requirements.txt
   ```

2. **启动系统**
   ```bash
   # 使用批处理文件（推荐）
   start.bat
   
   # 或直接运行
   venv\Scripts\python.exe run.py
   
   # 调试模式
   venv\Scripts\python.exe run.py --debug
   ```

### Go版本

1. **构建程序**
   ```bash
   # 进入Go目录
   cd go
   
   # 运行构建脚本
   build.bat
   
   # 或手动构建
   go mod tidy
   go build -o ticket_grabber.exe .
   ```

2. **运行程序**
   ```bash
   # 查看帮助
   ticket_grabber.exe --help
   
   # 指定演唱会抢票
   ticket_grabber.exe --concert concert_001
   
   # 无头模式
   ticket_grabber.exe --headless --concert concert_001
   ```

## 配置说明

### 配置文件位置
- 默认配置: `config/default_config.json`
- 用户配置: `config/config.json`

### 主要配置项

```json
{
  "user": {
    "username": "你的用户名",
    "password": "你的密码"
  },
  "ticketing": {
    "default_site": "interpark",
    "refresh_interval": 0.5,
    "auto_refresh": true
  },
  "concerts": [
    {
      "id": "concert_001",
      "name": "BTS 2024世界巡回演唱会",
      "url": "https://tickets.interpark.com/event/12345",
      "max_price": 150000,
      "preferred_seats": ["VIP", "A区"]
    }
  ]
}
```

## 支持的票务网站

### Interpark (인터파크)
- 网站: https://tickets.interpark.com
- 支持功能: 登录、搜索、购票

### Yes24 (예스24)
- 网站: https://ticket.yes24.com
- 支持功能: 登录、搜索、购票

### Melon Ticket (멜론티켓)
- 网站: https://ticket.melon.com
- 支持功能: 登录、搜索、购票

## 使用建议

### 选择版本
- **新手用户**: 推荐使用Python版本，界面友好，操作简单
- **高级用户**: 推荐使用Go版本，性能更好，适合批量操作
- **服务器部署**: 推荐使用Go版本，资源占用少，稳定性高

### 性能优化
1. **网络设置**: 使用稳定的网络连接，建议配置代理
2. **刷新间隔**: 根据网站限制调整刷新间隔，避免被封IP
3. **并发控制**: Go版本支持并发抢票，但要注意不要过度并发

### 安全注意事项
1. **账号安全**: 不要在配置文件中明文存储密码，建议使用环境变量
2. **IP保护**: 使用代理轮换IP，避免被封
3. **合规使用**: 请遵守票务网站的使用条款

## 故障排除

### 常见问题

1. **Python版本启动失败**
   - 检查虚拟环境是否正确激活
   - 确认所有依赖已安装
   - 查看日志文件获取详细错误信息

2. **Go版本构建失败**
   - 确认Go语言环境已正确安装
   - 检查网络连接，确保能下载依赖
   - 查看构建日志获取错误信息

3. **抢票失败**
   - 检查账号密码是否正确
   - 确认演唱会信息是否准确
   - 查看网络连接是否稳定

### 日志文件
- Python版本: `logs/ticket_bot_*.log`
- Go版本: 控制台输出

## 开发说明

### 项目结构
```
ticks/
├── python/              # Python版本
│   ├── core/           # 核心功能
│   ├── ui/             # 用户界面
│   └── utils/          # 工具类
├── go/                 # Go版本
│   ├── pkg/            # 包文件
│   └── cmd/            # 命令行程序
├── config/             # 配置文件
├── logs/               # 日志文件
└── README.md           # 说明文档
```

### 扩展开发
- 添加新的票务网站支持
- 实现新的通知方式
- 优化抢票算法
- 添加更多自动化功能

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v1.0.0
- ✅ 完成Python版本基础功能
- ✅ 完成Go版本核心功能
- ✅ 支持多个票务网站
- ✅ 实现自动化抢票流程
