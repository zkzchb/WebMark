# WorkBuddy 运行说明

## 必需能力

- WorkBuddy 内置 `WebFetch`：默认抓取器，也是微信公众号页面的首选。
- 本地文件读写和 Python 执行权限：用于生成 Raw Markdown。
- 乐享 MCP：用于知识库归档。

## 可选能力

- `web-scraper` Skill：仅在 WebFetch 无法取得完整正文时回退使用。
- 浏览器型 Skill：用于必须执行 JavaScript 或需要交互的页面。

## 权限原则

只授权 WebMark 所需的本地目录、Python 命令和目标网络服务。不要要求对整台电脑永久开启无限制权限。
