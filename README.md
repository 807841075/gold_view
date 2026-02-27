# GoldView — 黄金行情看板
简洁的 Windows 托盘 + 窗口应用，实时显示上金所 AU9999 与国际 COMEX 黄金价格，并提供多周期 K 线图查看。基于 PyQt6 与 pyqtgraph，支持一键打包为单文件可执行程序。

## 功能特性
- 实时行情刷新（默认每 10 秒一次）
- 国内 AU9999 与国际黄金价格同步展示，红涨绿跌配色
- 多周期 K 线图（5 分钟、日线、周线）
- 托盘常驻、菜单快捷操作（手动刷新 / 开机自启动 / 退出）
- 自定义应用图标，任务栏图标一致显示
- 单文件打包，双击即用
## 数据来源
- 国内金价（AU9999）：新浪财经
  - 接口示例： http://hq.sinajs.cn/list=SGE_AU9999
- 国际金价（COMEX GC）：东方财富
  - 实时： http://push2.eastmoney.com/api/qt/stock/get?secid=101.GC00Y&fields=...
  - 历史 K 线： http://push2his.eastmoney.com/api/qt/stock/kline/get?secid=118.AU9999&klt={klt}&lmt={lmt}
- 说明：程序使用 curl_cffi 优化 TLS 指纹，提升接口可用性
## 运行环境
- 操作系统：Windows 10/11
- Python：3.12（开发调试时）
- 主要依赖：PyQt6、pyqtgraph、numpy、curl_cffi、Pillow
## 快速开始（开发）
1. 安装依赖（示例）
   
   ```
   pip install PyQt6 pyqtgraph 
   numpy curl_cffi Pillow
   ```
2. 启动程序
   
   ```
   python main.py
   ```
## 打包发布（Windows 单文件）
- 方法一：使用脚本
  
  ```
  python run_build.py
  ```
- 方法二：使用 spec
  
  ```
  pyinstaller --clean GoldView.spec
  ```
- 打包产物： dist/GoldView.exe
说明：

- 已将 app_icon.png （桌面图标源文件）和 app_icon.ico （多尺寸 ICO）集成到打包流程中；
- 程序运行时优先从打包目录读取 app_icon.png ，确保托盘、窗口、任务栏图标一致。
## 图标与任务栏说明
- 图标文件：
  - 源图标： app_icon.png
  - 生成 ICO：运行 python generate_icon.py 自动生成 app_icon.ico
- 任务栏图标：
  - 通过设置 Windows AppUserModelID，确保任务栏显示为自定义图标（已在程序入口初始化）
## 常见问题
- 任务栏仍显示默认图标
  - 关闭所有运行中的实例后重新启动；
  - 确认 app_icon.png 与 app_icon.ico 均存在且未被占用；
  - 重新执行打包命令生成新的 GoldView.exe 。
- 网络请求失败或无数据
  - 检查网络环境；程序使用 http 接口减少证书问题；
  - 稍候重试或切换网络。
## 项目结构（简要）
- main.py ：应用入口、UI 与数据刷新逻辑
- generate_icon.py ：PNG 转多尺寸 ICO
- GoldView.spec ：PyInstaller 打包配置
- run_build.py ：一键打包脚本
- app_icon.png / app_icon.ico ：应用图标资源
- dist/GoldView.exe ：打包产物
如需我直接写入 README.md 文件或添加英文版/截图说明，告诉我即可。
