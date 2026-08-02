---
name: webmark
description: "按照同目录 config.json 将 URL 采集为结构化 Raw Markdown，并执行配置启用的知识库归档、站点同步和结果回传。"
---

# WebMark

本 Skill 的行为由同目录 `config.json` 及其可选远程配置决定。不要把用户路径、站点地址、知识库 ID、工具名称、回传偏好或运行时路径写进本文件。

## 运行前

1. 将包含本文件的目录记为 `<skill_dir>`。
2. 读取 `<skill_dir>/config.json`，取得 `bootstrap.python_command`。
3. 使用该命令运行：

```text
{python_command} "<skill_dir>/scripts/webmark.py" --config "<skill_dir>/config.json" config
```

4. 以后本次任务只使用命令输出的已解析 `settings`。不要自行猜测缺失配置。
5. 如果依赖缺失，读取 `bootstrap.pip_command`，按 README 安装 `requirements.txt` 后重试一次。

远程配置只在首次初始化、本地缓存缺失或损坏、或者用户明确升级时联网读取。日常运行不得主动检查更新。

## 触发

读取 `settings.trigger`：

- 仅在配置允许的 URL 场景自动执行；
- 多个 URL 按 `multiple_urls` 规则处理；
- 用户明确要求不保存时不执行归档。

## 流程

### 1. 抓取

读取 `settings.fetch`：

1. 根据 URL 主机匹配 `domain_rules`；
2. 使用匹配规则指定的工具，否则使用 `primary_tool`；
3. 使用配置中的 `prompt` 提取标题、作者、发布日期和主内容；
4. 首选工具失败后，按 `fallback_skills` 顺序回退；
5. 仅当 `allow_script_fallback` 为 true 时调用配置的降级脚本。

不要绕过配置中针对特定站点指定的抓取工具。

### 2. 分流与基础清洗

按照 `settings.classification` 判断文章页或资源页。文章页保留完整正文结构；资源页生成客观描述和关键信息。去除导航、广告、评论、页脚、推荐和明显重复内容，保留标题层级、列表、引用、代码、表格、图片说明和原始链接。

这里只做采集阶段的基础清洗，不进行深度重写。

### 3. 分类与结构化输入

按照配置和已安装的 mdFlow 规则确定 `collection`、标签和其他元数据。不要自行创造配置之外的分类。

将每个 URL 写成独立临时 JSON，至少包含：

```json
{
  "source_url": "https://example.com/page",
  "fetched_by": "实际使用的工具名称",
  "title": "页面标题",
  "body_markdown": "清洗后的正文或资源描述",
  "content_type": "article",
  "collection": "配置允许的分类"
}
```

可选字段包括 `author`、`published`、`summary`、`tags` 和 `source_channel`。

### 4. Raw Markdown 落盘

调用：

```text
{python_command} "<skill_dir>/scripts/webmark.py" --config "<skill_dir>/config.json" ingest --input "<payload.json>"
```

脚本负责稳定 ID、文件名、YAML、目录和 Raw URL 计算。不要用 Agent 手工复制这些确定性逻辑。

`local_path` 是内部结果，是否向用户展示由 `settings.response` 决定。

### 5. 可选知识库归档

读取脚本返回的 `targets.lexiang`。仅当 `enabled` 为 true 时：

1. 使用配置指定的 `mcp_server` 和 `import_tool`；
2. 使用配置中的目标 ID；
3. 工具参数以运行时 schema 为准；
4. 凭据只从 WorkBuddy MCP 或本地凭据存储取得，不从 JSON、Markdown 或对话正文读取；
5. 使用 `public_page_base_url` 和返回的条目 ID 构造公开链接。

### 6. 可选 Raw 站点同步

读取 `targets.raw_publish`。仅当 `enabled` 为 true 时，按 `sync` 中的 adapter、profile 和目标目录执行单向同步。凭据通过 `credential_ref` 指向本地凭据，不得写进 Skill 或远程 JSON。

只有同步明确成功并满足配置的验证要求后，才把 `raw_site_url` 标记为可回传。

### 7. 回复

严格按照 `settings.response` 输出：

- 只包含 `success_fields` 指定的字段；
- 按 `labels` 使用配置的显示名称；
- 是否包含摘要、本地路径和批量表格由配置决定；
- 不暴露目标 ID、凭据引用、缓存路径或内部执行细节。

部分失败时保留已经成功的结果，简洁标明失败环节，不虚构尚未生成或尚未同步的链接。

## 数据边界

- Raw Markdown 是证据层资产。
- 深度整理由后续 Skill 完成，不原地改写 Raw。
- 发布程序与本 Skill 解耦。
- 所有用户个性化行为均来自 JSON；本文件只定义通用执行协议。
