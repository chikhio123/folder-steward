# Folder Steward V3 设计稿

## 0. V3 定位

### 0.1 版本名称

**Folder Steward V3：智能整理与自然语言规则版**

### 0.2 一句话定位

在 V1 的安全文件操作链路和 V2 的内容索引/全文搜索基础上，V3 引入 AI 辅助能力：用户可以用自然语言描述整理意图，系统生成可审查、可修改、可确认的规则草案和整理方案，但 AI 不直接移动文件。

### 0.3 V3 核心目标

V3 只围绕一条主线展开：

```text
用户输入整理意图
  ↓
系统读取现有文件索引和内容摘要
  ↓
AI 生成规则草案 / 分类建议
  ↓
系统验证草案格式和路径边界
  ↓
用户预览整理方案
  ↓
用户确认后转成普通规则或整理建议
  ↓
沿用 V1 OperationService 执行真实文件操作
```

### 0.4 V3 不做什么

V3 暂不做以下功能：

```text
AI 直接移动文件
AI 直接删除文件
自动无人值守整理
OCR
文件夹实时监听
定时任务
插件系统
向量数据库
RAG 问答
多工作区
完整安装包发布
```

V3 的重点不是“让 AI 接管”，而是让 AI 生成可审查的整理草案。

---

## 1. V3 和 V1 / V2 的关系

V1 已经提供：

```text
扫描文件夹
建立文件索引
生成整理建议
执行移动 / 重命名
操作日志
回滚
Electron 桌面壳
```

V2 已经提供：

```text
内容提取
全文搜索
内容预览
内容关键词规则
stale 标记
rebuild-index 重新排队提取
```

V3 只新增：

```text
AI Rule Draft
AI Classification Suggestion
Organize Plan Preview
Feedback To Rule
LLM Provider Boundary
```

V3 不绕过 V1 / V2。

真实文件移动仍然只能走：

```text
OperationService
```

内容读取仍然来自：

```text
FileRecord + FileContent + SearchService
```

---

## 2. V3 核心设计原则

### 2.1 AI 只生成草案，不直接执行

AI 的输出只能进入以下状态：

```text
draft
```

AI 不能直接创建可执行操作。

AI 输出必须经过：

```text
schema validation
path safety validation
rule preview
user confirmation
```

之后才能转成：

```text
Rule
FileSuggestion
OrganizePlan
```

### 2.2 用户确认前不改变真实文件

V3 任何 AI 功能都不允许直接：

```text
move
rename
delete
rollback
archive
```

AI 只能给出：

```text
建议规则
建议分类
建议目标路径
建议理由
不确定项
```

### 2.3 现有规则系统仍是执行基础

AI 不是新的执行系统。

V3 的 AI 结果最后要落到已有结构：

```text
rules
file_suggestions
operation_logs
```

这样 V1 的安全链路仍然有效。

### 2.4 可解释优先于自动化

每条 AI 生成的规则或分类建议必须包含：

```text
reason
evidence
confidence
source_fields
```

例如：

```text
reason: 正文中出现“毕业论文”“系统设计”“开题报告”
evidence: file_content.text_content snippet
confidence: 0.82
source_fields: ["filename", "content"]
```

### 2.5 AI 可以建议新目录，但不能直接创建目录

V3 明确允许 AI 建议 `archive_root` 下尚不存在的新目录，因为智能整理的一个重要价值就是帮助用户形成新的归档结构。

但 AI 对目录没有执行权：

```text
AI 可以建议新目录
AI 不可以直接创建新目录
AI 不可以直接移动文件
AI 不可以绕过用户确认
```

AI 生成的目录建议必须经过系统校验，并被标记为：

```text
existing       目录已存在
proposed_new   目录不存在，但路径安全，可由用户确认后创建
invalid        路径不安全或不可使用；入库状态应为 failed
```

`proposed_new` 目录必须在整理方案预览中明确展示。只有用户确认整理方案后，后续执行链路才允许由 `OperationService` 在移动文件前创建目标目录。

