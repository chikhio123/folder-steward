# Folder Steward V4 架构师圆桌会议 - 最终定稿

*本文档由 Arch-Council 生成，融合了产品、数据、系统、安全、UX 及红队攻击的多维视角。*

## 1. Scope (功能范围)

### ✅ 核心引入 (In-Scope)
- **对话式规则生成 (Conversational UX)**：Magic Bar 输入框，通过自然语言生成结构化的整理草案。
- **语义聚类 (Semantic Grouping)**：基于文件正文和摘要，AI 自动发现潜在分组（不依赖写死的扩展名）。
- **自动标签 (Auto-Tagging)**：利用大模型读取正文，自动为文件写入 1-3 个元数据标签。
- **安全拦截防线**：防死循环、防 Token 耗尽、防跨库状态不一致。

### ❌ 明确暂缓与禁区 (Out-of-Scope)
- **绝对不碰 RAG（大文件嵌入式检索）**：不引入独立的 VectorDB（如 Milvus/Chroma），防范 SQLite 与外挂库状态脱节死锁。一切计算局限在本地 SQLite + 摘要层。
- **不碰 OCR**：暂不处理图片识别。
- **无后台文件监听 (Watchdog)**：防止系统级 IO 抖动引发海量影子任务导致 OOM。
- **无“真实静默自动执行”**：即便 AI 生成了绝佳的聚类和移动策略，最终必须落地为 `Pending Suggestion`，交由人类用户在沙盘 (Preview) 里一键 Click Confirm 才能物理挪动文件。

---

## 2. Architecture & Systems (架构与系统边界)

为了抵御红队指出的「系统级 DoS」和「异步状态断层」攻击，V4 采用严格解耦设计：

1. **流量指挥中心 (Traffic Cop)**
   - **交互优先级限流**：把 Token 预算池拆分为 `Interactive_Bucket` (用户直接发起的 Magic Bar 请求，优先级 P0) 和 `Background_Bucket` (后台慢慢消化自动打标签的任务，优先级 P3)。防止后台静默任务耗尽 Token 导致用户界面假死。
   - **任务防抖 (Debouncing)**：同一文件在 5 分钟内被修改 10 次，不会生成 10 个聚类任务，在入库时合并 `hash` 相同的冗余请求。

2. **安全隔离阀 (Safety Sandbox)**
   - **幻觉死循环防御**：任何 AI 输出的 `target_dir` 必须通过升级版的 `DirectoryPolicyService`。特别增加**「拓扑环路校验」**（如试图将文件夹移动到其子目录中），一经发现直接截断为 `Failed: Path Cycle Detected`。
   - **PII 脱敏墙**：任何发送给 LLM 的 `text_content` 摘要，必须在**后端**通过 `PIIRedactionService` 过一道正则清洗器，屏蔽手机号、银行卡号、以及常见密钥 (Token/Secret)。前端可以辅助提示，但绝对不能作为安全边界。
     ```text
     PIIRedactionService -> PromptContextService -> LLMProviderService
     ```

3. **Magic Bar Intent Contract (意图解析契约)**
   Magic Bar 不应该直接把自然语言丢给各服务猜，而是先解析为严格的 JSON 意图合约：
   ```json
   {
     "intent_type": "create_rule | generate_plan | tag_files | group_files | summarize_files",
     "scope": "current_search | selected_files | all_indexed | folder",
     "draft_only": true,
     "requires_confirmation": true,
     "raw_prompt": "把去年的工作文档按月份分类"
   }
   ```

---

## 3. Data Entities (核心数据结构更新)

在 V3 的基础上，补充以下表和关联：

### `tags` 和 `file_tags`
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT 'auto', -- 'auto' (AI 生成) / 'manual'
    color TEXT
);

CREATE TABLE file_tags (
    file_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'ai', -- 'ai' or 'manual'
    source_task_id INTEGER,
    reason TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'accepted', 'rejected', 'stale'
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY(file_id) REFERENCES file_records(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(file_id, tag_id)
);
```

### `semantic_groups` 和 `semantic_group_items`
不引入独立的向量数据库，直接基于 `file_summaries` 表，由 LLM 进行分批次聚合（Mini-batch clustering）：
```sql
CREATE TABLE semantic_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    summary_description TEXT,
    is_stale INTEGER DEFAULT 0
);

CREATE TABLE semantic_group_items (
    group_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    confidence REAL DEFAULT 0,
    reason TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'stale', 'rejected'
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY(group_id) REFERENCES semantic_groups(id) ON DELETE CASCADE,
    FOREIGN KEY(file_id) REFERENCES file_records(id) ON DELETE CASCADE,
    PRIMARY KEY(group_id, file_id)
);
```

**红队防御策略 (Stale 级联)：** 
当某个文档内容变更导致 `file_contents.extract_status = 'stale'` 时，触发器必须将 `file_tags` 和 `semantic_group_items` 中对应的该文件记录同步标记为 `stale`。
系统**不全局重算**聚类，而是把 `stale` 文档踢出当前的 `semantic_groups`，进入独立待分配区。这样永远不会因为一个字的变化导致一万个文件的组织结构发生雪崩（防余震）。

---

## 4. UX State Machine (前端交互状态机)

**渐进式披露沙盘 (Progressive Preview Sandbox)**
1. **[IDLE]**：Magic Bar 提供默认指令胶囊（“把去年的工作文档按月份分类”）。
2. **[PROCESSING]**：显示轻量级加载反馈（“正在嗅探文件语义联系...”），非阻塞当前页面浏览。
3. **[DRAFTING]**：弹出分层的 Cluster Card。如果是低置信度或者带“删除/丢进垃圾桶”倾向的操作，加上刺眼的警告红框。
4. **[CONFIRM/REVERT]**：确认后通过 `OperationService` 真实移动。并在历史记录支持基于原物理路径的原子回滚。

---

## 5. Milestones (开发里程碑拆解)

- **M1: 数据库与限流防线升级**：新增 `tags` 和 `semantic_groups` 体系，在 `AIRateLimitService` 引入**高低优双通道 Token 桶**机制。
- **M2: PII 安全清洗墙**：实现本地文本脱敏正则，组装并限制外发给大模型的上下文片段。
- **M3: Magic Bar 后端路由**：对接 `AIRuleDraftService` 支持处理极其复杂的自然语言分类意图，加强 `DirectoryPolicyService` 的反嵌套死循环。
- **M4: 渐进式智能预览板**：重塑前端界面，完成语义聚类的洋葱皮展示交互，打通草案确认的最后 100 米。
- **M5: Electron 应用打包封板**：配置 `electron-builder` 并封装为真实桌面可用程序。

---
*Conductor 结语：通过红蓝对抗与系统拆分，V4 方案已经剥离了昂贵的外部依赖与无限灾难可能，它兼具了大模型的“灵光乍现”与本地系统的“死板护栏”。随时准备拔锚起航！*