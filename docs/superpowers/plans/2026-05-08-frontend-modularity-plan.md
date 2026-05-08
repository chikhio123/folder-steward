# Frontend Modularity Refactoring Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the React frontend into modular, testable units by splitting the monolithic API service and extracting state management and UI components from heavy pages.

**Architecture:** Domain-driven directory structure for API services. Extraction of business logic into custom hooks. Decomposition of large page components into smaller, specialized presentation components.

**Tech Stack:** React 19, Vite, TypeScript, React Query, Tailwind CSS

---

### Task 1: Modularize API Service - Base Client & System API

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\services\api\client.ts`
- Create: `D:\Code\Folder Steward\frontend\src\services\api\system.ts`
- Modify: `D:\Code\Folder Steward\frontend\src\services\api.ts`
- Test: `D:\Code\Folder Steward\frontend\tests\services\api\client.test.ts` (Mocked for TDD structure)

- [ ] **Step 1: Create the new API directories and client file**

```typescript
// D:\Code\Folder Steward\frontend\src\services\api\client.ts
export const BASE_URL = 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMsg = 'An error occurred';
    try {
      const errorData = await response.json();
      errorMsg = errorData.detail || errorMsg;
    } catch {
      // Ignore JSON parse error
    }
    throw new ApiError(response.status, errorMsg);
  }

  return response.json();
}
```

- [ ] **Step 2: Create System API module**

```typescript
// D:\Code\Folder Steward\frontend\src\services\api\system.ts
import { request } from './client';
import type { DashboardData, FileSearchParams } from '../../types';

export const getSettings = () => request<any>('/settings');
export const updateSettings = (settings: any) =>
  request<any>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });

export const searchFiles = (params: FileSearchParams) => {
  const query = new URLSearchParams();
  if (params.keyword) query.append('keyword', params.keyword);
  if (params.extension) query.append('extension', params.extension);
  if (params.status) query.append('status', params.status);
  if (params.skip !== undefined) query.append('skip', params.skip.toString());
  if (params.limit !== undefined) query.append('limit', params.limit.toString());
  
  return request<any>(`/search?${query.toString()}`);
};

export const getDashboard = () => request<DashboardData>('/dashboard');
```

- [ ] **Step 3: Remove extracted code from main api.ts and re-export**

```typescript
// Modify D:\Code\Folder Steward\frontend\src\services\api.ts
// Remove ApiError, request, BASE_URL, getSettings, updateSettings, searchFiles, getDashboard
// Add re-exports:
export * from './api/client';
export * from './api/system';
// Keep the rest of the old code for now
```

- [ ] **Step 4: Verify application still compiles**

Run: `npm run build` in frontend directory.
Expected: Build passes.

- [ ] **Step 5: Commit**

```bash
git add src/services/api/ src/services/api.ts
git commit -m "refactor(frontend): extract base client and system api services"
```

### Task 2: Modularize API Service - Files & AI

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\services\api\files.ts`
- Create: `D:\Code\Folder Steward\frontend\src\services\api\ai.ts`
- Modify: `D:\Code\Folder Steward\frontend\src\services\api.ts`

- [ ] **Step 1: Create Files API module**

```typescript
// D:\Code\Folder Steward\frontend\src\services\api\files.ts
import { request } from './client';

export const getFiles = (skip = 0, limit = 50, sortBy?: string, sortOrder?: string) => {
  let url = `/files?skip=${skip}&limit=${limit}`;
  if (sortBy) url += `&sort_by=${sortBy}`;
  if (sortOrder) url += `&sort_order=${sortOrder}`;
  return request<any>(url);
};

export const getFileContent = (fileId: number) =>
  request<any>(`/files/${fileId}/content`);
```

- [ ] **Step 2: Create AI API module**

```typescript
// D:\Code\Folder Steward\frontend\src\services\api\ai.ts
import { request } from './client';
import type { AiRuleDraftRequest, ClassificationRequest, OrganizePlanRequest } from '../../types';

export const createClassificationTasks = (requestData: ClassificationRequest) =>
  request<any>('/smart-organize/classify', {
    method: 'POST',
    body: JSON.stringify(requestData),
  });

export const getAiTask = (taskId: string) =>
  request<any>(`/ai-tasks/${taskId}`);

export const createOrganizePlan = (requestData: OrganizePlanRequest) =>
  request<any>('/smart-organize/plan', {
    method: 'POST',
    body: JSON.stringify(requestData),
  });

export const getOrganizePlanPreview = (planId: number) =>
  request<any>(`/smart-organize/plans/${planId}/preview`);

export const acceptOrganizePlan = (planId: number) =>
  request<any>(`/smart-organize/plans/${planId}/accept`, {
    method: 'POST',
  });

export const getAiSummaries = (skip = 0, limit = 50) =>
  request<any>(`/ai-summaries?skip=${skip}&limit=${limit}`);

export const generateSummary = (fileId: number) =>
  request<any>(`/ai-summaries/generate/${fileId}`, {
    method: 'POST',
  });

export const createRuleDraft = (requestData: AiRuleDraftRequest) =>
  request<any>('/ai-rules/draft', {
    method: 'POST',
    body: JSON.stringify(requestData),
  });
  
export const getExcludePaths = () =>
  request<string[]>('/settings/exclude-paths');

export const updateExcludePaths = (paths: string[]) =>
  request<any>('/settings/exclude-paths', {
    method: 'PUT',
    body: JSON.stringify(paths),
  });
```