`invalid` 目录不能转换成 `file_suggestions`。invalid 建议入库时应直接标记为 failed，并记录 validation_error，仅作为错误日志展示，不进入可执行计划。

### 2.6 AI 调用必须走后台队列和速率限制

V3 不允许前端请求直接同步触发大量 LLM 调用。

原因：

```text
用户可能一次选择几百或几千个文件
直接循环调用 LLM 会造成 N+1 请求风暴
容易触发 429 限流
可能造成不可控 Token 成本
前端请求也会长时间阻塞
```

所有批量 AI 能力必须走后台任务队列：

```text
前端创建 AI 任务
  ↓
ai_tasks 入库
  ↓
AI worker 按队列消费
  ↓
AIRateLimitService 控制并发与速率
  ↓
结果写入 draft / classification / plan / summary
  ↓
前端轮询任务状态
```

V3 默认限制：

```text
AI worker 并发数：1-2
每分钟最大请求数：可配置，默认 20
单次分类最多文件数：50
批量超过 50 个文件时自动分批入队
支持取消 pending 任务
失败任务可重试
```

V3 可以先用进程内队列实现，不引入 Redis / Celery。

### 2.7 新规则生效必须刷新整理建议

当 AI 规则草案被用户接受并转换成正式 `rules` 后，系统必须自动刷新整理建议。

推荐流程：

```text
draft accepted
  ↓
insert rules
  ↓
mark draft converted
  ↓
trigger SuggestionService.generate_suggestions()
  ↓
刷新 pending suggestions
```

如果刷新过程较重，可以进入后台任务；但不能要求用户自己再手动点击“重新生成建议”。

### 2.8 invalid 目录必须失败闭环

当 AI 输出的目录被 `DirectoryPolicyService` 判定为 invalid 时，系统不应把它作为待处理建议长期展示。

处理规则：

```text
directory_status = invalid
  ↓
status = failed
  ↓
记录 validation_error
  ↓
仅在错误日志或失败项中展示
  ↓
不能转 organize_plan_items
  ↓
不能转 file_suggestions
```


---

## 3. V3 功能范围

### 3.1 自然语言规则草案

用户可以输入：

```text
把毕业论文相关的文档都放到 University/Thesis
```

系统生成规则草案：

```json
{
  "name": "毕业论文相关文档",
  "rule_type": "content_keyword",
  "pattern": "毕业论文,开题报告,毕业设计,论文",
  "target_dir": "University/Thesis",
  "action": "move_to",
  "priority": 95,
  "reason": "用户希望将毕业论文相关文档归档到 University/Thesis"
}
```

用户可以：

```text
接受草案
修改草案
拒绝草案
预览规则影响范围
保存为正式规则
```

### 3.2 AI 分类建议

对于未命中现有规则或落入 Others 的文件，系统可以生成分类建议。

输入上下文：

```text
filename
extension
current_path
text_content preview
existing rules
archive_root
```

输出：

```json
{
  "file_id": 12,
  "suggested_target_dir": "Books/Philosophy",
  "directory_status": "proposed_new",
  "confidence": 0.78,
  "reason": "文件正文多次出现 Kant、纯粹理性批判、先验演绎等关键词",
  "evidence": [
    "……康德在先验演绎中……",
    "……纯粹理性批判……"
  ]
}
```

### 3.3 整理方案预览

V3 不只展示单条 suggestion，还要展示批量计划。

示例：

```text
本次 AI 整理计划：

University/Thesis
  12 个文件
  理由：正文或文件名包含论文、开题、毕业设计

Books/Philosophy
  8 个文件
  理由：包含 Kant、康德、纯粹理性批判

Finance/Receipts
  3 个文件
  理由：包含 invoice、receipt、发票

Uncertain
  6 个文件
  理由：内容不足或分类冲突
```

用户可以：

```text
接受整组
展开查看单个文件
修改目标目录
移出计划
确认后生成 file_suggestions
```

### 3.4 用户反馈转规则

当用户多次把某类文件改到同一目录时，系统可以提示：

```text
是否创建一条规则？
```

