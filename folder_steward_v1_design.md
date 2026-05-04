# Folder Steward V1 设计稿

## 0. 项目概述

### 0.1 项目名称

**Folder Steward**

### 0.2 一句话定位

一个本地运行的文件夹整理工作台：扫描指定文件夹，建立文件索引，识别重复文件，按规则生成整理建议，用户确认后执行移动/重命名，并支持操作回滚。

### 0.3 V1 核心目标

V1 只解决一条主链路：

```text
选择/输入文件夹路径
  ↓
扫描文件
  ↓
建立文件索引
  ↓
检测重复文件
  ↓
按基础规则生成整理建议
  ↓
用户确认
  ↓
执行移动/重命名
  ↓
记录日志
  ↓
支持撤销
```

### 0.4 V1 不做什么

V1 暂不做以下功能：

```text
AI 自动分类
OCR 图片识别
PDF/Word 正文解析
全文检索
文件夹实时监听
定时扫描
多用户系统
云端同步
真实删除文件
复杂规则引擎
```

V1 的重点是把基础文件操作链路做稳，避免一开始把系统做散。

---

## 1. 设计原则

### 1.1 索引和整理分离

系统扫描文件夹后，只建立索引和建议，不直接移动文件。

```text
扫描阶段：只读文件
整理阶段：用户确认后才移动文件
```

### 1.2 默认安全

所有破坏性操作都要可预览、可确认、可撤销。

V1 不做真实删除。删除类建议统一转换为移动到回收目录。

```text
.folder_steward_trash/
```

### 1.3 单个文件失败不影响整体任务

扫描或移动过程中，某个文件失败时，只记录错误，不中断整个批处理。

### 1.4 所有真实文件操作必须留痕

移动、重命名、回滚都必须写入操作日志。

### 1.5 第一版规则简单明确

V1 只支持基础规则：

```text
按扩展名分类
按文件名关键词分类
重复文件检测
```

不做复杂条件组合。

---

## 2. V1 功能范围

### 2.1 文件夹扫描

用户输入一个本地文件夹路径，后端递归扫描其中的文件。

需要记录：

```text
文件名
原始路径
当前路径
扩展名
MIME 类型
文件大小
创建时间
修改时间
SHA-256 Hash
索引时间
文件状态
```

### 2.2 文件索引列表

前端展示已扫描文件列表。

支持基础筛选：

```text
按扩展名筛选
按文件名关键词搜索
按文件大小排序
按修改时间排序
按是否重复筛选
```

### 2.3 重复文件检测

通过以下条件判断重复：

```text
文件大小相同
SHA-256 相同
```

重复文件以分组形式展示。

V1 只生成“移动重复文件到 Duplicates 目录”的建议，不做自动删除。

### 2.4 整理建议生成

根据基础规则生成建议路径。

规则优先级：

```text
文件名关键词规则 > 扩展名规则 > 默认归档规则
```

示例：

```text
D:/Downloads/毕业论文最终版.docx
→ D:/Archive/University/Thesis/毕业论文最终版.docx

D:/Downloads/Kant_CPR.pdf
→ D:/Archive/Documents/PDF/Kant_CPR.pdf

D:/Downloads/photo.png
→ D:/Archive/Images/photo.png
```

### 2.5 整理建议预览

用户可以看到：

```text
原路径
建议目标路径
建议原因
置信度
是否存在冲突
```

用户可以：

```text
接受建议
拒绝建议
修改目标路径
批量执行已接受建议
```

### 2.6 执行整理

用户确认后，系统执行移动或重命名。

执行前必须二次校验：

```text
源文件是否仍然存在
目标路径是否可写
目标文件是否已存在
是否越过授权目录
```

### 2.7 操作日志

每次文件移动/重命名都记录日志。

记录内容：

```text
操作类型
源路径
目标路径
执行状态
错误信息
执行时间
是否可回滚
```

### 2.8 回滚操作

支持对 move / rename 操作执行反向恢复。

示例：

```text
原操作：
D:/Downloads/a.pdf → D:/Archive/PDF/a.pdf

回滚：
D:/Archive/PDF/a.pdf → D:/Downloads/a.pdf
```

---

## 3. 用户流程

