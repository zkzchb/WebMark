# WebMark

WebMark 是面向 Tencent WorkBuddy 的网络资料采集 Skill。Master 从 WorkBuddy App、微信、QQ 或飞书发送 URL 后，WebMark 优先使用 WorkBuddy 内置抓取能力取得页面内容，再完成基础清洗、初步分类、mdFlow YAML、Raw Markdown 落盘、乐享归档和 FolderMark-Raw 同步。

成功时普通回复只返回：

```text
乐享：{public_page_base_url}/{entry_id}
Raw：{raw_site_url}
```

本地文件路径仍保留在机器结果中，但不向 Master 日常回传。

## WorkBuddy 导入要求

根据 WorkBuddy 当前导入界面：

- 可以上传文件夹或 ZIP；
- 文件夹或 ZIP 必须包含 `SKILL.md`；
- `SKILL.md` 必须以 YAML Front Matter 提供技能名称和描述。

因此 WorkBuddy 版本只把根目录 `SKILL.md` 作为技能入口，不再依赖额外的 `skill.yml`。

稳定版发布时，Release ZIP 将确保 `SKILL.md` 位于压缩包根目录。是否再从 `main` 提供其他 Agent 的在线安装版本，等 WorkBuddy 版本稳定后另行确定；当前开发分支只服务 WorkBuddy。

## 项目边界

- **WebMark**：数据采集 Skill。
- **CleanMark**：深度整理 Skill，不原地修改 Raw。
- **FolderMark**：独立开源发布程序，不依赖 mdFlow。
- **PublishMark**：基于 FolderMark 的具体 Clean 内容站点。
- **mdFlow**：WebMark、CleanMark、PublishMark 共同遵守的规范与配置中心。

## 设计原则

1. **WorkBuddy 优先抓取**：默认使用内置 `WebFetch`；微信公众号页面禁止先用 Python 抓取。
2. **确定性操作下沉**：稳定 ID、YAML、文件写入和 URL 计算由 Python 核心完成。
3. **同构 JSON 配置**：你可以通过远程 URL 下发配置，其他用户可以复制模板后在本地填写。
4. **非敏感目标可下发**：Raw 站点域名、乐享团队 ID、知识库 ID、父节点 ID 可以进入 JSON。
5. **敏感凭据只留本地**：乐享 token、服务器密码和同步密钥不得进入远程 JSON、Git 或 Markdown。
6. **本地优先**：Raw Markdown 是权威资产，乐享是检索与问答副本。
7. **静默运行**：成功时只回传乐享 URL 与 Raw URL。

## 配置模型

WebMark 有两个配置层：

```text
config/local.json
        ↓ 本地路径、远程配置 URL、可选覆盖
mdFlow manifest JSON
        ↓ 分类、YAML、Raw 站点和乐享目标
WebMark 运行时配置
```

默认远程地址：

```text
https://config.fanqiemiao.com/mdFlow/v1/manifest.json
```

日常运行只读取本地缓存。只有以下情况才联网读取：

- 首次初始化；
- 本地缓存缺失或损坏；
- Master 明确要求升级到新地址。

### 远程 JSON 模板

```json
{
  "schema": "mdFlow-manifest-v1",
  "version": "1.0.0",
  "runtime": {
    "webmark": {
      "raw_site_base_url": "https://md.fanqiemiao.com",
      "lexiang": {
        "team_id": "YOUR_TEAM_ID",
        "space_id": "YOUR_SPACE_ID",
        "root_entry_id": "YOUR_ROOT_ENTRY_ID",
        "public_page_base_url": "https://lexiangla.com/pages"
      }
    }
  }
}
```

你的远程 JSON 可以写入实际值。公开仓库中的 `config/example.manifest.json` 只保留占位符。

### 本地手工配置

不使用远程下发的用户，可以在 `config/local.json` 中填写同名覆盖字段：

```json
{
  "raw_root": "D:\\claw\\md_inbox",
  "manifest_cache": "D:\\claw\\mdflow\\v1\\manifest.json",
  "manifest_url": "https://example.com/my-mdflow/manifest.json",
  "raw_site_base_url": "https://md.example.com",
  "lexiang": {
    "team_id": "MY_TEAM_ID",
    "space_id": "MY_SPACE_ID",
    "root_entry_id": "MY_ROOT_ENTRY_ID",
    "public_page_base_url": "https://lexiangla.com/pages"
  }
}
```

解析优先级：

```text
本地非空覆盖值
→ 远程 manifest 下发值
→ 缺失则报错
```

## WorkBuddy 前置条件

### 必需

- Tencent WorkBuddy 已安装并可导入本地 Skill；
- WorkBuddy 内置 `WebFetch` 可用；
- WorkBuddy 能写入本地 Raw 目录并运行 Python；
- Python 3.11 或更高版本；
- 腾讯乐享 MCP 已连接，并可调用知识条目导入工具。

### 可选

- `web-scraper` Skill：内置 WebFetch 不能完整抓取时使用；
- 浏览器类 Skill：处理必须执行 JavaScript 或需要交互的网页。

## 安装乐享 MCP

1. 在 WorkBuddy 中配置乐享 MCP，建议服务名固定为 `lexiang`。
2. 优先只开放知识条目相关工具。
3. 确认能够发现并调用 `knowledge_import_content`。
4. 乐享 token 只放在 WorkBuddy 的本地 MCP 配置中。

WebMark 从解析后的 JSON 获取：

- `team_id`；
- `space_id`；
- `root_entry_id`；
- `public_page_base_url`。

这些字段决定写入位置和最终链接，不承担身份认证。

## 安装 WebMark

1. 下载或解压 Skill 包。
2. 确认包根目录存在 `SKILL.md`。
3. 在 WorkBuddy 中选择“导入技能”，上传文件夹或 ZIP。
4. 将 `config/example.local.json` 复制为 `config/local.json`。
5. 安装 Python 依赖：

```bash
python -m pip install -e .
```

6. 首次初始化并检查：

```bash
python scripts/webmark.py --config config/local.json init
python scripts/webmark.py --config config/local.json preflight
```

不要把 `config/local.json`、MCP token、服务器账号或同步密钥提交到 Git。

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

脚本返回：

```json
{
  "status": "success",
  "local_path": "D:\\claw\\md_inbox\\technology\\...md",
  "raw_site_url": "https://md.fanqiemiao.com/technology/xxxxxxxxxx",
  "document_id": "xxxxxxxxxx",
  "lexiang": {
    "team_id": "...",
    "space_id": "...",
    "root_entry_id": "...",
    "public_page_base_url": "https://lexiangla.com/pages"
  }
}
```

随后 WorkBuddy 使用这些目标 ID 调用乐享 MCP，并执行 FolderMark-Raw 同步。完整流程见 [SKILL.md](./SKILL.md)。

## 当前目录

```text
WebMark/
├── SKILL.md
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

- 将实际乐享目标 ID 写入你的远程 mdFlow JSON；
- FolderMark-Raw 服务器同步适配器及本地凭据；
- WorkBuddy ZIP 导入实测；
- 乐享 MCP 在 WorkBuddy 中的端到端写入实测；
- 微信、QQ、飞书入口的统一自动触发验收；
- 稳定后生成 WorkBuddy Release ZIP。
