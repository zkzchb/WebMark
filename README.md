# WebMark

WebMark 是一个面向桌面 Agent 的网络资料采集 Skill。当前计划安装在 WorkBuddy 中，用于将用户通过 WorkBuddy App、微信、QQ、飞书等入口发送的 URL，自动转换为结构化的 Raw Markdown，并完成分类、存储、乐享知识库上传和原始站点同步。

## 项目关系与自动化工作流

这套 Markdown 工作流由五个相互配合、边界独立的项目组成：

- **WebMark**：数据采集 Skill；
- **CleanMark**：深度整理 Skill；
- **FolderMark**：无具体内容的开源发布程序；
- **PublishMark**：包含 Clean 内容的具体 FolderMark 项目；
- **mdFlow**：各环节共同遵守的内容分类、YAML 和处理规范中心。

它们与桌面 Agent 一起组成以下自动化工作流：

```text
用户通过 WorkBuddy App / 微信 / QQ / 飞书发送 URL
                         ↓
               WorkBuddy 调用 WebMark
                         ↓
        抓取、基础清洗、分类并生成 Raw Markdown
              ├── 保存到本地 Raw 文件夹
              ├── 上传对应的乐享知识库
              └── 同步到服务器 Markdown 文件夹
                         ↓
              FolderMark-Raw 即时展示原始资料
                         ↓
               WorkBuddy 调用 CleanMark
                         ↓
             深度清洗并生成独立 Clean 内容
                         ↓
               写入 PublishMark 并提交 Git
                         ↓
             Cloudflare 自动部署正式内容站点
```

FolderMark 是独立的通用开源项目，不依赖 mdFlow，也不读取任何外部配置中心。PublishMark 是基于 FolderMark 建立的具体站点实例，可以根据正式内容发布需要对 FolderMark 做少量适配。

## WebMark 的职责

WebMark 负责工作流的第一阶段：让网络资料快速、稳定地进入本地 Markdown 体系。

```text
URL
→ 网页抓取
→ 基础清洗
→ 初步分类
→ 生成 YAML Front Matter
→ 保存 Raw Markdown
→ 上传乐享知识库
→ 同步 FolderMark-Raw
→ 返回访问地址
```

主要职责包括：

- 接收来自桌面 Agent 和 IM 入口的 URL；
- 提取网页标题、作者、来源、发布时间和正文；
- 删除导航、广告、页脚、推荐阅读等网页噪声；
- 保留标题层级、列表、引用、图片和原始链接；
- 生成基础摘要和初步分类；
- 按 `collection` 写入对应的 Raw 内容目录；
- 生成符合 mdFlow 规范的 YAML Front Matter；
- 上传到对应的乐享知识库；
- 将 Raw Markdown 单向同步到 FolderMark-Raw 服务器目录；
- 返回本地文件路径、乐享 URL 和 Raw 站点 URL；
- 对重复 URL 和重复正文进行基础检测。

## 数据边界

- WebMark 只做采集阶段必要的基础清洗，不负责深度改写；
- Raw Markdown 是原始证据层；
- CleanMark 只读取 Raw 文件，不原地修改 Raw 文件；
- Raw 内容不进入 PublishMark；
- 本地 Markdown 是权威数据资产，乐享是检索和问答副本。

## mdFlow 配置

WebMark 使用 mdFlow 获取统一的分类、YAML 和采集规则。

默认初始化地址：

```text
https://my-work-flow.pages.dev/mdFlow/v1/manifest.json
```

读取原则：

1. 首次初始化时读取远程 manifest 并安装配置；
2. 日常运行只读取本地已安装版本；
3. 本地配置缺失或损坏时重新下载；
4. 升级时由用户明确指定新的 manifest 地址；
5. WebMark 不主动检查或自动安装远程更新。

远程 mdFlow 不保存实际本地路径、乐享凭据、服务器账号或同步密钥。这些信息由本地配置和环境变量提供。

## 计划中的目录结构

```text
WebMark/
├── README.md
├── SKILL.md
├── scripts/
│   └── mdflow.py
├── config/
│   └── example.local.json
├── templates/
│   └── raw.md
├── tests/
└── docs/
```

## 状态

项目处于初始设计与开发阶段。