### 3.1 首次扫描流程

```text
用户打开系统
  ↓
进入 Scan Page
  ↓
输入本地文件夹路径
  ↓
点击“开始扫描”
  ↓
前端显示扫描进度
  ↓
扫描完成后进入文件列表
```

### 3.2 生成整理建议流程

```text
用户进入 Suggestion Page
  ↓
点击“生成整理建议”
  ↓
后端读取 file_records
  ↓
应用基础分类规则
  ↓
生成 file_suggestions
  ↓
前端展示建议列表
```

### 3.3 执行整理流程

```text
用户勾选建议
  ↓
点击“执行整理”
  ↓
系统展示确认弹窗
  ↓
用户确认
  ↓
后端执行移动/重命名
  ↓
写入 operation_logs
  ↓
更新 file_records.current_path
  ↓
前端展示执行结果
```

### 3.4 回滚流程

```text
用户进入 Operation History
  ↓
选择一条可回滚操作
  ↓
点击“撤销”
  ↓
系统检查是否可回滚
  ↓
执行反向移动
  ↓
更新操作日志
  ↓
刷新文件索引
```

---

## 4. 技术架构

### 4.1 推荐技术栈

```text
Frontend:
  React + TypeScript + Tailwind

Backend:
  FastAPI + Python

Database:
  SQLite

Task:
  V1 使用后端内存任务管理
  V2 再考虑 Redis / Celery

File Operation:
  Python pathlib / shutil

Hash:
  hashlib.sha256

Packaging:
  本地启动脚本
  后期 Docker Compose
```

### 4.2 总体结构

```text
folder-steward/
  frontend/
    src/
      pages/
      components/
      services/
      types/
      utils/

  backend/
    app/
      api/
      services/
      models/
      schemas/
      repositories/
      workers/
      core/

  data/
    folder_steward.db

  README.md
```

### 4.3 前后端通信

```text
前端通过 HTTP 调用后端 API
扫描进度 V1 使用轮询
V2 再改 WebSocket
```

轮询频率建议：

```text
扫描任务运行中：每 1 秒请求一次任务状态
任务结束后：停止轮询
```

---

## 5. 前端设计

### 5.1 页面列表

```text
DashboardPage
ScanPage
FileListPage
SuggestionPage
DuplicatePage
OperationHistoryPage
SettingsPage
```

### 5.2 DashboardPage

展示系统概览：

```text
已索引文件总数
总文件大小
重复文件组数量
待处理建议数量
最近扫描任务
最近操作记录
```

### 5.3 ScanPage

功能：

```text
输入扫描路径
开始扫描
显示扫描进度
显示扫描状态
显示扫描错误摘要
跳转文件列表
```

页面核心组件：

```text
PathInput
ScanButton
ScanProgressBar
ScanStatusCard
ScanErrorList
```

### 5.4 FileListPage

展示文件索引列表。

表格字段：

```text
文件名
当前路径
扩展名
大小
修改时间
是否重复
状态
```

操作：

```text
搜索文件名
扩展名筛选
按大小排序
按修改时间排序
查看详情
打开所在目录
```

V1 可以先不做文件预览。

### 5.5 SuggestionPage

展示整理建议。

字段：

```text
文件名
当前路径
建议路径
建议原因
建议类型
状态
是否冲突
```

操作：

```text
接受
拒绝
修改目标路径
批量接受
执行已接受建议
```

### 5.6 DuplicatePage

重复文件分组展示。

字段：

```text
重复组 Hash
组内文件数量
每个文件路径
每个文件大小
修改时间
```

操作：

```text
选择保留文件
将其他文件生成移动建议
```

V1 不做自动删除。

### 5.7 OperationHistoryPage

展示操作历史。

字段：

```text
操作类型
源路径
目标路径
状态
执行时间
是否可回滚
```

操作：

```text
查看详情
撤销操作
```

### 5.8 SettingsPage

V1 设置项：

```text
默认归档目录
是否扫描隐藏文件
最大扫描文件大小
是否计算 Hash
是否跳过系统目录
```

---

## 6. 后端设计

### 6.1 后端目录结构

