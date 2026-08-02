# 乐享 MCP 接入约定

WebMark 使用腾讯乐享官方 MCP，不把 AppKey、AppSecret 或 access token 写进代码。

推荐在 WorkBuddy 的 MCP 管理界面配置用户级服务，服务名固定为 `lexiang`。为减少无关工具，优先使用 `knowledge.entry` preset；若当前客户端无法识别远程 MCP URL，可使用 `npx mcp-remote` 桥接。

WebMark 主要使用 `knowledge_import_content` 导入 Markdown。工具参数必须通过运行时 schema 获取；MCP 版本变化时，不在 SKILL.md 中硬编码参数结构。

乐享内部返回地址可能使用 `mcp.lexiang-app.com`。对 Master 输出时只使用：

```text
https://lexiangla.com/pages/{entry_id}
```
