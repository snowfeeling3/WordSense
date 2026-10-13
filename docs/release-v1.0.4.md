# WordSense v1.0.4

日期：2026-10-12（Asia/Shanghai）。

新增独立的“设置词库位置…”、“打开词库目录”和“清理旧词库残留”。之前仅支持文章目录迁移，词库保留默认位置；本版可以迁移整个统一词库并保留文章设置。

使用 SQLite backup 接口包含 WAL 中的数据，校验数据库完整性和完整数据，再保存新路径、切换连接并清理旧数据库。不会覆盖目标目录已存在的词库。配置写入失败时返回原库；配置中的库丢失时提示恢复，不自动创建空替代库。固定用户目录保留 settings.json 记录实际路径。

所有日期继续共用一个词库。迁移后请运行本版或更新版本，关闭不识别路径配置的旧版。备份包含固定配置目录、实际词库目录和实际文章目录。

本次同版本外观更新：只保留完全理解（绿）、有点模糊（蓝）、完全不懂（红）；未登记和输入中改为黄色。旧 level=1 迁移为 level=2，词条、词义、ID 和时间戳保留。

采用官方 Everforest Dark Soft 的柔和背景，取消亮绿实心按钮和纯白正文，使用暗色按钮、暖米色 UI 文字与柔和选区。主题代码在 wordsense/theme.py，上游配色来源：https://github.com/sainnhe/everforest/blob/master/autoload/everforest.vim。

48 项自动化测试通过，打包程序及从 ZIP 解压后的程序验证三种理解程度、黄色未登记词、统一词库迁移、旧库清理、文章目录设置保留与重启恢复。原主题包保存在 dist/archive/WordSense-v1.0.4-before-theme-Windows-x64.zip。

分发 ZIP：dist/WordSense-v1.0.4-Windows-x64.zip。
SHA-256：`ca6495f68e4abcca47bb1ef159f25228bddda6a083779f7cee51fc2cfa7764d0`。