```text
backend/app/
  main.py

  api/
    scan_tasks.py
    files.py
    suggestions.py
    duplicates.py
    operations.py
    settings.py

  services/
    scan_service.py
    hash_service.py
    suggestion_service.py
    duplicate_service.py
    operation_service.py
    path_safety_service.py

  repositories/
    file_repository.py
    scan_task_repository.py
    suggestion_repository.py
    operation_log_repository.py
    settings_repository.py

  models/
    file_record.py
    scan_task.py
    file_suggestion.py
    operation_log.py
    app_setting.py

  schemas/
    scan_task_schema.py
    file_schema.py
    suggestion_schema.py
    operation_schema.py

  core/
    database.py
    config.py
    errors.py
```

### 6.2 ScanService

职责：

```text
创建扫描任务
递归扫描目录
提取文件基础信息
调用 HashService 计算 hash
写入 file_records
更新 scan_tasks 进度
记录扫描错误
```

关键方法：

```python
create_scan_task(root_path: str) -> ScanTask
run_scan(task_id: int) -> None
scan_file(path: Path) -> FileRecord
```

### 6.3 HashService

职责：

```text
计算文件 SHA-256
处理大文件分块读取
处理读取失败
```

关键方法：

```python
calculate_sha256(path: Path) -> str
```

分块大小建议：

```text
1MB 或 4MB
```

### 6.4 DuplicateService

职责：

```text
根据 size + sha256 查找重复文件
生成重复文件组
为重复文件生成整理建议
```

关键方法：

```python
find_duplicate_groups() -> list[DuplicateGroup]
create_duplicate_suggestions(group_id: str, keep_file_id: int) -> list[FileSuggestion]
```

### 6.5 SuggestionService

职责：

```text
读取 file_records
应用分类规则
生成 target_path
处理重名冲突
写入 file_suggestions
```

关键方法：

```python
generate_suggestions(root_path: str, archive_root: str) -> int
build_target_path(file: FileRecord) -> Path
resolve_path_conflict(target_path: Path) -> Path
```

### 6.6 OperationService

职责：

```text
执行移动/重命名
执行前安全校验
更新 file_records
写 operation_logs
支持回滚
```

关键方法：

```python
execute_suggestions(suggestion_ids: list[int]) -> OperationResult
move_file(source: Path, target: Path) -> OperationLog
rollback_operation(operation_id: int) -> OperationLog
```

### 6.7 PathSafetyService

职责：

```text
检查路径是否合法
阻止系统敏感目录
阻止路径逃逸
阻止危险覆盖
```

关键方法：

```python
validate_scan_root(path: Path) -> None
validate_move(source: Path, target: Path) -> None
is_system_sensitive_path(path: Path) -> bool
```

---

## 7. 数据库设计

### 7.1 file_records

```sql
CREATE TABLE file_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    current_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT,
    mime_type TEXT,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT,
    created_at TEXT,
    modified_at TEXT,
    indexed_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    last_error TEXT
);

CREATE INDEX idx_file_records_current_path ON file_records(current_path);
CREATE INDEX idx_file_records_extension ON file_records(extension);
CREATE INDEX idx_file_records_sha256 ON file_records(sha256);
CREATE INDEX idx_file_records_size_sha ON file_records(size_bytes, sha256);
```

### 7.2 scan_tasks

```sql
CREATE TABLE scan_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path TEXT NOT NULL,
    status TEXT NOT NULL,
    total_files INTEGER DEFAULT 0,
    scanned_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL
);
```

状态枚举：

```text
pending
running
completed
failed
cancelled
```

### 7.3 scan_errors

```sql
CREATE TABLE scan_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    error_message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 7.4 file_suggestions

```sql
CREATE TABLE file_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    suggestion_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    reason TEXT,
    confidence REAL DEFAULT 0,
    conflict_status TEXT DEFAULT 'none',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX idx_file_suggestions_file_id ON file_suggestions(file_id);
CREATE INDEX idx_file_suggestions_status ON file_suggestions(status);
```

建议类型：

```text
move
rename
move_duplicate
```

状态枚举：

```text
pending
accepted
rejected
executed
failed
```

冲突状态：

```text
none
target_exists
source_missing
invalid_target
```

### 7.5 operation_logs

```sql
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,
    file_id INTEGER,
    source_path TEXT NOT NULL,
    target_path TEXT,
    status TEXT NOT NULL,
    rollback_available INTEGER DEFAULT 1,
    executed_at TEXT NOT NULL,
    rollback_at TEXT,
    error_message TEXT
);

