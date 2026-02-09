# 一种Markdown转Word的Pipeline

## Markdown转Word的优点

- **AI友好**：可让AI生成Markdown，再转为Word，避免直接操作Word
- **样式保留**：支持标题、列表、表格、代码块等核心格式
- **格式统一美观**：转换后排版清晰、一致，提升可读性

![效果对比1](images/img_5_MTA4NGM5NzczNjB.png)

![效果对比2](images/img_33_ZjJiYzc5NmQyMjU.png)

## Markdown转Word的缺点

- 无法实现表格的合并单元格
- 无法实现高级样式

## 解决方案

### 在markdown中插入html表格实现合并单元格

![HTML表格示例](images/img_24_Y2M1YTRjYmEyZjB.png)

![合并单元格效果](images/img_10_MzZhNTk5NWYwZWY.png)

### 使用pandoc实现md2html2docx实现生成带合并单元格的docx

```bash
pandoc input.md -t html | pandoc -f html -t docx -o output.docx
```

### 实现效果

![最终效果](images/img_4_MGU3MDBhYmQ2OWQ.png)

## 参考提示词

```markdown
请根据以下规则，将后续提供的文件内容转换为一篇完整的 Markdown 文档：

1. **文档结构：**
   - 必须从一级标题（`#`）开始构建完整的标题层级。
   - 严格保留原文的章节结构与标题层级关系。

2. **列表格式：**
   - 全文**只能使用无序列表**。
   - **必须使用连字符加空格（`- `）作为列表项标记**。
   - **必须体现列表层级的缩进**：子层级使用 **2 个空格**进行缩进。
   - 示例：
     ```markdown
     - 第一项
       - 子项一
       - 子项二
     - 第二项
     ```

3. **表格处理：**
   - 所有表格**必须使用内联 HTML 代码编写**。
   - HTML 表格**必须实现所需的单元格合并功能**（使用 `rowspan` 或 `colspan` 属性）。
   - 确保表格在 Markdown 渲染器中能正确显示。

4. **输出要求：**
   - **请直接输出优化后的 Markdown 文档内容，并以 ```markdown 开头，将整个 Markdown 文档置于代码块中，不要包含任何解释性文字。**
```

## Pandoc高级功能

以下是关于 Pandoc 转换到 docx 时的高级功能说明，内容简洁整理自官方文档：

### 1. 使用自定义参考样式文件（--reference-doc）

Pandoc 可通过 --reference-doc 指定一个 .docx 文件作为样式模板，用于定义标题、正文、字体、页边距等格式。实际内容来自源文件（如 Markdown）。

**典型流程：**

1. 生成默认参考文件：

```bash
pandoc -o custom-reference.docx --print-default-data-file reference.docx
```

2. 用 Word 修改该文件中的样式（如 Heading 1–9、正文、引用等），保存为模板。
3. 转换时使用：

```bash
pandoc input.md -o output.docx --reference-doc=custom-reference.docx
```

若未指定，Pandoc 会使用用户数据目录下的 reference.docx（可通过 `pandoc --version` 查看路径）。

### 2. 自动生成目录与图表列表

需配合 -s/--standalone 使用：

- `--toc`：插入自动目录
- `--toc-depth=N`：限制目录层级（默认 3）
- `--lof`：生成图列表
- `--lot`：生成表列表

**示例：**

```bash
pandoc input.md -o output.docx --standalone --toc --toc-depth=4 --lof --lot
```

**注意：** Word 中需手动"更新字段"以显示正确页码。

### 3. 自定义样式与样式映射

- 在 Markdown 中使用 `{custom-style="StyleName"}` 指定样式：
  - `::: {custom-style="EmphasisBlock"} 自定义段落 :::`
  - `[文字]{custom-style="MyCharStyle"}`
- 从 DOCX 导入样式到 Markdown（保留样式名）：

```bash
pandoc input.docx -f docx+styles -t markdown
```

### 4. 高级模板控制（--template）

除样式外，可通过 --template 使用 OpenXML 模板控制文档结构，如封面、页眉页脚、固定内容等。配合以下参数：

- `--include-before-body=FILE` / `--include-after-body=FILE`：在正文前后插入内容
- `--variable KEY=VALUE`：设置模板变量（如 title、author）

**常用命令行参数总结：**

