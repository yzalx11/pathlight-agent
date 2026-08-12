<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { UploadFile } from 'element-plus';
import { ElMessage } from 'element-plus';
import { Briefcase, CheckCircle2, ClipboardCheck, FileText, KeyRound, Save, Send, Settings2, Upload, XCircle } from 'lucide-vue-next';

const API_BASE = 'http://127.0.0.1:8000';

type Resume = {
  id: number;
  filename: string;
  created_at: string;
  facts: Array<{
    id: number;
    fact_code: string;
    category: string;
    content: string;
    source_excerpt: string;
    status: string;
  }>;
};

type MatchResult = {
  score: number;
  recommendation: string;
  reason: string;
  matched: Array<{ requirement: string; evidence: Array<{ fact_code: string; content: string }> }>;
  missing: string[];
  greeting: string;
  fact_check: { passed: boolean; risks: string[] };
};

const health = ref<{ ok: boolean; has_deepseek_key: boolean } | null>(null);
const apiKey = ref('');
const settingsVisible = ref(false);
const resumes = ref<Resume[]>([]);
const selectedResumeId = ref<number | null>(null);
const jdText = ref('');
const matchResult = ref<MatchResult | null>(null);
const loading = ref(false);
const applications = ref<any[]>([]);
const preferences = ref({
  role_direction: '',
  cities: '',
  salary_floor: '',
  industries: '',
  work_mode: '',
  notes: '',
});
const applicationDraft = ref({
  company: '',
  position: '',
  jd_link: '',
  resume_version: '',
  status: 'draft',
  notes: '',
});

const selectedResume = computed(() => resumes.value.find((resume) => resume.id === selectedResumeId.value));

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

async function refresh() {
  health.value = await request('/health');
  resumes.value = await request('/resumes');
  applications.value = await request('/applications');
  const savedPreferences = await request<Record<string, string>>('/preferences');
  preferences.value = { ...preferences.value, ...savedPreferences };
  selectedResumeId.value = resumes.value[0]?.id ?? null;
}

async function saveKey() {
  await request('/settings/deepseek-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey.value }),
  });
  apiKey.value = '';
  await refresh();
  ElMessage.success('API Key 已保存');
  settingsVisible.value = false;
}

async function uploadResume(file: File) {
  loading.value = true;
  try {
    const form = new FormData();
    form.append('file', file);
    const resume = await request<Resume>('/resumes', { method: 'POST', body: form });
    resumes.value.unshift(resume);
    selectedResumeId.value = resume.id;
    ElMessage.success('简历已上传，候选事实已生成');
  } finally {
    loading.value = false;
  }
}

function handleResumeChange(uploadFile: UploadFile) {
  if (uploadFile.raw) {
    uploadResume(uploadFile.raw);
  }
}

async function runMatch() {
  if (!selectedResumeId.value) return;
  loading.value = true;
  try {
    const result = await request<MatchResult>('/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_id: selectedResumeId.value, jd_text: jdText.value }),
    });
    matchResult.value = result;
    applicationDraft.value.notes = result.recommendation;
  } finally {
    loading.value = false;
  }
}

async function savePreferences() {
  await request('/preferences', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences.value),
  });
  ElMessage.success('偏好已保存');
}

