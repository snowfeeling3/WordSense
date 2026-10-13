# WordSense v1.0.1

更新日期：2026-10-12（Asia/Shanghai）。

- 词典列表只显示英文单词和中文词义，取消理解程度文字后缀，保留程度颜色。
- Ctrl+L 从正文跳到单词输入框，选中原有内容方便替换。
- 单词框 Enter 跳到中文词义框；词义框 Enter 保存并返回正文。
- 保存按钮同样返回正文，保留正文光标与选区；保存失败保留输入。
- 继续使用原有统一词库和每日 Markdown，不创建新的数据目录。

发布包：`dist/WordSense-v1.0.1-Windows-x64.zip`。解压完整文件夹后启动 WordSense.exe；项目根目录 WordSense.cmd 已指向本版本。旧 v1.0.0 发布包保留。

SHA-256：`ce9d5022b890557f193a497114f576294d78360884fd8212936ea381e368f9fa`。

34 项自动化测试全部通过；实际打包 EXE 的原生窗口、回车填写保存、词典显示、统一词库、日期文档和重启恢复验收通过。从 ZIP 解压到独立中文/空格目录、从 PATH 移除 Python/Conda 后的验证也通过。报告见 packaged-smoke.json、extracted-smoke.json。
