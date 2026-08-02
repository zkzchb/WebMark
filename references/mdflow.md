# mdFlow 运行配置契约

WebMark 默认初始化地址：

```text
https://config.fanqiemiao.com/mdFlow/v1/manifest.json
```

读取策略：首次初始化、本地缓存缺失、缓存损坏或 Master 明确升级时联网；日常运行只读本地缓存。

FolderMark-Raw 基地址由 JSON 下发：

```json
{
  "runtime": {
    "webmark": {
      "raw_site_base_url": "https://md.fanqiemiao.com"
    }
  }
}
```

本地 `raw_site_base_url` 仅作为显式覆盖。程序代码中不得硬编码该域名。