例如用户连续把包含“康德”的文件归档到：

```text
Books/Philosophy
```

系统生成规则草案：

```json
{
  "name": "康德相关文档",
  "rule_type": "content_keyword",
  "pattern": "康德,Kant,纯粹理性批判",
  "target_dir": "Books/Philosophy",
  "action": "move_to",
  "priority": 90
}
```

V3 不做复杂机器学习，只做：

```text
用户反馈 → 规则草案
```

### 3.5 AI 摘要，可选轻量功能

V3 可以对已提取正文的文件生成短摘要。

用途：

```text
帮助用户判断文件内容
辅助 AI 分类解释
搜索结果中展示摘要
```

限制：

```text
摘要只读 file_contents
摘要不参与真实文件操作
摘要失败不影响搜索和整理
```

---

## 4. V3 页面设计

### 4.1 AiRuleDraftPage

功能：

```text
输入自然语言整理意图
生成规则草案
展示结构化规则
展示规则影响范围
保存为正式规则
```

页面区域：

```text
PromptInput
DraftRuleCard
AffectedFilesPreview
ValidationResult
SaveRuleButton
```

### 4.2 SmartOrganizePage

功能：

```text
选择文件范围
运行 AI 分类建议
展示整理方案预览
用户确认后生成 file_suggestions
```

文件范围：

```text
全部未整理文件
当前搜索结果
指定扩展名
Others 目录候选
用户勾选文件
```

### 4.3 FeedbackReviewPanel

功能：

```text
展示用户最近的手动修改
识别可沉淀为规则的模式
生成规则草案
```

### 4.4 FileDetailPanel 增强

新增：

```text
AI 分类建议
AI 摘要
证据片段
接受/拒绝建议
```

---

## 5. 后端架构

### 5.1 新增目录结构

```text
backend/app/
  api/
    ai_rules.py
    smart_organize.py
    ai_summaries.py
    ai_tasks.py

  services/
    llm_provider_service.py
    ai_rule_draft_service.py
    ai_classification_service.py
    organize_plan_service.py
    feedback_rule_service.py
    prompt_context_service.py
    directory_policy_service.py
    ai_task_queue_service.py
    ai_rate_limit_service.py

  repositories/
    ai_rule_draft_repository.py
    ai_classification_repository.py
    organize_plan_repository.py
    file_summary_repository.py
    ai_task_repository.py

  models/
    ai_rule_draft.py
    ai_classification_suggestion.py
    organize_plan.py
    file_summary.py
    ai_task.py

  schemas/
    ai_rule_schema.py
    smart_organize_schema.py
    file_summary_schema.py
```

### 5.2 LLMProviderService

职责：

```text
统一封装 AI 调用
读取本地配置中的 provider
限制 prompt 长度
处理超时和失败
返回结构化 JSON
```

V3 支持抽象 provider，不绑定单一厂商：

```text
OpenAI-compatible API
Local LLM endpoint
Manual mock provider for testing
```

V3 可以先实现：

```text
mock provider
OpenAI-compatible provider
```

### 5.3 PromptContextService

职责：

```text
根据 file_id 组装 AI 上下文
限制内容长度
提取 filename / path / extension / content preview / existing rules
过滤敏感字段
```

上下文限制：

```text
单文件 content preview 默认最多 3000 字符
批量分类时每个文件最多 800 字符
单次请求最多 50 个文件
```

### 5.4 AIRuleDraftService

职责：

```text
接收自然语言意图
调用 LLM 生成规则草案
验证 JSON schema
验证 target_dir 安全
保存 draft
预览影响文件
```

### 5.5 AIClassificationService

职责：

```text
对文件生成分类建议
返回 target_dir / confidence / reason / evidence
不创建真实 suggestion
```

### 5.6 OrganizePlanService

职责：

```text
把多个 AI 分类建议合并成整理方案
按目标目录分组
识别低置信度文件
生成 plan preview
用户确认后转成 file_suggestions
```

### 5.7 FeedbackRuleService

职责：

```text
分析用户修改 suggestion target_path 的行为
识别重复模式
生成规则草案
```


