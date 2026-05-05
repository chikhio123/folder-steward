# Folder Steward V2 设计稿

## 0. V2 定位

### 0.1 版本名称

**Folder Steward V2：内容索引与搜索增强版**

### 0.2 一句话定位

在 V1 已经完成“扫描—索引—整理建议—执行—回滚”的基础上，V2 增加文件内容提取、全文搜索、内容预览、提取任务管理和更细的整理规则，让系统从“按文件名和扩展名整理”升级为“理解部分文件内容后再检索和辅助整理”。

### 0.3 V2 核心目标

V2 只围绕一条新主线展开：

```text
扫描已有文件索引
  ↓
对支持的文件类型提取正文
  ↓
建立全文搜索索引
  ↓
用户按关键词搜索文件内容
  ↓
查看命中文件、命中片段和提取状态
  ↓
基于内容关键词增强整理建议
```

### 0.4 V2 不做什么

V2 暂不做以下功能：

```text
AI 自动分类
OCR 图片识别
文件夹实时监听
定时扫描
多用户系统
云端同步
插件系统
真正的打包发布
复杂自然语言规则
```

V2 的重点不是“智能”，而是把内容处理链路做稳。

---

## 1. V2 和 V1 的关系

V1 已经解决：

```text
文件夹扫描
文件索引
重复文件检测
基础整理建议
执行移动
操作日志
回滚
Electron 桌面壳
```

V2 不推翻 V1，只在 V1 的边界上增加：

```text
内容提取 Extract
全文搜索 Search
内容预览 Preview
规则增强 Rules
任务状态 ExtractTask
```

V1 的核心实体继续保留：

```text
FileRecord
FileSuggestion
OperationLog
ScanTask
```

V2 新增实体：

```text
FileContent
ExtractTask
SearchIndex
RuleProfile
```

---

## 2. V2 功能范围

### 2.1 文件内容提取

V2 支持对以下文件类型提取文本：

```text
.txt
.md
.pdf
.docx
```

第一阶段建议优先级：

```text
1. txt / md
2. pdf
3. docx
```

暂不支持：

```text
图片 OCR
扫描版 PDF OCR
复杂 doc / xls / ppt 正文解析
压缩包内文件正文解析
```

### 2.2 内容提取任务

内容提取不应该阻塞扫描任务。

V2 增加独立的提取任务：

```text
用户扫描文件夹
  ↓
系统识别可提取文本的文件
  ↓
创建 extract_tasks
  ↓
后台逐个提取
  ↓
写入 file_contents
  ↓
更新 FTS 索引
```

提取失败时：

```text
记录错误
标记 failed
不影响文件索引
不影响整理功能
```

### 2.3 全文搜索

V2 使用 SQLite FTS5 建立本地全文索引。

搜索支持：

```text
按文件名搜索
按文件内容搜索
按扩展名筛选
按文件大小筛选
按修改时间筛选
按提取状态筛选
```

搜索结果展示：

```text
文件名
当前路径
文件类型
修改时间
命中片段
匹配来源：filename / content
提取状态
```

### 2.4 文件内容预览

V2 不做完整阅读器，只做轻量预览。

支持：

```text
txt / md：显示文本前若干字符
pdf / docx：显示提取出的纯文本
```

预览限制：

```text
默认只展示前 5000 字符
可以点击“加载更多”
不保留复杂格式
不渲染 PDF 原版页面
```

### 2.5 内容增强整理建议

V1 的整理建议主要依赖：

```text
文件名关键词
扩展名
默认规则
```

V2 增加内容关键词判断：

```text
如果正文包含“论文 / 开题 / 毕业设计”
→ University/Thesis

如果正文包含“发票 / invoice / receipt / 税号”
→ Finance/Receipts

如果正文包含“康德 / Kant / 纯粹理性批判”
→ Books/Philosophy

如果正文包含“简历 / resume / curriculum vitae”
→ Personal/Resume
```

优先级建议：

```text
用户自定义规则 > 文件名关键词规则 > 内容关键词规则 > 扩展名规则 > 默认规则
```

### 2.6 规则配置增强

V2 增加可编辑规则配置。

支持规则类型：

```text
extension
filename_keyword
content_keyword
size_range
modified_time_range
```

规则动作：

```text
move_to
tag
ignore
```

V2 暂不做复杂条件组合。

### 2.7 提取状态管理

前端需要能看到：

```text
未提取
等待中
提取中
已完成
提取失败
跳过：不支持的文件类型
跳过：文件过大
```

用户可以：

```text
重新提取单个文件
批量重新提取失败文件
清空提取内容
```

---

## 3. V2 页面调整

### 3.1 DashboardPage

新增统计：

