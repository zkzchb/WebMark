# WorkBuddy 运行约定

- Skill 包根目录必须包含 `SKILL.md`。
- `SKILL.md` 的 YAML Front Matter 至少包含 `name` 和 `description`。
- 其他 JSON、脚本、依赖和参考文档可以放在同一技能目录内。
- Skill 运行时先解析技能目录，再读取根目录 `config.json`。
- 所有工具名称、运行命令和回传偏好以解析后的 settings 为准。
