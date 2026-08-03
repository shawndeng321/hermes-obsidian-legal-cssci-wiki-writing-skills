# Hermes 法学研究技能包（Chinese Legal Research Skills for Hermes Agent）

一套为**中国法学学术研究**设计的 Hermes Agent 技能集，覆盖「知识库建库 → 维护排查 → 论文写作」完整流程。源自群案研究实战迭代，2026-08 经三轮合并收敛为 3 个核心技能。

## 技能一览

| 技能 | 版本 | 定位 | 覆盖任务 |
|---|---|---|---|
| [`legal-research-wiki`](legal-research-wiki/) | **v3.0.0** | 建库 | 摄入论文/案例/法条、PDF/DOCX 提取、交叉引用网络、六维质量门禁 |
| [`legal-wiki-audit-repair`](legal-wiki-audit-repair/) | **v3.1.0** | 维护 | 全库体检、每日检修（三日迭代）、P0—P3 问题分级、分批修复、批量重命名/链接迁移/反链补齐、统计复核 |
| [`chinese-law-paper-writing`](chinese-law-paper-writing/) | **v4.0.0** | 写作 | 五问框架、PLAN→ADAPT 七模式、五项硬门禁、推理链/统计口径、投稿 docx 生成 |

**合并历史**（2026-08）：`wiki-content-completeness` → legal-research-wiki；`wiki-batch-operations` → legal-wiki-audit-repair；`five-questions-framework` + `legal-paper-argumentation` + `academic-paper-docx` → chinese-law-paper-writing。内容全部保留，无删除。

## 安装

### 方式一：Hermes Skills System（推荐）

每个技能是独立目录，放入 Hermes 的本地技能目录即可自动发现：

```bash
# macOS / Linux
git clone <本仓库地址> ~/.hermes/skills/

# 或只装需要的：
git clone <本仓库地址> ~/.hermes/skills/ && cp -R chinese-law-paper-writing ~/.hermes/skills/
```

> Windows：`%USERPROFILE%\.hermes\skills\`

### 方式二：手动复制

```bash
cp -R legal-research-wiki ~/.hermes/skills/
cp -R legal-wiki-audit-repair ~/.hermes/skills/
cp -R chinese-law-paper-writing ~/.hermes/skills/
```

### 方式三：Herd / Curator 安装（如果使用）

```bash
hermes skills install <本仓库地址>
```

安装后验证：`hermes skills list` 应看到三个技能均为 enabled。

## 快速上手（一页工作流）

```text
【新项目开始】
  1. 读 chinese-law-paper-writing：启动纪律 → 五问框架问研究思路
  2. 用户确认思路后，用 legal-research-wiki 建库（先 SCHEMA → index → log 定向）
  3. 摄入顺序：方法论 → 论文 → 案例；每批验收（死链0 + 六维质量 + 交叉引用）

【日常维护】
  4. 用 legal-wiki-audit-repair 定期体检（AUDIT_ONLY 只读）
  5. 发现问题 → OPT 编号 → 用户确认范围 → 5-8页小批修复 → 全量验收
  6. 批量重命名/补链 → 读 references/batch-operations.md 安全流程

【论文写作】
  7. PLAN（五问选题）→ RESEARCH（证据核验）→ OUTLINE → DRAFT（中文主笔）
  8. REVISE（反说纪律：实证归纳在前）→ AUDIT（五项门禁）→ ADAPT（期刊适配）
  9. 交付 docx：chinese-law-paper-writing/references/docx-production.md
```

## 技能依赖关系

```text
chinese-law-paper-writing  (写作总纲，最高层)
        │  引用
        ▼
legal-research-wiki       (建库 + 质量门禁)
        │  引用
        ▼
legal-wiki-audit-repair   (维护 + 批量操作)
```

## 目录结构约定

```
hermes-legal-skills/
├── README.md                    # 本文件
├── LICENSE                      # MIT
├── legal-research-wiki/         # 技能1：建库
│   ├── SKILL.md                 # 技能主文件（frontmatter 含 name/description/version）
│   ├── README.md
│   ├── LICENSE
│   ├── references/              # 按需加载的详细规则（31 个参考文件）
│   └── scripts/                 # 可复用脚本（提取/死链检查/清洗）
├── legal-wiki-audit-repair/     # 技能2：维护
│   ├── SKILL.md
│   ├── README.md
│   ├── LICENSE
│   ├── references/              # 批量操作手册等（5 个）
│   └── scripts/                 # 链接同步/校验脚本（4 个）
└── chinese-law-paper-writing/   # 技能3：写作
    ├── SKILL.md
    ├── README.md
    ├── LICENSE
    ├── references/              # 工作流/引注/期刊适配/论证细则等（8 个）
    ├── scripts/                 # md2docx 脚注脚本
    └── assets/templates/        # 项目卡/来源登记/矩阵/审计模板（7 个）
```

## 使用前提

- **Hermes Agent**（任意版本，技能使用标准 SKILL.md frontmatter）
- Python 3.11+（scripts/ 目录下脚本；`md2docx_footnotes.py` 需 `python-docx`、`lxml`）
- [可选] pymupdf / marker-pdf：PDF 批量提取与 OCR
- 目标：法学论文写作（CSSCI 等）、法学知识库管理；**不适用于**书籍/学位论文/合同/法律意见书

## 版本策略

每个技能版本号遵循「内容迭代即升号」纪律（`X.Y`：大迭代改 `X`，增量改 `Y`）。本次打包基线：**2026-08-03**。

## License

MIT © 2026 Shawn Deng。技能内容来自作者法学论文写作与知识库管理实战，含用户确认的纪律条款（文中已标注 `user confirmed 2026-08` 的为作者个人方法论，可自由使用但建议注明出处）。
