# WordSense Logo

使用内置 imagegen 工具生成，原始透明 PNG：`wordsense-logo.png`；Windows 多尺寸图标：`wordsense.ico`。

设计：用展开书页构成 W，深色圆角底板、Everforest 绿和青色主体、黄色页边。适用于窗口、任务栏、桌面快捷方式和下载包。

最终生成提示词（内置工具；非 CLI）：

> Use case: logo-brand. Asset type: production Windows desktop application icon for WordSense, a local English writing and vocabulary-understanding editor. Create one polished square icon, straight-on, no mockup. An elegant bold W monogram cleverly shaped like an open book with folded pages, readable at 32 pixels. Everforest palette: dark charcoal #2D353B rounded-square tile, primary sage green #A7C080 and soft teal #7FBBB3 book/W strokes, a restrained small warm-yellow #DBBC7F page accent. Simple thick geometric shapes, clean balanced negative space, flat vector-like edges. The tile occupies nearly the whole canvas with only about 5% transparent outer padding; outside its rounded corners is genuinely transparent. No letters beyond the abstract W monogram, no wordmark, no caption, no border, no gradients, no glow, no shadow, no photographic textures, no extra illustrations. One single centered icon, high-resolution square asset.

ICO 封装使用 Qt 转换成 16/24/32/48/64/128/256 像素 PNG 帧，保留透明通道，不改动原图设计。可运行 `python -m tools.make_icon` 重建。
