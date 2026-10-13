# WordSense v1.0.3 · 首个正式分发版

日期：2026-10-12（Asia/Shanghai）。之前的 v1.0.0–v1.0.2 是项目内迭代包，本版本加入应用品牌及分发材料。

下载文件：`dist/WordSense-v1.0.3-Windows-x64.zip`。Windows x64 免安装版，解压完整文件夹后双击 WordSense.exe；无需 Python，保留 _internal 文件夹。可以直接分享 ZIP，包内不包含用户文档和词库。

Logo：展开书页形成 W，沿用 Everforest 配色，透明圆角外缘。PNG 原图在 assets/wordsense-logo.png，16–256 像素的七尺寸 Windows ICO 在 assets/wordsense.ico，生成提示词及工具记录在 assets/logo-design.md。已接入 EXE 资源、窗口、任务栏和标题区域。

保留全部功能：英文增量标记、统一词库、侧边栏检索、回车填写保存、Ctrl+L、每日 Markdown、圆形文章菜单、自定义文章目录和旧文件清理。

包内附使用说明、THIRD_PARTY_NOTICES.txt 和 licenses 文件夹。第三方原始库未修改，使用独立运行库加载。发布包校验文件：`WordSense-v1.0.3-Windows-x64.zip.sha256`。

SHA-256：`08061472e90526a168cafdcf4fd9f5d017952d12d7d70602dd98f9aff0f2f97a`。

41 项自动化测试通过；打包及解压后的程序在原生 Windows 平台验证窗口、图标、统一词库、日文档、目录迁移清理及重启恢复。没有创建互联网下载地址，ZIP 可作为上传网盘或其他分发渠道的文件。