| 参数                   | 用途         |
| ---------------------- | ------------ |
| `-o output.docx`       | 输出文件     |
| `-s` 或 `--standalone` | 生成完整文档 |
| `--reference-doc=FILE` | 指定样式模板 |
| `--toc`                | 生成目录     |
| `--toc-depth=N`        | 目录深度     |
| `--lof`, `--lot`       | 图/表清单    |
| `--template=FILE`      | 使用结构模板 |
| `--variable KEY=VALUE` | 设置模板变量 |

**注意事项：**

- 目录需在 Word 中刷新字段才能显示页码；
- 自定义 reference.docx 中不要删除 Pandoc 依赖的样式名（如 Heading 1）；
- 列表/编号样式可能因未被识别而失效，建议基于默认 reference.docx 修改。

**支持能力总结：**

| 功能             | 支持 | 说明              |
| ---------------- | ---- | ----------------- |
| 参考样式文件     | ✔    | 控制格式与样式    |
| 自动生成目录     | ✔    | 通过 --toc        |
| 图/表清单        | ✔    | --lof / --lot     |
| 自定义元素样式   | ✔    | 使用 custom-style |
| OpenXML 结构模板 | ✔    | 控制文档结构      |

## 愿景：让 Pandoc 成为智能化文档套用与自动生成的核心引擎

Pandoc 当前主要作为格式转换工具，但其模板系统、过滤器机制和外部集成能力使其具备成为跨格式、跨场景的智能文档生成平台的潜力。结合模板、自动化流程与 AI，可构建一个标准化、模块化、可落地的文档自动化生态。

**核心目标：** 用户仅需提供大纲、关键数据或少量内容，系统即可自动生成符合组织规范的完整文档，无需手动调整 Word 样式。

### 典型工作流

#### 1. 统一模板库

建立标准化模板（如项目章程、周报、合同草案、学术论文等），每类模板包含：

- 预设样式（标题、摘要、结论等）
- 规范化元数据字段（作者、日期、版本、审批状态等）

#### 2. 参数化内容填充

用户通过 YAML、JSON 或表单提供结构化数据，Pandoc 渲染模板时注入变量，例如：

```yaml
title: "项目交付方案"
author: "作者名称"
project_number: "PRJ-2024-001"
```

#### 3. AI 辅助内容生成

调用 LLM（如 GPT、Claude）自动生成初稿、摘要、风险分析等内容，输出结构化 Markdown 或 JSON，再交由 Pandoc 格式化。

#### 4. 自动输出规范文档

生成的 Word 文档自动包含：

- 统一排版与样式
- 目录、图/表清单
- 自动编号、脚注、引用
- 封面、页眉页脚等企业标准元素

### 三大扩展方向

#### 1. 模板化体系：标准化与复用

- 支持参数化模板：通过 `--metadata-file` 注入变量
- `pandoc input.md --template=project.docx --metadata-file=data.yaml`
- 分离"样式"（reference.docx）与"结构"（模板变量 + 内容标记），提升灵活性与维护性

#### 2. 自动化工作流：融入企业系统

- 集成 CI/CD（如 GitHub Actions）：源文件更新后自动重建多格式文档
- 数据驱动：对接 Jira、Confluence、数据库等，从结构化数据生成报告

#### 3. AI 与 Pandoc 协同：内容生成 + 格式实现

- LLM 生成语义内容 → Pandoc 结构化排版 → 输出可审定 Word/PDF
- 已有实践：从自然语言提示一步生成带格式的完整文档

### 潜在能力（理论可行）

| 功能         | 描述                         | 实现途径                     |
| ------------ | ---------------------------- | ---------------------------- |
| 智能模板库   | 按文档类型分类，内置标准样式 | 模板 + 变量系统              |
| 自动字段填充 | 填写日期、作者、项目编号等   | LLM + Schema 约束            |
| 规则检查     | 验证段落规范、术语一致性     | 自定义验证脚本（Lua/Python） |
| 多格式输出   | 同时生成 DOCX / PDF / HTML   | Pandoc 原生支持              |

### 典型应用场景

**场景一：自动生成 SOW**

用户填写项目基本信息 → AI 生成背景与目标 → Pandoc 套用企业模板输出规范 Word。

**场景二：会议纪要自动化**

上传会议记录 → AI 提取要点 → Pandoc 生成含时间、参会人、编号的标准纪要。

**场景三：多源编译蓝皮书**

汇总多个 Markdown/YAML/JSON 文件 → 自动生成 Word + PDF + HTML 版本。

## 小结

Pandoc 的模板机制、数据驱动能力、过滤器扩展和跨格式支持，已构成智能文档生成平台的核心。通过与参数化模板、标准化流程及 AI 协同，可升级为企业级文档自动化中枢。
