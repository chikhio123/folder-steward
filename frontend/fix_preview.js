import fs from 'fs';

let content = fs.readFileSync('D:/Code/Folder Steward/frontend/src/pages/SettingsPage.tsx', 'utf8');

// Remove the old hint string from aiFields
content = content.replace(
  'hint: "Anthropic 需填 https://api.anthropic.com，OpenAI 中转需带 /v1 结尾（如填错可能拉取失败）", ',
  ''
);

// Add the dynamic preview display for llm_base_url
const renderFieldOld = `            {f.hint && (
              <p className="mt-2 text-[13px] text-indigo-500/80 font-medium">
                {f.hint}
              </p>
            )}`;

const renderFieldNew = `            {f.key === "llm_base_url" && (
              <div className="mt-2 px-3 py-2 bg-slate-100 rounded-lg border border-slate-200 text-xs font-mono text-slate-500 overflow-x-auto">
                <div><span className="text-slate-400">请求预览 (Chat):</span> {values[f.key] ? (values[f.key].replace(/\/$/, '') + (values[f.key].replace(/\/$/, '').endsWith('/v1') ? '' : '/v1') + '/chat/completions') : 'https://api.openai.com/v1/chat/completions'}</div>
                <div className="mt-1"><span className="text-slate-400">请求预览 (Models):</span> {values[f.key] ? (values[f.key].replace(/\/$/, '') + (values[f.key].replace(/\/$/, '').endsWith('/v1') ? '' : '/v1') + '/models') : 'https://api.openai.com/v1/models'}</div>
              </div>
            )}`;

content = content.replace(renderFieldOld, renderFieldNew);

fs.writeFileSync('D:/Code/Folder Steward/frontend/src/pages/SettingsPage.tsx', content);