### 5.8 DirectoryPolicyService

职责：

```text
校验 AI 生成的 suggested_target_dir
判断目录是否已存在
判断目录是否可作为新目录创建
为 AI 分类建议和整理方案标记 directory_status
```

校验规则：

```text
suggested_target_dir 必须是相对路径
禁止空路径
禁止 ..
禁止盘符，如 C:/
禁止以 / 或 \\ 开头
拼接 archive_root 后必须仍位于 archive_root 内
```

输出状态：

```text
existing
proposed_new
invalid
```


### 5.9 AITaskQueueService

职责：

```text
创建 AI 后台任务
按类型调度 rule_draft / classify / organize_plan / summary
记录任务状态、进度、错误信息和成本估计
避免前端请求直接阻塞 LLM 调用
```

任务类型：

```text
rule_draft
classification
organize_plan
summary
feedback_rule
```

状态：

```text
pending
running
completed
failed
cancelled
rate_limited
```

### 5.10 AIRateLimitService

职责：

```text
限制 AI 请求并发
限制单位时间请求数
限制单批文件数
限制 prompt 字符数
记录 estimated_tokens / actual_tokens / estimated_cost
处理 429 后退避重试
```

默认策略：

```text
max_concurrency = 1
max_requests_per_minute = 20
max_files_per_batch = 50
retry_after_seconds = 30
```

---

## 6. 数据库设计

### 6.1 ai_rule_drafts

```sql
CREATE TABLE ai_rule_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_prompt TEXT NOT NULL,
    name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    target_dir TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 90,
    reason TEXT,
    confidence REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    validation_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_ai_rule_drafts_status ON ai_rule_drafts(status);
```

状态：

```text
draft
validated
accepted
rejected
converted
failed
```

### 6.2 ai_classification_suggestions

```sql
CREATE TABLE ai_classification_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    suggested_target_dir TEXT NOT NULL,
    directory_status TEXT NOT NULL DEFAULT 'proposed_new',
    confidence REAL DEFAULT 0,
    reason TEXT,
    evidence_json TEXT,
    source_context_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
);

CREATE INDEX idx_ai_classification_file_id ON ai_classification_suggestions(file_id);
CREATE INDEX idx_ai_classification_status ON ai_classification_suggestions(status);
```

状态：

```text
pending
accepted
rejected
converted
stale
failed
```

### 6.3 organize_plans

```sql
CREATE TABLE organize_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    scope TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    summary_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_organize_plans_status ON organize_plans(status);
```

状态：

```text
draft
reviewing
accepted
rejected
converted
failed
```

### 6.4 organize_plan_items

```sql
CREATE TABLE organize_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    source_path TEXT NOT NULL,
    target_dir TEXT NOT NULL,
    target_path TEXT NOT NULL,
    directory_status TEXT NOT NULL DEFAULT 'proposed_new',
    confidence REAL DEFAULT 0,
    reason TEXT,
    evidence_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (plan_id) REFERENCES organize_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
);

CREATE INDEX idx_plan_items_plan_id ON organize_plan_items(plan_id);
CREATE INDEX idx_plan_items_status ON organize_plan_items(status);
```

状态：

```text
pending
accepted
rejected
modified
converted
failed
```

### 6.5 file_summaries

```sql
CREATE TABLE file_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    summary TEXT NOT NULL,
    llm_provider TEXT,
    model_name TEXT,
    source_content_hash TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_file_summaries_file_id ON file_summaries(file_id);
```

### 6.6 ai_tasks

所有 LLM 调用必须通过 `ai_tasks` 记录和调度，避免前端直接触发大量同步请求。

```sql
CREATE TABLE ai_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input_json TEXT,
    result_ref_type TEXT,
    result_ref_id INTEGER,
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    error_message TEXT,
    estimated_tokens INTEGER DEFAULT 0,
    actual_tokens INTEGER DEFAULT 0,
    estimated_cost REAL DEFAULT 0,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_type_status ON ai_tasks(task_type, status);
```

task_type：