```text
已提取内容文件数
待提取文件数
提取失败文件数
FTS 索引文件数
最近提取任务
```

### 3.2 FileListPage

新增字段：

```text
内容提取状态
是否可搜索内容
标签
```

新增操作：

```text
查看内容预览
重新提取内容
打开所在目录
```

### 3.3 SearchPage

V2 新增页面：

```text
SearchPage
```

功能：

```text
输入关键词
选择搜索范围：文件名 / 内容 / 全部
筛选扩展名
筛选提取状态
展示命中片段
点击打开文件详情
```

搜索结果示例：

```text
Kant_CPR.pdf
路径：D:/Archive/Books/Philosophy/Kant_CPR.pdf
命中：……在先验演绎中，康德试图说明范畴如何能够……
匹配来源：content
```

### 3.4 FileDetailPanel

展示：

```text
基础元数据
当前路径
Hash
重复状态
内容提取状态
正文预览
相关整理建议
操作历史
```

### 3.5 SettingsPage

新增设置项：

```text
是否自动提取文本
最大提取文件大小
PDF 提取最大页数
预览最大字符数
是否启用内容关键词规则
是否启用 FTS 搜索
```

---

## 4. 后端架构调整

### 4.1 新增目录结构

```text
backend/app/
  api/
    search.py
    extract_tasks.py
    file_contents.py
    rules.py

  services/
    extract_service.py
    text_extractors/
      base.py
      txt_extractor.py
      markdown_extractor.py
      pdf_extractor.py
      docx_extractor.py
    search_service.py
    rule_engine_service.py

  repositories/
    file_content_repository.py
    extract_task_repository.py
    rule_repository.py

  models/
    file_content.py
    extract_task.py
    rule.py

  schemas/
    search_schema.py
    extract_task_schema.py
    file_content_schema.py
    rule_schema.py
```

### 4.2 ExtractService

职责：

```text
识别可提取文件
创建提取任务
调度提取任务
调用具体 extractor
保存 file_contents
更新 FTS 索引
记录失败原因
```

关键方法：

```python
create_extract_tasks(file_ids: list[int] | None) -> int
run_extract_task(task_id: int) -> None
extract_file(file_record: FileRecord) -> ExtractResult
retry_failed_tasks() -> int
```

### 4.3 TextExtractor

抽象接口：

```python
class TextExtractor:
    supported_extensions: set[str]

    def extract(self, path: Path) -> ExtractResult:
        ...
```

返回：

```python
class ExtractResult:
    text: str
    metadata: dict
    warnings: list[str]
```

### 4.4 SearchService

职责：

```text
执行全文搜索
生成命中片段
合并文件名搜索和内容搜索
处理分页
```

关键方法：

```python
search(query: str, scope: str, filters: SearchFilters) -> SearchResult
rebuild_index(file_id: int | None = None) -> None
```

### 4.5 RuleEngineService

V2 把整理建议规则从硬编码逐步迁出。

职责：

```text
加载规则列表
按 priority 匹配规则
返回目标目录和原因
处理内容关键词规则
```

关键方法：

```python
match(file_record: FileRecord, content: FileContent | None) -> RuleMatch
build_target_path(file_record: FileRecord, match: RuleMatch) -> Path
```

---

## 5. 数据库设计

### 5.1 file_contents

```sql
CREATE TABLE file_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    text_content TEXT,
    text_length INTEGER DEFAULT 0,
    extractor_type TEXT NOT NULL,
    extract_status TEXT NOT NULL,
    error_message TEXT,
    extracted_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (file_id) REFERENCES file_records(id)
);

CREATE UNIQUE INDEX idx_file_contents_file_id ON file_contents(file_id);
CREATE INDEX idx_file_contents_status ON file_contents(extract_status);
```

状态：

```text
pending
running
completed
failed
skipped
stale
```

### 5.2 extract_tasks

```sql
CREATE TABLE extract_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (file_id) REFERENCES file_records(id)
);

CREATE INDEX idx_extract_tasks_file_id ON extract_tasks(file_id);
CREATE INDEX idx_extract_tasks_status ON extract_tasks(status);
```

状态：

```text
pending
running
completed
failed
cancelled
skipped
```

### 5.3 file_content_fts

```sql
CREATE VIRTUAL TABLE file_content_fts USING fts5(
    file_id UNINDEXED,
    filename,
    current_path,
    text_content,
    tokenize='unicode61'
);
```

### 5.4 rules

```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    target_dir TEXT,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 100,
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_rules_enabled_priority ON rules(enabled, priority);
```

rule_type：

```text
extension
filename_keyword
content_keyword
size_range
modified_time_range
```

action：

```text
move_to
tag
ignore
```

---

## 6. API 设计

