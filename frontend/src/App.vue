<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import type { UploadFile } from 'element-plus';
import { ElMessage } from 'element-plus';
import {
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  CircleAlert,
  ClipboardCheck,
  FileText,
  FolderOpen,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  Plus,
  Save,
  Send,
  Settings2,
  Sparkles,
  Upload,
  X,
} from 'lucide-vue-next';
import AgentDock from './components/ui/AgentDock.vue';

const desktopMode = '__TAURI_INTERNALS__' in window;
const API_BASE = `http://127.0.0.1:${desktopMode ? '8001' : '8000'}/api`;

type View = 'overview' | 'profile' | 'analysis' | 'applications' | 'settings';
type FactStatus = 'candidate' | 'confirmed' | 'rejected';
type ApplicationStatus = 'draft' | 'submitted' | 'follow_up' | 'interview' | 'offer' | 'rejected';

type Fact = {
  id: number;
  fact_code: string;
  category: 'general' | 'education' | 'project' | 'experience' | 'skill';
  content: string;
  source_excerpt: string;
  status: FactStatus;
};

type Resume = { id: number; filename: string; created_at: string; facts: Fact[] };
type Trace = { run_id: string; task_type: string; status: string; summary: string; created_at: string };
type Dashboard = {
  resumes_total: number;
  facts_confirmed: number;
  applications_total: number;
  follow_up_total: number;
  action_items: Array<{ job_id: number; title: string; company: string; status: JobStatus; action: string; next_action_at: string | null }>;
  recent_trace: Trace[];
};
type Application = { id: number; company: string; position: string; jd_link: string; resume_version: string; greeting: string; status: ApplicationStatus; notes: string; created_at: string };
type ModelSettings = { has_api_key: boolean; llm_provider: string; model: string };
type JobStatus = 'pending_review' | 'ready' | 'contacted' | 'waiting' | 'read_no_reply' | 'resume_sent' | 'assessment' | 'interview' | 'offer' | 'rejected' | 'archived';
type Job = {
  id: number;
  company: string;
  title: string;
  city: string;
  salary: string;
  experience: string;
  education: string;
  source: string;
  source_link: string;
  status: JobStatus;
  next_action_at: string | null;
  notes: string;
  ocr_text: string;
  jd_text: string;
  screenshots: Array<{ id: number; filename: string; ocr_text: string }>;
};
type MatchResult = {
  jd: { title_hint: string; confidence: string; keywords: string[]; responsibilities: string[]; requirements: string[] };
  score: number;
  recommendation: string;
  reason: string;
  matched: Array<{ requirement: string; evidence: Array<{ fact_code: string; content: string }> }>;
  missing: string[];
  preference_conflicts: string[];
  greeting: string;
  fact_check: { passed: boolean; risks: string[] };
  llm_insight?: {
    role_focus: string;
    day_to_day: string[];
    risks: string[];
    questions_to_clarify: string[];
    fact_codes: string[];
  } | null;
};

const currentView = ref<View>('overview');
const loading = ref(false);
const apiKey = ref('');
const health = ref<ModelSettings>({ has_api_key: false, llm_provider: 'deepseek', model: 'deepseek-v4-flash' });
const dashboard = ref<Dashboard>({ resumes_total: 0, facts_confirmed: 0, applications_total: 0, follow_up_total: 0, action_items: [], recent_trace: [] });
const resumes = ref<Resume[]>([]);
const selectedResumeId = ref<number | null>(null);
const applications = ref<Application[]>([]);
const jobs = ref<Job[]>([]);
const selectedJobId = ref<number | null>(null);
const jobScreenshotFiles = ref<UploadFile[]>([]);
const jdText = ref('');
const matchResult = ref<MatchResult | null>(null);
const preferences = ref({ role_direction: '', cities: '', salary_floor: '', industries: '', work_mode: '', notes: '' });
const applicationDraft = ref({ company: '', position: '', jd_link: '', status: 'draft' as ApplicationStatus, notes: '' });
const jobDraft = ref({ company: '', title: '', city: '', salary: '', experience: '', education: '', source_link: '', status: 'pending_review' as JobStatus, next_action_at: null as string | null, notes: '', jd_text: '' });
const pipoGradient = ref('');
let pipoFrame = 0;
let pipoStartedAt = 0;
let desktopConnectionAttempts = 0;

