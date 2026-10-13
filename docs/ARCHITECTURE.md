# Architecture and validation / 架构与验证

[English README](../README.md) · [中文说明](../README.zh-CN.md)

## Modules / 模块

| File | English | 中文 |
| --- | --- | --- |
| `wordsense/editor.py` | Native editing, indentation, batch paste, incremental highlighting | 原生编辑、缩进、批量粘贴及增量高亮 |
| `wordsense/storage.py` | Shared SQLite database, atomic daily Markdown, migration and cleanup | 统一词库、每日 Markdown 原子保存、迁移和清理 |
| `wordsense/window.py` | Dictionary form, keyboard navigation, document menu | 词典表单、键盘流程和文章菜单 |
| `wordsense/sidebar.py` | In-memory word/meaning search and selection | 内存词条/词义搜索与选择 |
| `wordsense/theme.py` | Everforest Dark Soft palette and three level labels | Everforest Dark Soft 配色和三种程度标签 |
| `wordsense/branding.py` | Shared application icon path | 统一应用图标路径 |
| `wordsense/smoke.py` | Temporary-data validation of the packaged runtime | 使用临时数据验证打包运行环境 |

## Editing and coloring / 编辑与颜色

Tokens contain only `[A-Za-z]+`. Lookup keys use `casefold()`, while the document retains its original spelling. An actively edited token stays yellow until a delimiter completes it. Unknown tokens also remain yellow; recorded levels use green, blue or red. QSyntaxHighlighter applies display formats without replacing text, HTML or undo history. Normal edits reprocess affected Qt text blocks, not the entire article. Python code-point offsets are converted to Qt UTF-16 positions when a block contains supplementary characters such as emoji.

单词仅包含 `[A-Za-z]+`。查询键通过 `casefold()` 规范化，原文保留大小写。输入中的词和未登记词为黄色，完成后按照词库使用绿、蓝、红。QSyntaxHighlighter 只设置显示格式，不替换正文或重建 HTML，不干扰撤销历史。日常编辑只处理受影响的 Qt 文本块；包含 emoji 等字符时转换 Python 字符索引与 Qt UTF-16 位置。

## Persistence / 持久化

The dictionary is loaded into a Python dict on startup; typing performs no SQLite queries. Dictionary edits commit explicit transactions. A single worker serializes Markdown saves using a temporary file, `fsync` and replacement in the same directory. A 700 ms single-shot timer coalesces disk saves; it is not a text polling loop or highlighting debounce. Document switches and normal shutdown flush the current draft before continuing.

词库启动时加载到 Python dict，输入期间不查询 SQLite。词条修改通过显式事务提交。单个后台线程按序保存 Markdown，使用同目录临时文件、`fsync` 和替换保护原文。700 ms 一次性计时器合并磁盘保存，不用于轮询正文或延迟着色。切换文档和正常退出前会等待保存。

Database relocation uses SQLite's backup API and checks integrity and dumped content before committing the fixed user-directory path configuration. Article relocation verifies SHA-256 before deleting originals. Conflicting destinations are preserved. Cleanup plans can be retried when old files are busy; unrelated files remain untouched. The vocabulary remains shared across every date and the current source/frozen builds.

词库迁移通过 SQLite backup 接口复制并校验完整性与数据，随后提交固定用户目录中的路径配置。文章迁移校验 SHA-256 后才删除原文；目标冲突时保留原文件。旧文件被占用可重试清理，其他文件保留。每个日期以及当前源码/打包程序继续共用一个词库。

## Reproducible checks / 可复现验证

Run `python -m unittest discover -s tests -v` for the current 48 tests. Qt offscreen events cover case matching, token completion, punctuation, merge/replacement edits, bulk paste, UTF-16, indentation, undo/redo, native keyboard flow, daily files, restarts, migration failures and legacy level conversion. Every persistence test uses temporary data.

运行 `python -m unittest discover -s tests -v` 执行当前 48 项测试，覆盖大小写、完成词、分隔符、合并/替换、粘贴、UTF-16、缩进、撤销重做、键盘操作、日文档、重启、迁移失败与旧程度转换。所有持久化测试都使用临时数据。

Run `python -m benchmarks.benchmark` to record machine-specific timings in `benchmarks/results.json`. Historical measurements on Windows 11 / Python 3.13.5 / PySide6 6.8.3: 120,000-character multiline paste 74.632 ms; two-key local edits median 0.076 ms, P95 0.093 ms, at most two blocks. The benchmark excludes screen presentation and disk writes; it is not a universal latency guarantee.

运行 `python -m benchmarks.benchmark` 记录本机耗时。历史 Windows 11 / Python 3.13.5 / PySide6 6.8.3 数据：12 万字符多段落粘贴 74.632 ms；局部两键输入中位数 0.076 ms、P95 0.093 ms，最多两个块。计时不包括屏幕呈现和磁盘保存，不能视为所有设备的延迟保证。

## Boundaries / 已知边界

Very long single paragraphs are scanned as a whole. Global vocabulary refresh and large initial loads run on the GUI thread. Forced termination may lose the newest unsaved input. Undo history does not persist across documents or restarts. Concurrent writers and old application versions can overwrite data or use an obsolete database path; use one current writing instance. Markdown stores text rather than highlight colors, so historical articles reflect the current shared vocabulary.

极长单段落仍扫描整个段落，全局词库刷新和大文本首次加载在 GUI 线程执行。强制结束可能丢失最新未保存输入，撤销历史不跨文档或重启。并发写入及旧版程序可能互相覆盖或使用旧路径，建议只用一个当前版本的写作实例。Markdown 保存正文而非颜色，历史文章按当前词库显示。
