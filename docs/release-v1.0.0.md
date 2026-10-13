# WordSense v1.0.0

发布日期：2026-10-12（Asia/Shanghai）。Windows x64 免安装版，包含 Python/Qt 运行库，无需额外安装 Python。

- 发布 ZIP：`dist/WordSense-v1.0.0-Windows-x64.zip`，49,261,784 字节（约 47 MiB）。
- 解压后启动：`WordSense-v1.0.0/WordSense.exe`，保留 `_internal` 文件夹。
- SHA-256：`fb5736367bce243fcba9310efb0bf5b22cb2e9b5101a93faf7d3338ff54656e1`。
- 校验文件：`dist/WordSense-v1.0.0-Windows-x64.zip.sha256`。

每日文档按日期自动保存为 UTF-8 Markdown，支持手动保存、另存为和日期切换。所有日期与源码/打包版本共用 `%LOCALAPPDATA%\WordSense\wordsense.sqlite3` 中的同一个词库；日文档只保存正文，不嵌入词库和颜色。已有词库直接沿用，旧稿首次启动迁移。

保留已有实时增量着色、白色未记录词、四级理解颜色、侧边栏词义检索、原生编辑和撤销重做功能。发布包不携带个人文档和词库。

验收：30 项自动化测试通过；实际运行打包 EXE 和从 ZIP 解压后的 EXE，均通过跨日期 Markdown、统一词库、固定数据位置和重启恢复验证。解压后测试清除了 Python/Conda 环境路径，使用中文/空格目录及不同工作目录。原始报告见 `packaged-smoke.json`、`extracted-smoke.json`。

已知限制：当前为未签名的免安装版，没有安装器；Markdown 不保存编辑器颜色，历史文档按当前共享词库重新着色；撤销栈不跨文档/重启保存；强制结束进程可能丢失最后尚未自动保存的输入；极长单段落高亮成本随段落长度增长。外部程序同时编辑同一天的 Markdown 或多个 WordSense 实例同时写作可能互相覆盖，建议保持单个写作实例。
