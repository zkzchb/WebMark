# WebMark

WebMark 是 WorkBuddy 优先的 URL 采集 Skill：由 WorkBuddy 使用配置指定的内置工具抓取网页，再由确定性脚本生成 Raw Markdown，并按配置选择性执行知识库归档和 Raw 站点同步。

## WorkBuddy 包结构

WorkBuddy 可以导入文件夹或 ZIP，根目录必须包含带 YAML Front Matter 的 `SKILL.md`。实际参考包也证明，`SKILL.md` 可以读取同目录 JSON、模板和脚本。因此 WebMark 的 WorkBuddy Release 将保持下面的直接结构：

```text
WebMark/
├── SKILL.md
├── config.json
├── README.md
├── requirements.txt
├── scripts/
├── src/
└── references/
```

稳定后发布的 ZIP 会让 `SKILL.md` 直接位于压缩包根目录，不再依赖额外技能元数据文件。

## 核心原则：Skill 无个人设置

`SKILL.md` 不保存以下内容：

- 用户称呼和个人触发偏好；
- 本地绝对路径、Python 路径；
- 配置中心 URL；
- 抓取工具和回退 Skill 名称；
- 分类阈值与默认目录；
- Raw 站点域名和服务器目录；
- MCP 服务名、工具名、团队 ID、知识库 ID 和父节点 ID；
- 回传字段、标签、摘要和本地路径偏好。

这些内容全部进入 JSON。代码也不提供任何特定用户的默认域名、路径或 ID。

认证信息是例外：token、密码、私钥、AppSecret 等不应进入远程或本地 WebMark JSON。JSON 只保存 `credential_ref`，真正凭据由 WorkBuddy MCP、SSH profile 或本地凭据系统管理。程序会拒绝常见明文 secret 字段。

## 两种配置方式

### 远程下发

适合个人长期使用。根目录 `config.json` 只保存配置来源、缓存位置和本机启动命令：

```json
{
  "schema": "webmark-bootstrap-v1",
  "bootstrap": {
    "python_command": "python",
    "pip_command": "python -m pip"
  },
  "source": {
    "mode": "remote",
    "url": "https://config.example.com/mdflow/v1/manifest.json",
    "cache_path": "~/.webmark/config-cache.json",
    "selector": "runtime.webmark",
    "request_timeout_seconds": 30
  },
  "settings": {},
  "overrides": {}
}
```

远程文档中被 `selector` 选中的对象包含全部 WebMark 个性化设置。日常运行只读取缓存；首次初始化、缓存缺失或损坏、显式升级时才访问远程 URL。

### 本地填写

适合公开用户。保持 `source.mode` 为 `inline`，直接修改 `config.json` 中的 `settings`。仓库提供一份不含个人数据的完整模板。

本地 `overrides` 会深度覆盖远程设置，适合临时更换目录或关闭某个集成。

## 配置范围

完整 JSON 可配置：

- `trigger`：自动触发和多 URL 行为；
- `runtime`：Agent 运行参数；
- `fetch`：主抓取工具、域名规则、回退 Skill、Prompt 和脚本回退；
- `classification`：文章判定阈值和兜底分类；
- `storage`：Raw 根目录、文件名、编码和 ID 长度；
- `front_matter`：Raw YAML 初始状态；
- `lexiang`：是否启用、MCP 服务和工具名称、目标 ID、公开链接基地址；
- `raw_publish`：站点基地址、同步 adapter、profile、目标目录和验证；
- `response`：成功回传字段、标签、摘要、本地路径和批量格式。

远程完整模板见 `mdflow.webmark.example.json`，远程启动模板见 `config.remote.example.json`。

## 安装

1. 下载 Release ZIP 或文件夹。
2. 确认 `SKILL.md` 位于包根目录。
3. 在 WorkBuddy 的“导入技能”界面上传。
4. 编辑根目录 `config.json`，选择 remote 或 inline 模式。
5. 安装依赖：

```text
{pip_command} install -r "<skill_dir>/requirements.txt"
```

6. 初始化并检查：

```text
{python_command} "<skill_dir>/scripts/webmark.py" --config "<skill_dir>/config.json" init
{python_command} "<skill_dir>/scripts/webmark.py" --config "<skill_dir>/config.json" preflight
```

其中 `{python_command}` 和 `{pip_command}` 取自 `config.json` 的 `bootstrap`。

## 命令

查看 Agent 应使用的最终配置：

```text
webmark --config config.json config
```

初始化或显式刷新远程缓存：

```text
webmark --config config.json init
webmark --config config.json init --upgrade-url https://config.example.com/new.json
```

检查配置和 Raw 目录：

```text
webmark --config config.json preflight
```

归档 WorkBuddy 已抓取的结构化内容：

```text
webmark --config config.json ingest --input payload.json
```

## 分支与发布

当前先稳定 WorkBuddy 版本。稳定后：

- 为 WorkBuddy 建立稳定分支；
- 通过 GitHub Releases 提供根目录含 `SKILL.md` 的 ZIP；
- 是否让 `main` 面向其他 Agent 在线安装，待其他平台规范确定后再决定。

现在不为了未知平台兼容性削弱 WorkBuddy 版。
