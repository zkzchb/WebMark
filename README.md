# WebMark

WebMark 是面向 Tencent WorkBuddy 的网络资料采集 Skill。Master 从 WorkBuddy App、微信、QQ 或飞书发送 URL 后，WebMark 优先使用 WorkBuddy 内置抓取能力取得页面内容，再完成基础清洗、初步分类、mdFlow YAML、Raw Markdown 落盘、乐享归档和 FolderMark-Raw 同步。

最终普通回复只返回：

```text
乐享：https://lexiangla.com/pages/{entry_id}
Raw：https://md.fanqiemiao.com/{collection}/{document_id}
```

本地路径仍保留在机器结果中，但不向 Master 日常回传。

## 项目边界

- **WebMark**：数据采集 Skill。
- **CleanMark**：深度整理 Skill，不原地修改 Raw。
- **FolderMark**：独立开源发布程序，不依赖 mdFlow。
- **PublishMark**：基于 FolderMark 的具体 Clean 内容站点。
- **mdFlow**：WebMark、CleanMark、PublishMark 共同遵守的规范与配置中心。

## 设计原则

1. **WorkBuddy 优先抓取**：默认使用内置 `WebFetch`；微信公众号页面禁止先用 Python 抓取。
2. **确定性操作下沉**：ID、YAML、文件写入和 URL 计算由 Python 核心完成。
3. **配置下发**：FolderMark-Raw 域名不硬编码，由 mdFlow JSON 下发；当前值为 `https://md.fanqiemiao.com`。
4. **本地优先**：Raw Markdown 是权威资产，乐享是检索与问答副本。
5. **静默运行**：成功时只回传乐享 URL 与 Raw URL。

## WorkBuddy 前置条件

### 必需

- Tencent WorkBuddy 已安装并可使用“技能”与 MCP。
- WorkBuddy 内置 `WebFetch` 可用。
- WorkBuddy 获得 `D:\claw\md_inbox` 的写入权限，以及运行本 Skill Python 脚本的权限。
- Python 3.11 或更高版本。WorkBuddy 内置 Python 可满足时无需另外安装。
- 腾讯乐享官方 MCP 已连接，至少可调用知识条目工具。

WorkBuddy 支持从“技能 → 添加技能 → 上传技能”导入本地技能包，也兼容 OpenClaw 社区 Skill。仓库同时提供 `SKILL.md` 和 `skill.yml`；最终发布前仍须以 WorkBuddy 实际导入结果完成兼容性验收。

### 可选

- `web-scraper` Skill：当内置 WebFetch 无法取得完整正文时使用，不是默认抓取器。
- 浏览器类 Skill：用于必须执行 JavaScript 或需要交互的网页。

## 安装乐享 MCP

1. 登录乐享并打开 MCP 配置页，创建 OAuth 会话或 access token。
2. 在 WorkBuddy 中打开“插件 → MCP 服务器 → 配置 MCP”。
3. 建议把乐享配置为用户级 MCP，服务名固定为 `lexiang`。
4. 优先限制为 `knowledge.entry` preset；若 WorkBuddy 当前版本不能直接连接远程 MCP URL，使用 Node.js 的 `npx mcp-remote` 桥接。
5. 保存后确认 MCP 状态正常，并测试能发现 `knowledge_import_content`。

示例（令牌不得提交到 Git）：

```json
{
  "mcpServers": {
    "lexiang": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.lexiang-app.com/mcp?company_from=YOUR_CODE&access_token=YOUR_TOKEN&preset=knowledge.entry"
      ]
    }
  }
}
```

WorkBuddy 用户级 MCP 配置通常位于 `~/.workbuddy/mcp.json`，也可以直接通过界面配置。乐享凭据只放在本地 MCP 配置中。

## 安装 WebMark

1. 下载本仓库的 Skill 包。
2. 在 WorkBuddy 技能页选择“添加技能 → 上传技能”。
3. 启用 WebMark。
4. 将 `config/example.local.json` 复制为 `config/local.json`。
5. 安装 Python 依赖：

```bash
python -m pip install -e .
```

6. 首次执行：

```bash
python scripts/webmark.py --config config/local.json init
python scripts/webmark.py --config config/local.json preflight
```

不要把 `config/local.json`、MCP token、服务器账号或同步密钥提交到 Git。

mdFlow 初始化地址：

```text
https://config.fanqiemiao.com/mdFlow/v1/manifest.json
```

仅首次初始化、本地缓存缺失或 Master 明确升级时联网读取；日常运行不主动检查更新。

## WorkBuddy 调用方式

WorkBuddy 先抓取并整理网页，再把结构化 JSON 交给确定性脚本：

```bash
python scripts/webmark.py --config config/local.json ingest --input payload.json
```

最小 payload：

```json
{
  "source_url": "https://example.com/article",
  "fetched_by": "workbuddy.WebFetch",
  "title": "页面标题",
  "body_markdown": "正文或资源描述",
  "content_type": "article",
  "collection": "technology"
}
```

脚本返回本地路径、稳定 ID 和 Raw URL。随后 WorkBuddy 调用乐享 MCP 导入同一份 Markdown，并执行服务器同步。完整流程见 [SKILL.md](./SKILL.md)。

## mdFlow 中的 Raw 站点配置

建议由 manifest 下发：

```json
{
  "runtime": {
    "webmark": {
      "raw_site_base_url": "https://md.fanqiemiao.com"
    }
  }
}
```

解析优先级：本地显式覆盖 > mdFlow 下发值。程序代码本身不保存域名。

## 当前目录

```text
WebMark/
├── SKILL.md
├── skill.yml
├── README.md
├── config/
│   ├── example.local.json
│   └── example.manifest.json
├── scripts/
│   └── webmark.py
├── src/webmark/
│   ├── archive.py
│   ├── cli.py
│   └── config.py
├── references/
│   ├── workbuddy.md
│   ├── lexiang.md
│   └── mdflow.md
└── tests/
```

## 当前尚待接通

- FolderMark-Raw 服务器同步适配器及凭据配置；
- mdFlow 正式 manifest 字段与分类文件；
- WorkBuddy 技能包导入实测；
- 乐享 MCP 在 WorkBuddy 中的端到端写入实测；
- 微信、QQ、飞书入口的统一自动触发验收。

## 参考文档

- WorkBuddy 技能与本地技能包：https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market
- WorkBuddy MCP：https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide
- 腾讯乐享 MCP：https://cloud.tencent.com/developer/mcp/server/11802
- 乐享 MCP 官方仓库：https://github.com/tencent-lexiang/lexiang-mcp-server