const selectedResume = computed(() => resumes.value.find((resume) => resume.id === selectedResumeId.value));
const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value));
const confirmedFacts = computed(() => selectedResume.value?.facts.filter((fact) => fact.status === 'confirmed').length ?? 0);
const currentStep = computed(() => {
  if (!selectedResume.value) return 1;
  if (!confirmedFacts.value) return 2;
  if (!matchResult.value) return 3;
  return 4;
});

const navItems: Array<{ id: View; label: string; icon: typeof LayoutDashboard }> = [
  { id: 'overview', label: '概览', icon: LayoutDashboard },
  { id: 'profile', label: '简历档案', icon: FolderOpen },
  { id: 'analysis', label: '岗位分析', icon: Sparkles },
  { id: 'applications', label: '投递记录', icon: BriefcaseBusiness },
  { id: 'settings', label: '设置', icon: Settings2 },
];

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof error.detail === 'string' ? error.detail : '请求未完成，请检查输入后重试。');
  }
  return response.json();
}

async function refresh() {
  try {
    const [settings, dashboardData, resumeData, applicationData, jobData, preferenceData] = await Promise.all([
      request<typeof health.value>('/settings'),
      request<Dashboard>('/dashboard'),
      request<Resume[]>('/resumes'),
      request<Application[]>('/applications'),
      request<Job[]>('/jobs'),
      request<typeof preferences.value>('/preferences'),
    ]);
    health.value = settings;
    dashboard.value = dashboardData;
    resumes.value = resumeData;
    applications.value = applicationData;
    jobs.value = jobData;
    preferences.value = preferenceData;
    selectedResumeId.value = selectedResumeId.value ?? resumeData[0]?.id ?? null;
  } catch (error) {
    if (desktopMode && desktopConnectionAttempts < 5) {
      desktopConnectionAttempts += 1;
      window.setTimeout(() => void refresh(), 500);
      return;
    }
    ElMessage.error(error instanceof Error ? error.message : '无法连接本地服务。');
  }
}

function openView(view: View) {
  currentView.value = view;
}

async function saveKey() {
  loading.value = true;
  try {
    await request('/settings/deepseek-key', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ api_key: apiKey.value }) });
    apiKey.value = '';
    await refresh();
    ElMessage.success('API Key 已安全保存到系统凭据库。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败。');
  } finally {
    loading.value = false;
  }
}

async function uploadResume(file: File) {
  loading.value = true;
  try {
    const form = new FormData();
    form.append('file', file);
    const resume = await request<Resume>('/resumes', { method: 'POST', body: form });
    await refresh();
    selectedResumeId.value = resume.id;
    ElMessage.success('简历已读取，请确认候选事实。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '上传失败。');
  } finally {
    loading.value = false;
  }
}

function handleResumeChange(uploadFile: UploadFile) {
  if (uploadFile.raw) uploadResume(uploadFile.raw);
}

async function uploadJobScreenshots(files: File[]) {
  loading.value = true;
  try {
    const form = new FormData();
    files.forEach((file) => form.append('files', file));
    const job = await request<Job>('/jobs/import-screenshots', { method: 'POST', body: form });
    await refresh();
    selectedJobId.value = job.id;
    jobDraft.value = {
      company: job.company,
      title: job.title,
      city: job.city,
      salary: job.salary,
      experience: job.experience,
      education: job.education,
      source_link: job.source_link,
      status: job.status,
      next_action_at: job.next_action_at,
      notes: job.notes,
      jd_text: job.jd_text,
    };
    jdText.value = job.jd_text;
    matchResult.value = null;
    ElMessage.success(`已导入 ${job.screenshots.length} 张截图，请确认职位信息。`);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '截图识别失败。');
  } finally {
    loading.value = false;
  }
}

function handleJobScreenshotChange(_: UploadFile, uploadFiles: UploadFile[]) {
  jobScreenshotFiles.value = uploadFiles;
}

function importSelectedJobScreenshots() {
  const files: File[] = [];
  for (const uploadFile of jobScreenshotFiles.value) {
    if (uploadFile.raw) files.push(uploadFile.raw);
  }
  if (files.length) uploadJobScreenshots(files);
}