### 6.1 创建提取任务

```http
POST /api/extract-tasks
```

请求：

```json
{
  "file_ids": [1, 2, 3],
  "mode": "missing_only"
}
```

mode：

```text
missing_only
failed_only
force
```

响应：

```json
{
  "created_count": 12,
  "skipped_count": 5
}
```

### 6.2 查询提取任务

```http
GET /api/extract-tasks?status=running&page=1&page_size=50
```

响应：

```json
{
  "items": [
    {
      "id": 1,
      "file_id": 12,
      "status": "completed",
      "error_message": null,
      "started_at": "2026-05-05T20:00:00",
      "finished_at": "2026-05-05T20:00:03"
    }
  ],
  "total": 1
}
```

### 6.3 获取文件内容

```http
GET /api/files/{file_id}/content
```

响应：

```json
{
  "file_id": 12,
  "extract_status": "completed",
  "text_length": 18320,
  "preview": "这里是提取出的前 5000 字符……",
  "extracted_at": "2026-05-05T20:00:03"
}
```

### 6.4 全文搜索

```http
GET /api/search?q=康德&scope=all&page=1&page_size=20
```

scope：

```text
filename
content
all
```

响应：

```json
{
  "items": [
    {
      "file_id": 12,
      "filename": "Kant_CPR.pdf",
      "current_path": "D:/Archive/Books/Philosophy/Kant_CPR.pdf",
      "extension": ".pdf",
      "match_source": "content",
      "snippet": "……康德在先验演绎中试图说明……",
      "score": -1.23
    }
  ],
  "total": 1
}
```

### 6.5 重建全文索引

```http
POST /api/search/rebuild-index
```

请求：

```json
{
  "file_id": null
}
```

响应：

```json
{
  "indexed_count": 120,
  "failed_count": 2
}
```

### 6.6 规则 API

```http
GET /api/rules
POST /api/rules
PATCH /api/rules/{rule_id}
DELETE /api/rules/{rule_id}
```

规则响应示例：

```json
{
  "id": 1,
  "name": "论文关键词",
  "rule_type": "content_keyword",
  "pattern": "毕业论文|开题报告|毕业设计",
  "target_dir": "University/Thesis",
  "action": "move_to",
  "priority": 10,
  "enabled": true
}
```

---

## 7. 内容提取策略

### 7.1 TXT / Markdown

实现方式：

```text
直接读取文本
尝试 utf-8
失败时尝试 gbk / latin-1
限制最大读取大小
```

### 7.2 PDF

推荐库：

```text
pypdf
```

策略：

```text
逐页提取文本
限制最大页数
跳过无文本页
记录页数 metadata
```

失败情况：

```text
加密 PDF
扫描版 PDF
损坏 PDF
权限错误
```

V2 不做 OCR。扫描版 PDF 标记为：

```text
skipped: no_extractable_text
```

### 7.3 DOCX

推荐库：

```text
python-docx
```

策略：

```text
提取段落文本
提取表格文本可以后置
保留简单换行
```

V2 暂不支持 `.doc`。

---

## 8. 全文搜索策略

### 8.1 为什么用 SQLite FTS5

V2 仍然是本地单机应用，SQLite FTS5 足够支撑轻量全文搜索。

优点：

```text
无需额外服务
跟现有 SQLite 兼容
部署简单
适合 Electron + FastAPI 本地应用
```

### 8.2 搜索分层

```text
filename LIKE 搜索
FTS 内容搜索
筛选条件过滤
```

scope = filename：

```text
只查 file_records.filename
```

scope = content：

```text
只查 file_content_fts
```

scope = all：

```text
合并 filename 和 content 结果
```

### 8.3 命中片段

SQLite FTS5 支持 snippet。

示例：

```sql
SELECT file_id,
       snippet(file_content_fts, 3, '[', ']', '...', 16) AS snippet
FROM file_content_fts
WHERE file_content_fts MATCH ?;
```

前端渲染时：

```text
不要直接 dangerouslySetInnerHTML 渲染未清洗 HTML
V2 建议后端返回纯文本 snippet
```

---

## 9. V2 安全策略

### 9.1 内容提取只读文件

ExtractService 只能读取文件，不允许移动、重命名、删除文件。

### 9.2 文件大小限制

默认限制：

```text
最大提取文件大小：50MB
最大 PDF 页数：300 页
最大保存文本长度：1,000,000 字符
预览默认长度：5000 字符
```

超过限制：

```text
extract_status = skipped
error_message = "file too large"
```

### 9.3 搜索输入处理

FTS 查询不能直接拼接用户输入。

必须：

```text
参数化查询
转义特殊 FTS 操作符
限制 query 长度
```

最大 query 长度建议：