CREATE INDEX idx_operation_logs_file_id ON operation_logs(file_id);
CREATE INDEX idx_operation_logs_status ON operation_logs(status);
```

操作类型：

```text
move
rename
rollback
```

状态：

```text
success
failed
rolled_back
```

### 7.6 app_settings

```sql
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

V1 默认设置：

```text
archive_root
scan_hidden_files
max_file_size_for_hash
skip_system_directories
```

---

## 8. API 设计

### 8.1 创建扫描任务

```http
POST /api/scan-tasks
```

请求：

```json
{
  "root_path": "D:/Downloads"
}
```

响应：

```json
{
  "task_id": 1,
  "status": "pending"
}
```

### 8.2 查询扫描任务

```http
GET /api/scan-tasks/{task_id}
```

响应：

```json
{
  "task_id": 1,
  "root_path": "D:/Downloads",
  "status": "running",
  "total_files": 1000,
  "scanned_files": 320,
  "failed_files": 2,
  "started_at": "2026-05-04T20:00:00",
  "finished_at": null
}
```

### 8.3 查询扫描错误

```http
GET /api/scan-tasks/{task_id}/errors
```

响应：

```json
{
  "items": [
    {
      "file_path": "D:/Downloads/locked.pdf",
      "error_message": "Permission denied"
    }
  ]
}
```

### 8.4 查询文件列表

```http
GET /api/files?page=1&page_size=50&extension=.pdf&keyword=kant&duplicated=false
```

响应：

```json
{
  "items": [
    {
      "id": 1,
      "filename": "Kant_CPR.pdf",
      "current_path": "D:/Downloads/Kant_CPR.pdf",
      "extension": ".pdf",
      "size_bytes": 2048000,
      "sha256": "abc...",
      "modified_at": "2026-05-04T19:30:00",
      "status": "active"
    }
  ],
  "total": 1
}
```

### 8.5 查询重复文件组

```http
GET /api/duplicates
```

响应：

```json
{
  "groups": [
    {
      "sha256": "abc...",
      "size_bytes": 2048000,
      "count": 3,
      "files": [
        {
          "id": 1,
          "current_path": "D:/Downloads/a.pdf",
          "modified_at": "2026-05-04T19:30:00"
        }
      ]
    }
  ]
}
```

### 8.6 生成整理建议

```http
POST /api/suggestions/generate
```

请求：

```json
{
  "archive_root": "D:/Archive"
}
```

响应：

```json
{
  "created_count": 58,
  "skipped_count": 12
}
```

### 8.7 查询整理建议

```http
GET /api/suggestions?status=pending&page=1&page_size=50
```

响应：

```json
{
  "items": [
    {
      "id": 1,
      "file_id": 1,
      "suggestion_type": "move",
      "source_path": "D:/Downloads/Kant_CPR.pdf",
      "target_path": "D:/Archive/Documents/PDF/Kant_CPR.pdf",
      "reason": "PDF 文件，建议归档到 Documents/PDF",
      "confidence": 0.75,
      "conflict_status": "none",
      "status": "pending"
    }
  ],
  "total": 1
}
```

### 8.8 更新整理建议状态

```http
PATCH /api/suggestions/{suggestion_id}
```

请求：

```json
{
  "status": "accepted",
  "target_path": "D:/Archive/Books/Kant_CPR.pdf"
}
```

响应：

```json
{
  "id": 1,
  "status": "accepted"
}
```

### 8.9 执行整理建议

```http
POST /api/operations/execute-suggestions
```

请求：

```json
{
  "suggestion_ids": [1, 2, 3]
}
```

响应：

```json
{
  "success_count": 2,
  "failed_count": 1,
  "results": [
    {
      "suggestion_id": 1,
      "status": "success",
      "operation_id": 10
    },
    {
      "suggestion_id": 3,
      "status": "failed",
      "error_message": "Source file missing"
    }
  ]
}
```

