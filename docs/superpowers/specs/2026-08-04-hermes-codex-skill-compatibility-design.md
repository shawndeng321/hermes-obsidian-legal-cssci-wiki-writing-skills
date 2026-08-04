# Hermes 与 Codex 单一技能源兼容设计

## 目标

让仓库中的三个技能继续使用同一份 `SKILL.md`，并同时通过本机 Hermes 与 Codex 的技能格式校验。此次只处理发现、元数据、Codex UI 元数据和安装说明，不改方法论正文、参考资料或业务脚本。

## 已确认的基线

- Hermes 能读取现有三个技能，但三个 `description` 都超过新技能建议的 60 字符路由预算。
- Codex `quick_validate.py` 对三个技能均失败，因为顶层包含 `version`、`platforms` 或 `author` 等非兼容字段。
- 仓库声明兼容 Hermes 与 Codex，但尚无 `agents/openai.yaml`，安装说明也会把整个仓库克隆到单个技能目录。

## 方案

### 1. 使用公共 frontmatter 子集

每个 `SKILL.md` 顶层只使用双方都接受的字段：

```yaml
---
name: skill-name
description: Use when ...
license: MIT
metadata:
  version: "x.y.z"
  author: "existing-author-if-present"
  hermes:
    tags: []
    related_skills: []
---
```

实施规则：

- 保持 `name` 不变并与目录名一致。
- 将描述压缩为以 `Use when` 开头、只表达触发条件、总长不超过 60 字符的一句话。
- 将现有 `version` 和 `author` 从顶层移入 `metadata`，不创造仓库中没有依据的作者信息。
- 删除值为全平台的 `platforms`；Hermes 在省略该字段时仍会在全部平台显示技能。
- 保留现有 `metadata.hermes` 内容；没有该内容的技能不额外发明标签或依赖。
- `license: MIT` 以每个技能目录现有的 MIT `LICENSE` 为依据。

### 2. 增加 Codex UI 元数据

为每个技能生成 `agents/openai.yaml`，只包含：

- `interface.display_name`
- `interface.short_description`
- `interface.default_prompt`

不添加未经提供的图标、品牌颜色或 MCP 依赖。`default_prompt` 必须明确提及对应的 `$skill-name`。

### 3. 修正安装说明

- Hermes 使用已验证能识别的逐技能安装标识，不再把整个仓库地址当成一个技能安装。
- Codex 说明先克隆仓库，再把三个技能目录分别复制到用户技能目录。
- 不改变仓库目录布局，也不建立 Hermes/Codex 两套正文副本。

### 4. 加入兼容性回归测试

新增一个仓库级测试，至少检查：

- 三个技能均存在且目录名与 `name` 一致；
- frontmatter 只包含公共字段；
- 描述满足 `Use when`、不超过 60 字符且以句号结束；
- `metadata` 和 `metadata.hermes` 的形状合法；
- 每个 `agents/openai.yaml` 包含三个必需 UI 字段，默认提示词引用正确技能名；
- 每个 `SKILL.md` 不超过 Hermes 的 100,000 字符限制。

## 测试顺序

1. 先新增兼容性测试并在原始仓库上运行，确认因现有 frontmatter/描述/缺少 `openai.yaml` 而失败。
2. 仅修改三个 frontmatter、增加三个 `agents/openai.yaml`、更新安装说明。
3. 运行兼容性测试，确认转绿。
4. 对三个技能分别运行 Codex `quick_validate.py`。
5. 对三个技能分别运行 Hermes `_validate_frontmatter`（含 `new_skill=True`）和 `_validate_content_size`。
6. 检查 Git diff，确认没有方法论正文或业务脚本变更。

## 非目标

- 不处理“反说纪律”、Obsidian 链接冲突、脚本安全、DOCX 脚注或技能体积问题。
- 不安装技能到用户的 Hermes/Codex 全局目录。
- 不推送 GitHub，不发布新版本或标签。

## 验收标准

- 三个技能的仓库级兼容测试全部通过。
- 三个技能的 Codex 校验全部通过。
- 三个技能的 Hermes 新技能校验与内容大小校验全部通过。
- `agents/openai.yaml` 字段完整且引用正确技能名。
- Git diff 仅包含本设计列出的兼容性文件和安装文档。