function loadJobDraft(jobId: number | null) {
  const job = jobs.value.find((item) => item.id === jobId);
  if (!job) return;
  jobDraft.value = {
    company: job.company,
    title: job.title,
    city: job.city,
    salary: job.salary,
    experience: job.experience,
    education: job.education,
    source_link: job.source_link,
    status: job.status,
    next_action_at: job.next_action_at,
    notes: job.notes,
    jd_text: job.jd_text,
  };
  jdText.value = job.jd_text;
  applicationDraft.value.company = job.company;
  applicationDraft.value.position = job.title;
  applicationDraft.value.jd_link = job.source_link;
  matchResult.value = null;
}

function openJobFromAction(jobId: number) {
  selectedJobId.value = jobId;
  loadJobDraft(jobId);
  currentView.value = 'analysis';
}

async function saveJobDraft() {
  if (!selectedJobId.value) return;
  loading.value = true;
  try {
    const job = await request<Job>(`/jobs/${selectedJobId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobDraft.value),
    });
    jdText.value = job.jd_text;
    await refresh();
    ElMessage.success('职位草稿已保存。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存职位失败。');
  } finally {
    loading.value = false;
  }
}

async function saveFact(fact: Fact, status = fact.status) {
  try {
    await request(`/facts/${fact.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: fact.category, content: fact.content, status }) });
    fact.status = status;
    await refresh();
    ElMessage.success(status === 'confirmed' ? `${fact.fact_code} 已确认` : status === 'rejected' ? `${fact.fact_code} 已排除` : '事实已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败。');
  }
}

async function savePreferences() {
  try {
    await request('/preferences', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(preferences.value) });
    await refresh();
    ElMessage.success('求职偏好已保存。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败。');
  }
}