### 8.10 查询操作日志

```http
GET /api/operations?page=1&page_size=50
```

响应：

```json
{
  "items": [
    {
      "id": 10,
      "operation_type": "move",
      "source_path": "D:/Downloads/a.pdf",
      "target_path": "D:/Archive/PDF/a.pdf",
      "status": "success",
      "rollback_available": true,
      "executed_at": "2026-05-04T20:10:00"
    }
  ],
  "total": 1
}
```

### 8.11 回滚操作

```http
POST /api/operations/{operation_id}/rollback
```

响应：

```json
{
  "operation_id": 10,
  "status": "rolled_back"
}
```

---

## 9. 基础整理规则

### 9.1 扩展名规则

```text
.pdf       → Documents/PDF
.doc/.docx → Documents/Word
.xls/.xlsx → Documents/Excel
.ppt/.pptx → Documents/PowerPoint
.md/.txt   → Notes
.png/.jpg/.jpeg/.webp/.gif → Images
.zip/.rar/.7z → Archives
.mp4/.mov/.avi → Videos
.py/.js/.ts/.java/.cpp/.c → Code
```

### 9.2 文件名关键词规则

```text
包含 “论文” / “毕业” / “开题” / “thesis”
→ University/Thesis

包含 “发票” / “invoice” / “receipt”
→ Finance/Receipts

包含 “简历” / “resume” / “cv”
→ Personal/Resume

包含 “康德” / “Kant” / “CPR”
→ Books/Philosophy
```

### 9.3 默认归档规则

如果没有命中关键词规则或扩展名规则：

```text
Others/{extension_without_dot}
```

示例：

```text
.abc → Others/abc
无扩展名 → Others/NoExtension
```

### 9.4 目标路径冲突处理

如果目标路径已存在：

```text
a.pdf
a (1).pdf
a (2).pdf
```

不允许覆盖已有文件。

---

## 10. 安全策略

### 10.1 禁止扫描的路径

V1 默认禁止扫描：

```text
Windows:
  C:/
  C:/Windows
  C:/Program Files
  C:/Program Files (x86)
  C:/Users/{user}/AppData

macOS:
  /
  /System
  /Library
  /private

Linux:
  /
  /bin
  /boot
  /dev
  /etc
  /proc
  /sys
  /usr
  /var
```

### 10.2 路径校验

所有路径操作必须经过 PathSafetyService。

必须检查：

```text
路径是否存在
路径是否为绝对路径
是否包含路径逃逸
是否命中系统敏感目录
目标目录是否可写
源文件是否仍存在
目标文件是否已存在
```

### 10.3 符号链接处理

V1 默认不跟随符号链接。

原因：

```text
避免扫描范围逃逸
避免循环扫描
避免误操作外部文件
```

### 10.4 删除策略

V1 不真实删除文件。

如果未来需要“删除重复文件”，实际执行：

```text
move file → .folder_steward_trash/
```

---

## 11. 错误处理

### 11.1 扫描错误

常见错误：

```text
文件无权限
文件被占用
文件路径过长
文件扫描中被删除
Hash 计算失败
```

处理策略：

```text
记录 scan_errors
增加 failed_files
继续扫描下一个文件
```

### 11.2 整理执行错误

常见错误：

```text
源文件不存在
目标路径不可写
目标文件已存在
跨盘移动失败
移动过程中被占用
```

处理策略：

```text
当前文件操作标记 failed
写 operation_logs
继续处理下一个 suggestion
最终返回成功/失败统计
```

### 11.3 回滚错误

常见错误：

```text
目标文件已经不存在
原路径已被其他文件占用
无权限写回原目录
```

处理策略：

```text
回滚失败时不修改原操作状态
记录错误信息
提示用户手动处理
```

---

## 12. V1 里程碑

### Milestone 1：项目骨架

目标：

```text
前端项目初始化
后端项目初始化
SQLite 连接
基础 API 跑通
```

验收：

```text
前端能访问后端 health check
数据库能创建表
```

### Milestone 2：文件夹扫描

目标：

```text
输入路径
创建扫描任务
递归扫描文件
写入 file_records
查询扫描进度
```

验收：

