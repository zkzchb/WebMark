# 乐享 MCP 接入约定

WebMark 使用腾讯乐享 MCP，不把 AppKey、AppSecret、access token 或 OAuth 凭据写进代码、远程 JSON、Markdown 或日志。

建议在 WorkBuddy 的 MCP 管理界面配置用户级服务，服务名固定为 `lexiang`。WebMark 主要使用 `knowledge_import_content` 导入 Markdown；工具参数必须通过运行时 schema 获取，不在 SKILL.md 中硬编码易变参数结构。

## 目标位置配置

以下非敏感字段由 mdFlow JSON 下发，或由本地 JSON 覆盖：

```json
{
  "team_id": "YOUR_TEAM_ID",
  "space_id": "YOUR_SPACE_ID",
  "root_entry_id": "YOUR_ROOT_ENTRY_ID",
  "public_page_base_url": "https://lexiangla.com/pages"
}
```

它们只决定导入位置和公开链接，不承担认证作用。

归档成功取得 `entry_id` 后，对 Master 输出：

```text
{public_page_base_url}/{entry_id}
```