```text
rule_draft
classification
organize_plan
summary
feedback_rule
```

状态：

```text
pending
running
completed
failed
cancelled
rate_limited
```

### 6.7 AI stale 级联规则

AI 分类建议依赖文件名、路径和 `file_contents.text_content`。当文件内容变为 stale 时，旧 AI 建议必须同步过期。

建议通过数据库 trigger 或服务层级联实现：

```sql
CREATE TRIGGER IF NOT EXISTS idx_ai_classification_stale_on_content_update
AFTER UPDATE OF extract_status ON file_contents
WHEN new.extract_status = 'stale'
BEGIN
    UPDATE ai_classification_suggestions
    SET status = 'stale',
        updated_at = CURRENT_TIMESTAMP
    WHERE file_id = new.file_id
      AND status IN ('pending', 'accepted');
END;
```

语义：

```text
文件内容 stale → 旧 AI 分类建议 stale
stale 建议不能转换成 organize_plan_items
stale 建议不能转换成 file_suggestions
用户需要重新提取内容并重新生成 AI 建议
```

摘要也必须级联 stale：

```sql
CREATE TRIGGER IF NOT EXISTS idx_file_summary_stale_on_content_update
AFTER UPDATE OF extract_status ON file_contents
WHEN new.extract_status = 'stale'
BEGIN
    UPDATE file_summaries
    SET status = 'stale',
        updated_at = CURRENT_TIMESTAMP
    WHERE file_id = new.file_id
      AND status = 'completed';
END;
```

---

## 7. API 设计

### 7.1 生成规则草案

```http
POST /api/ai/rule-drafts
```

请求：

```json
{
  "prompt": "把毕业论文相关的文档都放到 University/Thesis",
  "archive_root": "D:/Archive"
}
```

响应：

```json
{
  "draft_id": 1,
  "name": "毕业论文相关文档",
  "rule_type": "content_keyword",
  "pattern": "毕业论文,开题报告,毕业设计,论文",
  "target_dir": "University/Thesis",
  "action": "move_to",
  "priority": 95,
  "reason": "用户希望将毕业论文相关文档归档到 University/Thesis",
  "confidence": 0.86,
  "status": "validated"
}
```

### 7.2 预览规则影响范围

```http
GET /api/ai/rule-drafts/{draft_id}/preview
```

响应：

```json
{
  "draft_id": 1,
  "matched_count": 12,
  "items": [
    {
      "file_id": 10,
      "filename": "开题报告.docx",
      "current_path": "D:/Downloads/开题报告.docx",
      "target_path": "D:/Archive/University/Thesis/开题报告.docx",
      "reason": "正文包含“开题报告”"
    }
  ]
}
```

### 7.3 接受规则草案

```http
POST /api/ai/rule-drafts/{draft_id}/accept
```

效果：

```text
把 ai_rule_drafts 转成正式 rules 记录
draft.status = converted
```

接受规则草案后，后端必须触发一次建议刷新：

```text
ai_rule_draft → rules
  ↓
SuggestionService.generate_suggestions()
  ↓
刷新 pending file_suggestions
```

如果文件数量较大，可以创建后台 refresh task，但不能让用户手动猜测还需要重新生成整理建议。


### 7.4 生成 AI 分类建议

```http
POST /api/ai/classify
```

请求：

```json
{
  "file_ids": [1, 2, 3],
  "archive_root": "D:/Archive"
}
```

响应：

```json
{
  "task_id": 12,
  "status": "pending",
  "queued_count": 3
}
```

说明：

```text
该接口只创建 AI 后台任务，不直接同步调用 LLM。
前端通过 /api/ai/tasks/{task_id} 查询进度。
```

### 7.5 创建整理方案

```http
POST /api/ai/organize-plans
```

请求：

```json
{
  "scope": "others",
  "archive_root": "D:/Archive",
  "min_confidence": 0.65
}
```

响应：

```json
{
  "task_id": 18,
  "status": "pending"
}
```

说明：

```text
创建整理方案是 AI 后台任务。
任务完成后会生成 organize_plan，再通过 GET /api/ai/organize-plans/{plan_id} 查询。
```