```text
扫描 D:/Downloads 后能在数据库看到文件记录
前端能显示扫描进度
```

### Milestone 3：文件列表

目标：

```text
分页查询文件
按扩展名筛选
按关键词搜索
按修改时间排序
```

验收：

```text
前端 FileListPage 能展示扫描结果
筛选和搜索可用
```

### Milestone 4：重复文件检测

目标：

```text
计算 SHA-256
按 size + sha256 分组
展示重复文件组
```

验收：

```text
两个相同文件能被识别为重复组
```

### Milestone 5：整理建议

目标：

```text
实现扩展名规则
实现关键词规则
生成 target_path
处理路径冲突
写入 file_suggestions
```

验收：

```text
PDF、图片、压缩包能生成不同归档建议
同名文件不会覆盖
```

### Milestone 6：执行整理

目标：

```text
接受/拒绝建议
执行移动
更新 current_path
写 operation_logs
```

验收：

```text
用户确认后文件被移动到目标目录
数据库路径同步更新
操作日志可查询
```

### Milestone 7：回滚

目标：

```text
根据 operation_log 执行反向移动
更新 file_records
标记 rollback_at
```

验收：

```text
移动后的文件可以一键撤销回原位置
```

### Milestone 8：安全加固

目标：

```text
敏感目录拦截
路径逃逸检测
符号链接跳过
移动前二次校验
```

验收：

```text
不能扫描 C:/Windows
不能通过 ../ 构造危险目标路径
```

---

## 13. 测试方案

### 13.1 单元测试

重点测试：

```text
HashService
PathSafetyService
SuggestionService
OperationService
DuplicateService
```

### 13.2 集成测试

测试链路：

```text
创建临时目录
写入测试文件
扫描目录
生成建议
执行移动
检查文件位置
执行回滚
检查文件恢复
```

### 13.3 边界测试

测试场景：

```text
空文件夹
无扩展名文件
同名文件冲突
重复文件
文件名包含中文
文件名包含特殊字符
扫描中途文件被删除
目标路径已存在
无权限文件
```

---

## 14. 给 AI Worker 的开发约束

### 14.1 不允许跳过的规则

```text
真实文件操作前必须做路径安全校验
所有移动/重命名必须写 operation_logs
不允许覆盖已有文件
不允许真实删除文件
扫描失败不能中断整个任务
V1 不引入 AI 分类
V1 不引入 OCR
V1 不引入全文检索
```

### 14.2 代码风格要求

```text
业务逻辑放 services
数据库访问放 repositories
API 层只做参数接收和响应返回
路径处理统一经过 PathSafetyService
文件操作统一经过 OperationService
不要在前端硬编码后端业务规则
```

### 14.3 Review 重点

```text
路径安全
文件移动是否可回滚
数据库路径和真实文件路径是否一致
批量执行是否支持部分失败
重复扫描是否会产生重复记录
目标路径冲突是否处理
异常是否被吞掉
```

---

## 15. V1 最终验收标准

V1 完成时，系统应满足：

```text
1. 用户可以输入本地文件夹路径并扫描。
2. 系统可以展示扫描到的文件列表。
3. 系统可以计算文件 hash 并识别重复文件。
4. 系统可以根据基础规则生成整理建议。
5. 用户可以接受、拒绝、修改整理建议。
6. 用户确认后，系统可以移动文件。
7. 系统可以记录所有移动操作。
8. 用户可以撤销 move / rename 操作。
9. 系统不会扫描明显危险的系统目录。
10. 系统不会直接删除文件。
11. 单个文件失败不会导致整个任务失败。
```

---

## 16. V1 后续扩展入口

V1 完成后，可以自然扩展：

```text
V2:
  PDF / Word 文本提取
  SQLite FTS 全文搜索
  文件内容摘要
  更细的规则配置

V3:
  AI 分类建议
  自然语言整理规则
  OCR
  文件夹监听

V4:
  插件系统
  多工作区
  定时任务
  可视化文件关系
```

V1 不需要为这些功能提前写完整架构，只需要保留清晰边界：

```text
扫描 Scanner
索引 FileRecord
建议 Suggestion
执行 Operation
规则 Rule
```

后续功能围绕这些边界扩展即可。