```text
200 字符
```

---

## 10. V2 错误处理

### 10.1 提取失败

常见失败：

```text
文件被删除
文件被占用
权限不足
编码错误
PDF 损坏
DOCX 解析失败
文件过大
不支持的文件类型
```

处理：

```text
extract_task.status = failed / skipped
file_contents.extract_status = failed / skipped
error_message 记录原因
不影响文件索引和整理
```

### 10.2 FTS 更新失败

如果文本提取成功但 FTS 写入失败：

```text
file_contents 保留 completed
extract_task 标记 failed
error_message = "fts index update failed"
```

后续通过 rebuild-index 修复。

### 10.3 文件变动后内容过期

如果文件重新扫描发现：

```text
modified_at 变化
size_bytes 变化
sha256 变化
```

则应把旧内容标记为：

```text
stale
```

---

## 11. V2 里程碑

### Milestone 1：内容表与提取任务骨架

目标：

```text
新增 file_contents
新增 extract_tasks
新增 API /api/extract-tasks
新增提取状态展示
```

验收：

```text
可以对 txt/md 文件创建提取任务
任务完成后 file_contents 有文本
```

### Milestone 2：TXT / Markdown 提取

目标：

```text
实现 txt_extractor
实现 markdown_extractor
处理编码异常
限制文件大小
```

验收：

```text
txt/md 文件能提取正文
提取失败不影响文件列表
```

### Milestone 3：PDF / DOCX 提取

目标：

```text
接入 pypdf
接入 python-docx
处理损坏文件和无文本文件
```

验收：

```text
普通 PDF / DOCX 能提取正文
扫描版 PDF 不会导致任务崩溃
```

### Milestone 4：SQLite FTS 全文搜索

目标：

```text
建立 file_content_fts
提取完成后写入 FTS
新增 /api/search
新增 SearchPage
```

验收：

```text
搜索正文关键词能返回文件和命中片段
```

### Milestone 5：文件详情与内容预览

目标：

```text
新增 FileDetailPanel
展示内容预览
展示提取状态
支持重新提取单个文件
```

验收：

```text
用户能从文件列表打开详情并查看正文预览
```

### Milestone 6：内容关键词规则

目标：

```text
新增 rules 表
新增 rules API
SuggestionService 接入 RuleEngineService
支持 content_keyword 规则
```

验收：

```text
正文包含关键词的文件能生成更准确的整理建议
```

### Milestone 7：索引过期与重建

目标：

```text
文件变化后标记 stale
支持重新提取 stale 文件
支持 rebuild FTS index
```

验收：

```text
文件修改后不会继续使用旧正文误导搜索
```

---

## 12. V2 给 AI Worker 的开发约束

### 12.1 不允许做的事

```text
不允许引入 AI 分类
不允许引入 OCR
不允许在提取任务中移动文件
不允许全文搜索直接拼接 SQL
不允许因为单个文件提取失败中断整个批次
不允许在前端直接渲染未清洗 HTML
不允许把 PDF/DOCX 提取失败当作系统失败
```

### 12.2 必须遵守的边界

```text
文件操作仍归 OperationService
扫描仍归 ScanService
内容提取归 ExtractService
搜索归 SearchService
规则匹配归 RuleEngineService
数据库访问仍放 repositories
API 层只做参数接收和响应返回
```

### 12.3 Review 重点

```text
提取任务是否会阻塞扫描
提取失败是否可恢复
FTS 查询是否参数化
文件变动后旧内容是否会过期
大文件是否被限制
PDF/DOCX 异常是否被捕获
搜索结果是否正确分页
规则优先级是否确定
```

---

## 13. V2 最终验收标准

V2 完成时，系统应满足：

```text
1. 用户可以对已索引文件创建内容提取任务。
2. txt / md / pdf / docx 文件可以提取纯文本。
3. 提取任务有明确状态和错误信息。
4. 单个文件提取失败不影响其他文件。
5. 系统可以使用 SQLite FTS 搜索文件内容。
6. 搜索结果可以展示命中文件和命中片段。
7. 用户可以查看文件正文预览。
8. 文件内容变化后旧索引会标记过期或可重新提取。
9. 整理建议可以使用内容关键词规则。
10. V2 不引入 AI、OCR、实时监听等超范围功能。
```

---

## 14. V2 后续扩展入口

V2 完成后，可以自然进入：

```text
V3:
  AI 分类建议
  自然语言整理规则
  OCR
  文件夹监听
  摘要生成

V4:
  插件系统
  多工作区
  定时任务
  压缩包内容索引
  可视化文件关系
```

V2 的价值在于先把“本地内容理解基础设施”打稳。后面的 AI 分类和 OCR 都要依赖这层内容索引。