### 7.6 查询整理方案

```http
GET /api/ai/organize-plans/{plan_id}
```

### 7.7 确认整理方案并生成 suggestions

```http
POST /api/ai/organize-plans/{plan_id}/convert-to-suggestions
```

效果：

```text
accepted plan items → file_suggestions
plan.status = converted
```

真实文件移动仍然需要用户走：

```text
POST /api/operations/execute-suggestions
```

### 7.8 生成文件摘要

```http
POST /api/ai/files/{file_id}/summary
```

---

### 7.9 查询 AI 任务

```http
GET /api/ai/tasks/{task_id}
```

响应：

```json
{
  "id": 1,
  "task_type": "classification",
  "status": "running",
  "total_items": 120,
  "processed_items": 35,
  "estimated_tokens": 18000,
  "estimated_cost": 0.12,
  "error_message": null
}
```

### 7.10 取消 AI 任务

```http
POST /api/ai/tasks/{task_id}/cancel
```

说明：

```text
只能取消 pending 任务。
running 任务可以标记为 cancellation_requested，但不能强制中断正在进行的外部 API 请求。
```

---

## 8. AI 输出契约

### 8.1 规则草案 JSON Schema

AI 必须输出：

```json
{
  "name": "string",
  "rule_type": "extension | filename_keyword | content_keyword",
  "pattern": "comma,separated,keywords",
  "target_dir": "relative/path",
  "action": "move_to",
  "priority": 90,
  "reason": "string",
  "confidence": 0.0
}
```

禁止输出：

```text
绝对路径 target_dir
../ 路径
空 pattern
delete / remove 动作
直接 operation 指令
```

### 8.2 分类建议 JSON Schema

```json
{
  "file_id": 1,
  "suggested_target_dir": "Books/Philosophy",
  "directory_status": "proposed_new",
  "confidence": 0.78,
  "reason": "string",
  "evidence": ["string"]
}
```

要求：

```text
suggested_target_dir 必须是相对目录
directory_status 必须由后端 DirectoryPolicyService 生成或校正
confidence 必须在 0 到 1 之间
evidence 最多 3 条
reason 不超过 300 字
```

### 8.3 整理方案 JSON Schema

```json
{
  "title": "string",
  "groups": [
    {
      "target_dir": "University/Thesis",
      "file_ids": [1, 2, 3],
      "reason": "string"
    }
  ],
  "uncertain_file_ids": [9, 10]
}
```

---

## 9. 安全策略

### 9.1 AI 不能绕过 PathSafetyService

所有 AI 生成的路径都必须经过：

```text
PathSafetyService
```

尤其检查：

```text
target_dir 是否为相对路径
是否包含 ..
是否包含盘符
是否指向系统目录
最终 target_path 是否位于 archive_root 内
```


### 9.1.1 AI 目录建议策略

V3 允许 AI 建议 `archive_root` 下的新目录，但 AI 不允许直接创建目录。

AI 生成的 `suggested_target_dir` 必须经过 `DirectoryPolicyService` 校验，并被标记为：

```text
existing：目录已存在
proposed_new：目录不存在但路径安全
invalid：路径不安全或无法使用
```

整理方案预览必须明确展示将要创建的新目录：

```text
本次整理将创建 3 个新目录：
- Books/Philosophy
- University/Thesis
- Finance/Receipts
```

只有当用户确认整理方案后，`proposed_new` 目录才允许在后续 `OperationService` 执行移动时创建。

`invalid` 目录不能转成 `file_suggestions`。它应在入库时直接标记为 failed，并附带原因，例如“包含危险路径逃逸”或“不是 archive_root 下的相对目录”。前端只在错误日志或失败项中展示，不作为待确认建议停留在主列表。

### 9.2 AI 不能执行 OperationService

AI 服务层禁止调用：

```text
OperationService.execute_suggestions
OperationService.rollback_operation
shutil.move
os.remove
Path.unlink
```

AI 只能创建：

