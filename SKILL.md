---
name: webmark
description: "当 Master 发送 http/https URL 时，优先使用 WorkBuddy 内置 WebFetch 抓取（尤其是微信公众号），完成基础清洗、分类、Raw Markdown 落盘、乐享归档与 FolderMark-Raw 同步，最终只返回乐享 URL 和 Raw URL。"
homepage: https://github.com/zkzchb/WebMark
user-invocable: true
---

# WebMark

WebMark 是 WorkBuddy 优先的网络资料采集 Skill。确定性归档脚本位于 `{baseDir}/scripts/`，但网页抓取由 WorkBuddy 自身工具完成。

## 触发

当 Master 的消息中包含一个或多个 `http://` 或 `https://` URL，且没有明确要求不要归档时，自动逐个执行本流程。每个 URL 单独生成结果，不把多个页面拼成一篇 Raw 文档。

## 前置检查

首次运行或配置缺失时：

1. 确认 `WebFetch` 可用。
2. 确认乐享 MCP 已连接，并能发现 `knowledge_import_content`；若只暴露元工具，先用 `search_tools` 和 `get_tool_schema` 查找并调用。
3. 确认 `{baseDir}/config/local.json` 存在；缺失时复制 `config/example.local.json`，再补充本地私密配置。
4. 运行 `python {baseDir}/scripts/webmark.py --config {baseDir}/config/local.json preflight`。
5. 只有首次初始化、本地 mdFlow 缺失或 Master 明确升级时才运行 `init`。日常运行不得主动联网检查 mdFlow 更新。

## 流程

### 1. 抓取

优先调用 WorkBuddy 内置 `WebFetch`。对 `mp.weixin.qq.com` 页面，禁止先用 Python、requests、curl 或 wget 抓取。

如果 `WebFetch` 无法获得完整正文，再调用已安装的 `web-scraper` Skill 或 WorkBuddy 可用的浏览器抓取能力。只有 WorkBuddy 原生抓取均失败时，才允许脚本级 HTTP 抓取兜底。

### 2. 分流

将页面判定为：

- `article`：有连续正文的文章、新闻、博客、技术资料、公众号文章；
- `resource`：官网首页、工具页、产品页、下载页等没有可归档长正文的页面。

`article` 保留清理后的正文；`resource` 生成客观的一句话概述、主要功能、适用场景和关键入口，不虚构页面未提供的信息。

### 3. 基础处理

删除导航、广告、页脚、评论、推荐阅读和明显重复内容。保留标题层级、列表、引用、代码块、图片和原始链接。只做证据层必要清洗，不进行深度改写；深度整理属于 CleanMark。

根据本地 mdFlow 规则确定 `collection`、基础 `tags` 和 YAML 字段。无法可靠分类时使用 mdFlow 定义的兜底分类，不自行创造新分类。

### 4. 本地 Raw 归档

把处理结果写入临时 JSON，再调用：

```bash
python {baseDir}/scripts/webmark.py --config {baseDir}/config/local.json ingest --input <payload.json>
```

至少传入：

```json
{
  "source_url": "https://example.com/article",
  "fetched_by": "workbuddy.WebFetch",
  "title": "页面标题",
  "body_markdown": "正文或资源描述",
  "content_type": "article",
  "collection": "mdFlow 分类"
}
```

可选字段包括 `author`、`published`、`summary`、`tags`、`source_channel`。脚本返回 `local_path`、`document_id` 和 `raw_site_url`。`local_path` 仅供内部后续步骤使用，不在普通回复中展示。

### 5. 乐享归档

优先调用乐享 MCP 的 `knowledge_import_content`，导入同一份 Markdown 到 mdFlow 或本地配置指定的团队、知识库和父节点。不要把乐享凭据写入仓库、Markdown 或日志。

MCP 工具参数以运行时 schema 为准，不凭记忆猜测。归档成功后取得 `entry_id`，对外链接统一构造为：

```text
https://lexiangla.com/pages/{entry_id}
```

### 6. FolderMark-Raw 同步

按本地同步配置把刚生成的 Raw Markdown 单向同步到服务器内容目录。只有确认同步成功、Raw 页面可访问或同步程序明确返回成功后，才能将 `raw_site_url` 视为成功结果。

Raw 站点基地址不得硬编码在 Skill 或 Python 逻辑中。默认由 mdFlow 的 `runtime.webmark.raw_site_base_url` 下发；当前预期值为 `https://md.fanqiemiao.com`。本地配置可以显式覆盖。

### 7. 回复

全部成功时只返回两行：

```text
乐享：https://lexiangla.com/pages/{entry_id}
Raw：https://md.fanqiemiao.com/{collection}/{document_id}
```

不回传摘要，不回传本地路径，不解释执行过程。

若部分失败，已成功的归档不得回滚；简洁列出成功链接和失败环节。不得返回尚未完成同步的 Raw URL。

## 数据边界

- Raw Markdown 是原始证据层，本地文件是权威资产。
- 乐享是检索与问答副本。
- CleanMark 读取 Raw，但不原地修改 Raw。
- FolderMark 是独立发布程序，不读取 mdFlow。
- PublishMark 只接收 Clean 内容。