async function runMatch() {
  if (!selectedResumeId.value || jdText.value.length < 10) return;
  loading.value = true;
  try {
    jobDraft.value.jd_text = jdText.value;
    if (selectedJobId.value) {
      await request<Job>(`/jobs/${selectedJobId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobDraft.value),
      });
    }
    const result = await request<MatchResult>('/matches', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resume_id: selectedResumeId.value, jd_text: jdText.value }) });
    matchResult.value = result;
    applicationDraft.value.notes = result.recommendation;
    currentView.value = 'analysis';
    await refresh();
    ElMessage.success('岗位分析已完成。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '分析失败。');
  } finally {
    loading.value = false;
  }
}

async function saveApplication() {
  if (!matchResult.value || !applicationDraft.value.company || !applicationDraft.value.position) {
    ElMessage.warning('请填写公司名称和岗位名称。');
    return;
  }
  try {
    await request('/applications', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...applicationDraft.value, resume_version: selectedResume.value?.filename ?? '', greeting: matchResult.value.greeting, notes: applicationDraft.value.notes || matchResult.value.recommendation }) });
    applicationDraft.value = { company: '', position: '', jd_link: '', status: 'draft', notes: '' };
    await refresh();
    currentView.value = 'applications';
    ElMessage.success('投递记录已保存。');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败。');
  }
}

function statusLabel(status: ApplicationStatus) {
  return ({ draft: '草稿', submitted: '已投递', follow_up: '待跟进', interview: '面试中', offer: '已获 Offer', rejected: '已拒绝' } as const)[status];
}

function handleAgentMessage(message: string) {
  ElMessage.info(`已收到：${message.slice(0, 36)}${message.length > 36 ? '…' : ''}。岗位上下文问答将在下一步接入。`);
}

type PipoBlob = { rgb: string; x: number; y: number; fade: number; phase: number; phaseY: number };

function seededPhase(seed: number, index: number) {
  const mixed = Math.imul(seed ^ (index * 0x9e3779b9), 0x85ebca6b) >>> 0;
  return (mixed / 4_294_967_296) * Math.PI * 2;
}

const pipoBlobs: PipoBlob[] = [
  { rgb: '230, 176, 147', x: 68.1, y: 46.03, fade: 41.1, phase: seededPhase(1, 1), phaseY: seededPhase(11, 1) },
  { rgb: '163, 206, 255', x: 25.17, y: 75.99, fade: 44.6, phase: seededPhase(1, 2), phaseY: seededPhase(11, 2) },
  { rgb: '250, 249, 239', x: 53.11, y: 12.71, fade: 66.65, phase: seededPhase(1, 3), phaseY: seededPhase(11, 3) },
];

const pipoGrain = `url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.305'/></svg>")`;

function renderPipo(now: number) {
  const t = (now - pipoStartedAt) / 1000;
  const ph = t * 0.86;
  const amt = 0.72;
  const dir = 1;
  const spin = ph * dir;
  const layers = pipoBlobs.map((blob) => {
    const x = blob.x + (Math.sin(ph * 0.55 + blob.phase) - Math.sin(blob.phase)) * 14 * amt;
    const y = blob.y + (Math.sin(ph * 0.43 + blob.phaseY) - Math.sin(blob.phaseY)) * 14 * amt;
    const fade = blob.fade + (Math.cos(spin * 0.16 + blob.phase) - Math.cos(blob.phase)) * 1.5 * amt;
    const stopOne = fade * 0.25;
    const stopTwo = fade * 0.5;
    const stopThree = fade * 0.75;
    return `radial-gradient(circle at ${x}% ${y}%, rgba(${blob.rgb}, 1) 0%, rgba(${blob.rgb}, .844) ${stopOne}%, rgba(${blob.rgb}, .5) ${stopTwo}%, rgba(${blob.rgb}, .156) ${stopThree}%, rgba(${blob.rgb}, 0) ${fade}%)`;
  });
  pipoGradient.value = `${pipoGrain}, ${layers.join(', ')}`;
  pipoFrame = window.requestAnimationFrame(renderPipo);
}

onMounted(() => {
  void refresh();
  pipoStartedAt = performance.now();
  pipoFrame = window.requestAnimationFrame(renderPipo);
});

onBeforeUnmount(() => window.cancelAnimationFrame(pipoFrame));
</script>

<template>
  <main class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <span class="brand-mark"><Sparkles :size="19" /></span>
        <div><strong>Pathlight</strong><span>Career command centre</span></div>
      </div>

      <nav class="primary-nav" aria-label="主导航">
        <button v-for="item in navItems" :key="item.id" class="nav-item" :class="{ active: currentView === item.id }" @click="openView(item.id)">
          <component :is="item.icon" :size="18" /><span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="privacy-note"><KeyRound :size="15" /><span>数据仅保存在本机</span></div>
        <div class="model-status"><span :class="['status-dot', { ready: health.has_api_key }]" />{{ health.has_api_key ? '模型已配置' : '模型未配置' }}</div>
      </div>
    </aside>

    <section class="app-main" :style="{ '--pipo-gradient': pipoGradient }">
      <header class="app-header">
        <div class="header-title">
          <p class="eyebrow">PATHLIGHT / LOCAL CAREER OS</p>
          <h1>{{ ({ overview: '今天的求职工作', profile: '简历与事实档案', analysis: '岗位分析', applications: '投递记录', settings: '本地设置' } as const)[currentView] }}</h1>
        </div>
        <div class="header-actions">
          <span v-if="currentView !== 'settings'" class="toolbar-status"><span :class="['status-dot', { ready: health.has_api_key }]" />{{ health.has_api_key ? '模型已就绪' : '仅本地模式' }}</span>
          <el-select v-if="currentView !== 'settings'" v-model="selectedResumeId" class="resume-select" placeholder="选择简历">
            <el-option v-for="resume in resumes" :key="resume.id" :label="resume.filename" :value="resume.id" />
          </el-select>
          <el-button v-if="currentView !== 'settings'" type="primary" :icon="Plus" @click="openView('profile')">导入简历</el-button>
        </div>
      </header>

      <div class="workspace-scroll">
        <section v-if="currentView === 'overview'" class="view-stack overview">
          <section class="hero-panel">
            <div class="hero-copy">
              <p class="eyebrow">01 / TODAY'S SIGNAL</p>
              <h2>{{ currentStep === 1 ? '先建立可信的简历事实档案' : currentStep === 2 ? '确认可用于沟通的真实经历' : currentStep === 3 ? '导入一个想了解的职位' : '将你的研判转化为下一步行动' }}</h2>
              <p>{{ currentStep === 1 ? '从一份 PDF 或 DOCX 开始。Pathlight 只会使用由你确认过的事实。' : currentStep === 2 ? `当前简历有 ${selectedResume?.facts.length ?? 0} 条候选事实，确认后才会成为匹配与沟通的依据。` : currentStep === 3 ? '粘贴 JD，或一次导入多张 BOSS 职位截图。识别结果始终可先校对。' : '岗位洞察、沟通草稿和本地投递记录已经连成闭环。' }}</p>
              <el-button type="primary" size="large" :icon="currentStep === 1 ? Upload : currentStep === 2 ? Check : currentStep === 3 ? Send : BriefcaseBusiness" @click="openView(currentStep === 1 || currentStep === 2 ? 'profile' : currentStep === 3 ? 'analysis' : 'applications')">
                {{ currentStep === 1 ? '导入简历' : currentStep === 2 ? '确认事实' : currentStep === 3 ? '导入职位' : '查看投递记录' }}
              </el-button>
            </div>
            <ol class="workflow-steps" aria-label="求职工作流">
              <li v-for="(label, index) in ['简历', '事实', '职位', '行动']" :key="label" :class="{ done: currentStep > index + 1, current: currentStep === index + 1 }">
                <span>{{ index + 1 }}</span><strong>{{ label }}</strong>
              </li>
            </ol>
          </section>

          <section class="metric-grid" aria-label="本地数据概览">
            <article class="metric"><span>简历版本</span><strong>{{ dashboard.resumes_total }}</strong><small>本地保存</small></article>
            <article class="metric"><span>已确认事实</span><strong>{{ dashboard.facts_confirmed }}</strong><small>可引用证据</small></article>
            <article class="metric"><span>职位草稿</span><strong>{{ jobs.length }}</strong><small>待研判或跟进</small></article>
            <article class="metric"><span>待跟进</span><strong>{{ dashboard.follow_up_total }}</strong><small>需要行动</small></article>
          </section>

          <section class="surface action-queue">
            <div class="section-heading"><div><p class="eyebrow">NEXT ACTIONS</p><h2>现在处理什么</h2><p>只显示需要你确认、沟通或准备的职位。</p></div><BriefcaseBusiness :size="19" /></div>
            <div v-if="dashboard.action_items.length" class="action-list">
              <button v-for="item in dashboard.action_items" :key="item.job_id" class="action-item" @click="openJobFromAction(item.job_id)">
                <span class="action-status">{{ item.action }}</span>
                <span class="action-main"><strong>{{ item.title }}</strong><small>{{ item.company }}</small></span>
                <span class="action-date">{{ item.next_action_at ? new Date(item.next_action_at).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) : '待安排' }}</span>
                <ArrowUpRight :size="16" />
              </button>
            </div>
            <el-empty v-else description="导入并校对职位后，需要处理的事项会显示在这里。" :image-size="62" />
          </section>

          <section class="content-grid overview-grid">
            <article class="surface trace-card"><div class="section-heading"><div><p class="eyebrow">ACTIVITY</p><h2>最近活动</h2></div><ListChecks :size="19" /></div>
              <div v-if="dashboard.recent_trace.length" class="trace-list"><div v-for="trace in dashboard.recent_trace.slice(0, 5)" :key="trace.run_id" class="trace-item"><span class="trace-dot" /><div><strong>{{ trace.summary }}</strong><small>{{ new Date(trace.created_at).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit', month: 'numeric', day: 'numeric' }) }}</small></div></div></div>
              <el-empty v-else description="完成一次导入或分析后，活动会显示在这里。" :image-size="72" />
            </article>
            <article class="surface preparation-card"><div class="section-heading"><div><p class="eyebrow">READY CHECK</p><h2>本地准备状态</h2></div><CircleAlert :size="19" /></div>
              <div class="readiness"><div><span :class="['check-icon', { done: resumes.length > 0 }]"><Check :size="14" /></span><span>已导入简历</span></div><div><span :class="['check-icon', { done: confirmedFacts > 0 }]"><Check :size="14" /></span><span>已确认事实</span></div><div><span :class="['check-icon', { done: health.has_api_key }]"><Check :size="14" /></span><span>已配置模型 Key</span></div></div>
              <button class="quiet-link" @click="openView('settings')">打开本地设置 <ArrowUpRight :size="15" /></button>
            </article>
          </section>
        </section>

        <section v-else-if="currentView === 'profile'" class="view-stack">
          <section class="surface import-strip"><div><p class="eyebrow">RESUME SOURCE</p><h2>导入并沉淀事实档案</h2><p>支持 PDF、DOCX，文件不离开本机。</p></div><el-upload :auto-upload="false" :show-file-list="false" :on-change="handleResumeChange"><el-button type="primary" :icon="Upload" :loading="loading">导入 PDF / DOCX</el-button></el-upload></section>
          <section class="content-grid profile-grid">
            <article class="surface facts-surface"><div class="section-heading"><div><p class="eyebrow">FACT ARCHIVE</p><h2>候选事实</h2><p>确认后才会优先进入匹配与话术。</p></div><span class="count-badge">{{ selectedResume?.facts.length ?? 0 }}</span></div>
              <div v-if="selectedResume" class="fact-list"><article v-for="fact in selectedResume.facts" :key="fact.id" class="fact-row" :class="fact.status"><div class="fact-row__meta"><span class="fact-code">{{ fact.fact_code }}</span><span class="fact-status">{{ fact.status === 'confirmed' ? '已确认' : fact.status === 'rejected' ? '已排除' : '待确认' }}</span></div><el-select v-model="fact.category" size="small"><el-option label="通用" value="general" /><el-option label="教育" value="education" /><el-option label="项目" value="project" /><el-option label="经历" value="experience" /><el-option label="技能" value="skill" /></el-select><el-input v-model="fact.content" type="textarea" :rows="2" /><div class="fact-row__actions"><el-button size="small" :icon="Save" @click="saveFact(fact)">保存</el-button><el-button size="small" type="primary" plain :icon="CheckCircle2" @click="saveFact(fact, 'confirmed')">确认</el-button><el-button size="small" text type="danger" :icon="X" @click="saveFact(fact, 'rejected')">排除</el-button></div></article></div>
              <el-empty v-else description="导入简历后，在这里确认可用事实。" :image-size="90" />
            </article>
            <article class="surface preferences-surface"><div class="section-heading"><div><p class="eyebrow">PREFERENCES</p><h2>求职偏好</h2><p>它们会参与岗位建议，但不替代硬性要求。</p></div></div><div class="form-stack"><el-input v-model="preferences.role_direction" placeholder="目标方向，如 Agent 应用 / 后端" /><el-input v-model="preferences.cities" placeholder="目标城市，如 上海 / 杭州 / 远程" /><el-input v-model="preferences.salary_floor" placeholder="薪资底线" /><el-input v-model="preferences.industries" placeholder="行业偏好" /><el-input v-model="preferences.work_mode" placeholder="工作模式" /><el-input v-model="preferences.notes" type="textarea" :rows="4" placeholder="其他偏好或避雷项" /><el-button :icon="Save" @click="savePreferences">保存偏好</el-button></div></article>
          </section>
        </section>

        <section v-else-if="currentView === 'analysis'" class="view-stack">
          <section class="content-grid analysis-entry">
            <article class="surface jd-surface">
              <div class="section-heading"><div><p class="eyebrow">JOB DESCRIPTION</p><h2>导入或粘贴岗位原文</h2><p>可上传职位截图，本地 OCR 后再由你检查和分析。</p></div><ClipboardCheck :size="19" /></div>
              <el-select v-if="jobs.length" v-model="selectedJobId" class="job-select" placeholder="选择已导入职位" @change="loadJobDraft">
                <el-option v-for="job in jobs" :key="job.id" :label="`${job.title || '未命名职位'} · ${job.company || '待确认公司'}`" :value="job.id" />
              </el-select>
              <el-upload class="job-screenshot-upload" :auto-upload="false" :show-file-list="true" multiple accept=".png,.jpg,.jpeg,.webp" :on-change="handleJobScreenshotChange">
                <el-button :icon="Upload" :loading="loading">导入 BOSS 职位截图</el-button>
              </el-upload>
              <el-button v-if="jobScreenshotFiles.length" class="job-import-button" :loading="loading" @click="importSelectedJobScreenshots">识别 {{ jobScreenshotFiles.length }} 张截图</el-button>
              <div v-if="selectedJob" class="job-draft-banner"><span>已创建职位草稿 · {{ selectedJob.screenshots.length }} 张截图</span><span>{{ selectedJob.source === 'boss_screenshot' ? 'BOSS 截图导入' : '手动导入' }}</span></div>
              <el-input v-model="jdText" type="textarea" :rows="13" placeholder="粘贴岗位职责、任职要求、加分项等内容" />
              <div class="analysis-actions"><span>{{ selectedResume ? `使用：${selectedResume.filename}` : '请先选择一份简历' }}</span><el-button type="primary" :icon="Send" :loading="loading" :disabled="!selectedResumeId || jdText.length < 10" @click="runMatch">分析岗位</el-button></div>
            </article>
            <article class="surface analysis-guide"><p class="eyebrow">JOB DRAFT</p><h2>确认职位信息</h2><div class="job-draft-fields"><el-input v-model="jobDraft.title" placeholder="岗位名称" /><el-input v-model="jobDraft.company" placeholder="公司名称（可稍后补充）" /><el-input v-model="jobDraft.city" placeholder="城市" /><el-input v-model="jobDraft.salary" placeholder="薪资" /><el-input v-model="jobDraft.experience" placeholder="经验要求" /><el-input v-model="jobDraft.education" placeholder="学历要求" /><el-select v-model="jobDraft.status" placeholder="当前状态"><el-option label="待确认" value="pending_review" /><el-option label="可沟通" value="ready" /><el-option label="沟通中" value="contacted" /><el-option label="已沟通待回复" value="waiting" /><el-option label="已读未回" value="read_no_reply" /><el-option label="已发简历" value="resume_sent" /><el-option label="笔试 / 作业" value="assessment" /><el-option label="面试中" value="interview" /><el-option label="Offer" value="offer" /><el-option label="不合适" value="rejected" /><el-option label="归档" value="archived" /></el-select><el-date-picker v-model="jobDraft.next_action_at" type="date" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="下一步日期" /></div><el-input v-model="jobDraft.notes" type="textarea" :rows="3" placeholder="这份职位的关键信息、沟通记录或下一步安排" /><el-button v-if="selectedJob" :icon="Save" :loading="loading" @click="saveJobDraft">保存职位草稿</el-button><p class="guide-note">截图只在本机 OCR。搜索列表截图可能带入相邻职位，请校对后再分析。</p></article>
          </section>
          <section v-if="matchResult" class="match-report">
            <header class="report-hero"><div><p class="eyebrow">MATCH REPORT</p><h2>{{ matchResult.recommendation }}</h2><p>{{ matchResult.reason }}</p></div><div class="score-ring"><strong>{{ matchResult.score }}</strong><span>匹配度</span></div></header>
            <section v-if="matchResult.llm_insight" class="surface insight-surface">
              <div class="section-heading"><div><p class="eyebrow">DEEPSEEK INSIGHT</p><h2>岗位实际重心</h2></div><Sparkles :size="19" /></div>
              <p class="insight-focus">{{ matchResult.llm_insight.role_focus }}</p>
              <div class="insight-grid">
                <div><h3>日常工作</h3><ul><li v-for="item in matchResult.llm_insight.day_to_day" :key="item">{{ item }}</li></ul></div>
                <div><h3>建议确认</h3><ul><li v-for="item in matchResult.llm_insight.questions_to_clarify" :key="item">{{ item }}</li></ul></div>
                <div v-if="matchResult.llm_insight.risks.length"><h3>岗位风险</h3><ul><li v-for="item in matchResult.llm_insight.risks" :key="item">{{ item }}</li></ul></div>
              </div>
              <p v-if="matchResult.llm_insight.fact_codes.length" class="insight-facts">引用已确认事实：{{ matchResult.llm_insight.fact_codes.join('、') }}</p>
            </section>
            <div class="report-grid"><article class="surface"><div class="section-heading"><h2>可强调的证据</h2><CheckCircle2 :size="19" /></div><ul class="evidence-list"><li v-for="item in matchResult.matched" :key="item.requirement"><strong>{{ item.requirement }}</strong><span v-for="evidence in item.evidence" :key="evidence.fact_code">{{ evidence.fact_code }} · {{ evidence.content }}</span></li><li v-if="!matchResult.matched.length" class="muted">未找到直接匹配的关键词。</li></ul></article><article class="surface"><div class="section-heading"><h2>缺口与偏好</h2><CircleAlert :size="19" /></div><div class="gap-list"><span v-for="missing in matchResult.missing" :key="missing">{{ missing }}</span><p v-if="!matchResult.missing.length">暂无明显关键词缺口。</p></div><el-alert v-if="matchResult.preference_conflicts.length" type="warning" :title="matchResult.preference_conflicts.join('；')" :closable="false" show-icon /></article></div>
            <section class="surface draft-surface"><div class="section-heading"><div><p class="eyebrow">DRAFT & SAVE</p><h2>沟通草稿与投递记录</h2></div></div><el-input v-model="matchResult.greeting" type="textarea" :rows="4" /><el-alert class="fact-alert" :type="matchResult.fact_check.passed ? 'success' : 'warning'" :title="matchResult.fact_check.passed ? '事实审查通过' : matchResult.fact_check.risks.join('；')" :closable="false" show-icon /><div class="draft-form"><el-input v-model="applicationDraft.company" placeholder="公司名称" /><el-input v-model="applicationDraft.position" placeholder="岗位名称" /><el-input v-model="applicationDraft.jd_link" placeholder="JD 链接（可选）" /><el-select v-model="applicationDraft.status"><el-option label="草稿" value="draft" /><el-option label="已投递" value="submitted" /><el-option label="待跟进" value="follow_up" /><el-option label="面试中" value="interview" /></el-select><el-input v-model="applicationDraft.notes" placeholder="备注" /><el-button type="primary" :icon="Save" @click="saveApplication">保存投递记录</el-button></div></section>
          </section>
        </section>

        <section v-else-if="currentView === 'applications'" class="view-stack"><section class="surface applications-surface"><div class="section-heading"><div><p class="eyebrow">APPLICATION BOARD</p><h2>所有投递记录</h2><p>记录由你确认保存，Pathlight 不会替你发送申请。</p></div><span class="count-badge">{{ applications.length }}</span></div><el-table :data="applications" class="applications-table" empty-text="分析岗位后，可将草稿保存到这里。"><el-table-column prop="company" label="公司" min-width="150" /><el-table-column prop="position" label="岗位" min-width="160" /><el-table-column label="状态" width="115"><template #default="scope"><el-tag :type="scope.row.status === 'offer' ? 'success' : scope.row.status === 'rejected' ? 'danger' : scope.row.status === 'follow_up' ? 'warning' : 'info'">{{ statusLabel(scope.row.status) }}</el-tag></template></el-table-column><el-table-column prop="resume_version" label="简历版本" min-width="150" /><el-table-column prop="notes" label="备注" min-width="180" /><el-table-column label="JD" width="70"><template #default="scope"><a v-if="scope.row.jd_link" :href="scope.row.jd_link" target="_blank" rel="noreferrer" class="external-link" title="打开 JD"><ArrowUpRight :size="16" /></a></template></el-table-column></el-table></section></section>

        <section v-else class="view-stack settings-view"><section class="surface settings-surface"><div class="section-heading"><div><p class="eyebrow">MODEL CONNECTION</p><h2>DeepSeek API Key</h2><p>用于岗位研判与沟通草案。密钥不会进入 SQLite、日志或 Git。</p></div><KeyRound :size="20" /></div><div class="settings-key"><el-input v-model="apiKey" type="password" show-password placeholder="输入 DeepSeek API Key" autocomplete="off" /><el-button type="primary" :loading="loading" :disabled="apiKey.length < 12" @click="saveKey">保存 Key</el-button></div><div class="security-callout"><CheckCircle2 :size="18" /><div><strong>{{ health.has_api_key ? `当前已配置 ${health.model}` : '当前未配置 Key' }}</strong><p>凭据由操作系统的安全凭据库管理；开发期可从本机 .env 读取，均不会写入 SQLite 或 Git。</p></div></div></section><section class="surface settings-surface"><div class="section-heading"><div><p class="eyebrow">LOCAL DATA</p><h2>数据边界</h2></div></div><ul class="boundary-list"><li>简历、事实档案、偏好和投递记录保存在本机。</li><li>外部平台操作始终需要你的最终确认。</li><li>当前版本不自动投递、不抓取招聘平台。</li></ul></section></section>
      </div>
    </section>
    <AgentDock @submit="handleAgentMessage" />
  </main>
</template>
