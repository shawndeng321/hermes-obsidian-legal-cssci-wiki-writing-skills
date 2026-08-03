# 法学研究 Wiki 建库 Skill

为法学学术研究（行政法群案研究、论文写作、法律知识库）构建 LLM Wiki 的核心技能。基于 Karpathy LLM Wiki 方法论，融合中文法律材料摄入纪律。

**v3.0.0** 已吸收原 `wiki-content-completeness`（内容完整性强制纪律：每页必须写满实质内容，不允许空壳页面）。

## 功能

- 范围优先摄入（scope-first）：先勘察、再确认范围、分批复核
- 批量 PDF 提取（pymupdf / marker-pdf）与格式清洗
- 案例 DOCX 解析（53 案简编 / 121 案编译集 / 公报汇编等）
- 死链预防与交叉引用网络构建（论文↔底稿↔案例双向链接）
- 六维质量门禁：摘要纯中文 / 结论完整 / 无 PDF 残留 / 关键词干净 / YAML 合法 / 标题空行
- 学术可用性审计（模板化检测、假说 vs 事实区分、来源可追溯）

## 安装

```bash
# Hermes Agent（macOS/Linux）
git clone <本仓库地址> ~/.hermes/skills/legal-research-wiki

# 或手动复制
cp -R legal-research-wiki ~/.hermes/skills/
```

## 使用

- 摄入论文/案例/法条时加载本技能，先读 `SCHEMA.md` → `index.md` → `log.md` → 台账，再确认范围
- 每批摄入后运行死链检查 + 六维质量检查 + 交叉引用网络检查
- 详细规则见 [SKILL.md](SKILL.md) 与 `references/`

## 配套

- 维护/排查修复：[legal-wiki-audit-repair](../legal-wiki-audit-repair)
- 论文写作：[chinese-law-paper-writing](../chinese-law-paper-writing)

## License

MIT © 2026 Shawn Deng