```text
ai_rule_drafts
ai_classification_suggestions
organize_plans
organize_plan_items
```

或在用户确认后转换成：

```text
rules
file_suggestions
```

### 9.3 Prompt 上下文限制

批量分类时必须限制上下文：

```text
单文件最多 800 字符正文
单次最多 50 个文件
总 prompt 不超过配置上限
```

### 9.4 隐私策略

V3 是本地文件工具，AI 请求可能包含文件名、路径和正文片段。

因此 UI 必须提示：

```text
AI 分类会把所选文件的文件名和内容片段发送给配置的 AI 服务。
```

用户必须可以选择：

```text
关闭 AI
只发送文件名
发送文件名 + 内容片段
使用本地模型 endpoint
```

### 9.5 失败策略

AI 调用失败时：

```text
不影响 V1/V2 功能
记录 error_message
draft / suggestion 标记 failed
用户可以重试
```

---

## 10. LLM Provider 设计

### 10.1 配置项

SettingsPage 增加：

```text
AI provider enabled
provider type
base_url
api_key
model_name
max_prompt_chars
max_files_per_batch
send_content_preview
```

### 10.2 Provider 类型

V3 支持：

```text
mock
openai_compatible
local_endpoint
```

第一阶段建议先实现：

```text
mock
openai_compatible
```

### 10.3 Mock Provider

Mock Provider 用于测试 UI 和流程，不调用真实 AI。

它可以根据关键词返回固定草案：

```text
毕业论文 → University/Thesis
康德 → Books/Philosophy
发票 → Finance/Receipts
简历 → Personal/Resume
```

这样可以先把 V3 主链路跑通。

---

## 11. 错误处理

### 11.1 AI 输出不是合法 JSON

处理：

```text
保存 raw_output
draft.status = failed
validation_error = "Invalid JSON"
```

### 11.2 AI 输出路径不安全

处理：

```text
draft.status = failed
validation_error = "Unsafe target_dir"
```

### 11.3 AI 置信度过低

处理：

```text
放入 Uncertain
不自动生成 file_suggestions
等待用户手动确认
```

### 11.4 文件内容 stale

如果 file_contents.extract_status = stale：

```text
默认不用于 AI 分类
提示用户重新提取
```

### 11.5 规则草案转换失败

处理：

```text
draft.status 保持 validated
记录 validation_error
不创建正式 rule
```

---

## 12. V3 里程碑

### Milestone 1：AI 配置、任务队列与 Mock Provider

目标：

```text
新增 AI settings
新增 ai_tasks 表
实现 AITaskQueueService
实现 AIRateLimitService
实现 LLMProviderService
实现 mock provider
不调用真实 AI
```

验收：

```text
前端能启用 mock AI
AI 请求会创建 ai_tasks
前端能查询任务进度
后端能返回固定规则草案
```

### Milestone 2：规则草案生成

目标：

```text
新增 ai_rule_drafts 表
新增 /api/ai/rule-drafts
实现规则草案 JSON 校验
实现 target_dir 安全校验
```

验收：

```text
用户输入自然语言后能生成规则草案
草案不会直接变成正式规则
```

### Milestone 3：规则影响范围预览与转正式规则

目标：

```text
预览草案会命中的文件
用户确认后转成 rules
```

验收：

```text
接受草案后，规则出现在 Rules 页面
SuggestionService 能使用该规则
```

### Milestone 4：AI 分类建议

目标：

```text
新增 ai_classification_suggestions
对指定文件生成 target_dir 建议
保存 reason / evidence / confidence
通过 DirectoryPolicyService 标记 directory_status
```

验收：

```text
AI 分类结果能展示在 FileDetailPanel 或 SmartOrganizePage
```

### Milestone 5：整理方案预览

目标：

```text
新增 organize_plans
按 target_dir 分组展示整理方案
支持低置信度 Uncertain 分组
明确展示 proposed_new 新目录
阻断 invalid 目录转换
```

验收：

```text
用户能看到批量整理计划，但文件不会被移动
```

### Milestone 6：计划转 suggestions

目标：

