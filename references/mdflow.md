# mdFlow 运行配置契约

WebMark 默认初始化地址：

```text
https://config.fanqiemiao.com/mdFlow/v1/manifest.json
```

读取策略：首次初始化、本地缓存缺失、缓存损坏或 Master 明确升级时联网；日常运行只读本地缓存。

## WebMark 运行目标

FolderMark-Raw 与乐享目标均由 JSON 下发：

```json
{
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

这些 ID 用于定位写入目标，不用于身份认证。乐享 token、服务器密码和同步密钥不得进入 mdFlow。

本地 `config/local.json` 可以提供同名非空覆盖值。解析顺序为：

```text
本地非空覆盖
→ mdFlow 下发
→ 缺失时报错
```

公开模板使用占位符；Master 的私有远程 JSON 写入实际目标 ID。