async function saveFact(fact: Resume['facts'][number], status = fact.status) {
  await request(`/facts/${fact.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      category: fact.category,
      content: fact.content,
      status,
    }),
  });
  fact.status = status;
  ElMessage.success(status === 'confirmed' ? '事实已确认' : status === 'rejected' ? '事实已排除' : '事实已保存');
}

async function saveApplication() {
  if (!matchResult.value) return;
  if (!applicationDraft.value.company || !applicationDraft.value.position) {
    ElMessage.warning('请先填写公司和岗位');
    return;
  }
  await request('/applications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company: applicationDraft.value.company,
      position: applicationDraft.value.position,
      jd_link: applicationDraft.value.jd_link,
      resume_version: applicationDraft.value.resume_version || selectedResume.value?.filename || '',
      greeting: matchResult.value.greeting,
      status: applicationDraft.value.status,
      notes: applicationDraft.value.notes || matchResult.value.recommendation,
    }),
  });
  await refresh();
  ElMessage.success('投递草稿已保存');
}

onMounted(refresh);
</script>

<template>
  <main class="shell">
    <aside class="sidebar">
      <div class="brand">
        <Briefcase :size="24" />
        <div>
          <h1>求职策略 Agent</h1>
          <p>本地 MVP 工作台</p>
        </div>
      </div>

      <section class="panel">
        <header>
          <Upload :size="18" />
          <h2>简历</h2>
        </header>
        <el-upload :auto-upload="false" :show-file-list="false" :on-change="handleResumeChange">
          <el-button :loading="loading">上传 PDF / DOCX</el-button>
        </el-upload>
        <el-select v-model="selectedResumeId" placeholder="选择简历">
          <el-option v-for="resume in resumes" :key="resume.id" :label="resume.filename" :value="resume.id" />
        </el-select>
      </section>

      <section class="panel">
        <header>
          <Settings2 :size="18" />
          <h2>求职偏好</h2>
        </header>
        <el-input v-model="preferences.role_direction" placeholder="目标方向，如 Agent 应用 / 后端" />
        <el-input v-model="preferences.cities" placeholder="城市，如 上海 / 杭州 / 远程" />
        <el-input v-model="preferences.salary_floor" placeholder="薪资底线" />
        <el-input v-model="preferences.industries" placeholder="行业偏好" />
        <el-input v-model="preferences.work_mode" placeholder="工作模式" />
        <el-input v-model="preferences.notes" type="textarea" :rows="3" placeholder="其他偏好或避雷项" />
        <el-button :icon="Save" @click="savePreferences">保存偏好</el-button>
      </section>
    </aside>

    <section class="workspace">
      <div class="topline">
        <div class="topline-title">
          <h2>岗位匹配</h2>
          <span class="status">模型：{{ health?.has_deepseek_key ? '已配置' : '未配置' }}</span>
        </div>
        <div class="topline-actions">
          <el-tooltip content="设置" placement="bottom">
            <el-button circle :icon="Settings2" aria-label="打开设置" @click="settingsVisible = true" />
          </el-tooltip>
          <el-button type="primary" :icon="Send" :loading="loading" :disabled="!selectedResumeId || jdText.length < 10" @click="runMatch">
            分析 JD
          </el-button>
        </div>
      </div>

      <div class="grid">
        <section class="panel">
          <header>
            <FileText :size="18" />
            <h2>事实档案</h2>
          </header>
          <div v-if="selectedResume" class="facts">
            <article v-for="fact in selectedResume.facts" :key="fact.fact_code" class="fact">
              <div class="fact-meta">
                <strong>{{ fact.fact_code }}</strong>
                <el-tag :type="fact.status === 'confirmed' ? 'success' : fact.status === 'rejected' ? 'danger' : 'info'" size="small">
                  {{ fact.status === 'confirmed' ? '已确认' : fact.status === 'rejected' ? '已排除' : '候选' }}
                </el-tag>
              </div>
              <el-select v-model="fact.category" size="small">
                <el-option label="通用" value="general" />
                <el-option label="教育" value="education" />
                <el-option label="项目" value="project" />
                <el-option label="经历" value="experience" />
                <el-option label="技能" value="skill" />
              </el-select>
              <el-input v-model="fact.content" type="textarea" :rows="2" />
              <div class="fact-actions">
                <el-button size="small" :icon="Save" @click="saveFact(fact)">保存</el-button>
                <el-button size="small" type="success" :icon="CheckCircle2" @click="saveFact(fact, 'confirmed')">确认</el-button>
                <el-button size="small" type="danger" plain :icon="XCircle" @click="saveFact(fact, 'rejected')">排除</el-button>
              </div>
            </article>
          </div>
          <el-empty v-else description="先上传一份简历" />
        </section>

        <section class="panel">
          <header>
            <ClipboardCheck :size="18" />
            <h2>JD 原文</h2>
          </header>
          <el-input
            v-model="jdText"
            type="textarea"
            :rows="16"
            placeholder="粘贴岗位职责、任职要求、加分项等内容"
          />
        </section>
      </div>

      <section v-if="matchResult" class="panel result">
        <div class="result-head">
          <div>
            <p class="eyebrow">匹配结论</p>
            <h2>{{ matchResult.recommendation }} · {{ matchResult.score }}%</h2>
          </div>
        </div>
        <p>{{ matchResult.reason }}</p>
        <h3>可强调点</h3>
        <ul>
          <li v-for="item in matchResult.matched" :key="item.requirement">
            {{ item.requirement }}：{{ item.evidence.map((e) => `${e.fact_code} ${e.content}`).join('；') }}
          </li>
        </ul>
        <h3>缺口</h3>
        <p>{{ matchResult.missing.join('、') || '暂无明显缺口' }}</p>
        <h3>招呼语草稿</h3>
        <el-input v-model="matchResult.greeting" type="textarea" :rows="4" />
        <el-alert
          :type="matchResult.fact_check.passed ? 'success' : 'warning'"
          :title="matchResult.fact_check.passed ? '事实审查通过' : matchResult.fact_check.risks.join('；')"
          show-icon
        />
        <h3>保存投递草稿</h3>
        <div class="application-form">
          <el-input v-model="applicationDraft.company" placeholder="公司名称" />
          <el-input v-model="applicationDraft.position" placeholder="岗位名称" />
          <el-input v-model="applicationDraft.jd_link" placeholder="JD 链接" />
          <el-select v-model="applicationDraft.status">
            <el-option label="草稿" value="draft" />
            <el-option label="已投递" value="submitted" />
            <el-option label="待跟进" value="follow_up" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
          <el-input v-model="applicationDraft.notes" placeholder="备注" />
          <el-button type="primary" :icon="Save" @click="saveApplication">保存记录</el-button>
        </div>
      </section>

      <section class="panel">
        <header>
          <Briefcase :size="18" />
          <h2>投递记录</h2>
        </header>
        <el-table :data="applications" height="220">
          <el-table-column prop="company" label="公司" />
          <el-table-column prop="position" label="岗位" />
          <el-table-column prop="status" label="状态" />
          <el-table-column prop="jd_link" label="JD 链接" />
          <el-table-column prop="notes" label="备注" />
        </el-table>
      </section>
    </section>

    <el-dialog v-model="settingsVisible" title="设置" width="min(480px, calc(100vw - 32px))" :close-on-click-modal="false">
      <div class="settings-dialog">
        <div class="settings-dialog__heading">
          <KeyRound :size="18" />
          <div>
            <h3>DeepSeek API Key</h3>
            <p>密钥仅保存在当前系统的凭据库中。</p>
          </div>
        </div>
        <el-input v-model="apiKey" type="password" show-password placeholder="输入 API Key" autocomplete="off" />
        <span class="status">{{ health?.has_deepseek_key ? '当前已配置，可随时替换' : '当前未配置' }}</span>
      </div>
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!apiKey" @click="saveKey">保存 Key</el-button>
      </template>
    </el-dialog>
  </main>
</template>
