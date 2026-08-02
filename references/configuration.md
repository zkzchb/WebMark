# WebMark 配置约定

`config.json` 是唯一的本地入口。它支持 inline 和 remote 两种来源，并允许本地 `overrides` 深度覆盖最终设置。

远程配置只在初始化、缓存缺失或损坏、显式升级时下载。普通运行只读缓存。

远程 `selector` 默认指向 `runtime.webmark`，但可配置为其他 JSON 对象路径。

所有个性化设置放在最终 `settings` 对象中。认证信息不得放入 JSON；只保存 `credential_ref`。