- [ ] **Step 3: Update main api.ts**

```typescript
// Modify D:\Code\Folder Steward\frontend\src\services\api.ts
// Remove the corresponding functions
// Add re-exports:
export * from './api/files';
export * from './api/ai';
```

- [ ] **Step 4: Verify application still compiles**

Run: `npm run build` in frontend directory.
Expected: Build passes.

- [ ] **Step 5: Commit**

```bash
git add src/services/api/ src/services/api.ts
git commit -m "refactor(frontend): extract files and ai api services"
```

### Task 3: Extract Common Components (Pagination)

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\components\common\Pagination.tsx`
- Modify: `D:\Code\Folder Steward\frontend\src\pages\FileListPage.tsx`

- [ ] **Step 1: Create Pagination component**

```tsx
// D:\Code\Folder Steward\frontend\src\components\common\Pagination.tsx
import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  onPageChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  onPageChange,
}) => {
  return (
    <div className="flex items-center justify-between bg-white px-4 py-3 border-t border-gray-200 sm:px-6 mt-4 rounded-lg shadow-sm">
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-700">
            Total <span className="font-medium">{totalItems}</span> results
          </p>
        </div>
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
            >
              <span className="sr-only">Previous</span>
              <ChevronLeft className="h-5 w-5" aria-hidden="true" />
            </button>
            <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
              Page {currentPage} of {Math.max(1, totalPages)}
            </span>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages || totalPages === 0}
              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
            >
              <span className="sr-only">Next</span>
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Replace pagination in FileListPage**

Edit `D:\Code\Folder Steward\frontend\src\pages\FileListPage.tsx`:
1. Import Pagination: `import { Pagination } from '../components/common/Pagination';`
2. Replace the existing pagination div (the one with ChevronLeft/ChevronRight buttons at the bottom) with:
   `<Pagination currentPage={page} totalPages={data?.total_pages || 0} totalItems={data?.total || 0} onPageChange={setPage} />`

- [ ] **Step 3: Verify TypeScript builds**

Run: `tsc --noEmit` in frontend directory.
Expected: No errors related to Pagination.

- [ ] **Step 4: Commit**

```bash
git add src/components/common/ src/pages/FileListPage.tsx
git commit -m "refactor(frontend): extract reusable Pagination component"
```

### Task 4: Extract Custom Hooks for FileListPage

**Files:**
- Create: `D:\Code\Folder Steward\frontend\src\hooks\useFileList.ts`
- Modify: `D:\Code\Folder Steward\frontend\src\pages\FileListPage.tsx`

- [ ] **Step 1: Create useFileList hook**

```typescript
// D:\Code\Folder Steward\frontend\src\hooks\useFileList.ts
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFiles, searchFiles } from '../services/api';
import type { FileRecord } from '../types';

export const useFileList = () => {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState('');
  const [extension, setExtension] = useState('');
  const [sortBy, setSortBy] = useState('size');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  const pageSize = 50;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['files', page, keyword, extension, sortBy, sortOrder],
    queryFn: () => {
      const skip = (page - 1) * pageSize;
      if (keyword || extension) {
        return searchFiles({
          keyword,
          extension,
          skip,
          limit: pageSize
        });
      }
      return getFiles(skip, pageSize, sortBy, sortOrder);
    },
  });

  return {
    state: { page, keyword, extension, sortBy, sortOrder, selectedFile },
    actions: { setPage, setKeyword, setExtension, setSortBy, setSortOrder, setSelectedFile, refetch },
    query: { data, isLoading }
  };
};
```

- [ ] **Step 2: Update FileListPage to use the hook**

Edit `D:\Code\Folder Steward\frontend\src\pages\FileListPage.tsx`:
Replace all state (`useState`) and `useQuery` declarations at the top of the component with:
```typescript
import { useFileList } from '../hooks/useFileList';
// ... inside component:
const { state, actions, query } = useFileList();
const { page, keyword, extension, sortBy, sortOrder, selectedFile } = state;
const { setPage, setKeyword, setExtension, setSortBy, setSortOrder, setSelectedFile, refetch } = actions;
const { data, isLoading } = query;
```
*(Ensure all references match, you might need to adjust import paths)*

- [ ] **Step 3: Verify TypeScript builds**

Run: `tsc --noEmit` in frontend directory.
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add src/hooks/ src/pages/FileListPage.tsx
git commit -m "refactor(frontend): extract useFileList custom hook"
```