```text
用户确认 plan 后生成 file_suggestions
沿用 V1 执行整理
```

验收：

```text
plan items 转成 suggestions 后，仍需用户执行 OperationService
```

### Milestone 7：用户反馈转规则

目标：

```text
分析用户手动修改 target_path 的行为
生成规则草案
```

验收：

```text
系统能提示“是否把这个整理习惯保存为规则”
```

### Milestone 8：文件摘要

目标：

```text
新增 file_summaries 表
对单文件生成简短摘要
保存 llm_provider / model_name / source_content_hash
详情页展示摘要
file_contents stale 时摘要也标记 stale
```

验收：

```text
摘要失败不影响搜索、规则和整理
```

---

## 13. V3 给 AI Worker 的开发约束

### 13.1 不允许做的事

```text
不允许 AI 直接移动文件
不允许 AI 直接删除文件
不允许 AI 调用 OperationService
不允许跳过规则草案校验
不允许把 AI 输出直接写成正式 rule
不允许把 AI 分类直接写成 file_suggestions
不允许把 invalid 目录转成 file_suggestions
不允许隐藏 proposed_new 新目录创建信息
不允许发送完整大文件正文给 AI
不允许默认启用外部 AI provider
不允许前端请求直接同步触发批量 LLM 调用
不允许绕过 ai_tasks 和 rate limit
```

### 13.2 必须遵守的边界

```text
OperationService 仍是唯一真实文件操作入口
PathSafetyService 必须校验所有 AI 生成路径
AI 输出必须先落 draft / suggestion / plan
AI 目录建议必须标记 directory_status
AI 调用必须通过 ai_tasks 后台队列
用户确认后才能转换
V2 的 FileContent 是 AI 内容上下文来源
rules 仍是正式规则源
file_suggestions 仍是整理执行前置层
```

### 13.3 Review 重点

```text
AI 输出是否经过 schema validation
target_dir 是否为安全相对路径
directory_status 是否正确标记 existing / proposed_new / invalid
proposed_new 是否在预览中明确展示
用户是否明确确认
是否存在 AI 直接调用文件操作
prompt 是否泄漏过多正文
AI 批量任务是否限流、分批、可重试
文件 stale 后旧 AI 建议是否级联 stale
规则草案转正式规则后是否刷新 suggestions
失败时是否不影响 V1/V2
plan 转 suggestions 是否保留 operation 安全链路
```

---

## 14. V3 最终验收标准

V3 完成时，系统应满足：

```text
1. 用户可以配置 mock 或 OpenAI-compatible AI provider。
2. 用户可以用自然语言生成规则草案。
3. AI 规则草案必须经过校验和用户确认。
4. 草案可以预览影响文件范围。
5. 用户确认后，草案可以转成正式 rules。
6. 系统可以对文件生成 AI 分类建议。
7. AI 分类建议必须展示 reason / evidence / confidence。
8. 系统可以生成整理方案预览。
9. 整理方案必须明确展示 proposed_new 新目录。
10. invalid 目录不能转换成 file_suggestions。
11. 整理方案确认后只能生成 file_suggestions，不直接移动文件。
12. 所有真实文件操作仍然走 V1 OperationService。
13. 用户可以选择是否发送内容片段给 AI。
14. AI 调用失败不影响 V1/V2 功能。
15. 批量 AI 调用必须经过 ai_tasks 队列和速率限制。
16. file_summaries 必须能持久化摘要结果。
17. file_contents stale 后，旧 AI 分类建议和摘要必须级联 stale。
18. 规则草案转正式规则后，系统必须刷新整理建议。
19. invalid 目录建议必须标记 failed，不进入可执行计划。
```

---

## 15. V3 后续扩展入口

V3 完成后，可以进入：

```text
V4:
  OCR
  文件夹监听
  定时任务
  压缩包内容索引
  插件系统
  多工作区
  更完整的规则 JSON schema
  本地模型更深集成
```

V3 的价值在于把 AI 放进一个安全、可审查、可回滚的整理工作流里，而不是让 AI 直接接管文件系统。
