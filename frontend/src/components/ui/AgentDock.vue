<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import { MessageCircle, Mic, Send, Sparkles, X } from 'lucide-vue-next';

const props = withDefaults(defineProps<{
  agentName?: string;
  idleStatus?: string;
  workingStatus?: string;
  working?: boolean;
}>(), {
  agentName: 'Pathlight',
  idleStatus: '准备就绪',
  workingStatus: '正在整理上下文',
  working: false,
});

const emit = defineEmits<{ submit: [message: string] }>();
const mode = ref<'idle' | 'composing' | 'working'>('idle');
const message = ref('');
const textarea = ref<HTMLTextAreaElement | null>(null);

watch(() => props.working, (working) => {
  if (working) {
    mode.value = 'working';
  } else if (mode.value === 'working') {
    mode.value = 'idle';
  }
});

async function openComposer() {
  mode.value = 'composing';
  await nextTick();
  textarea.value?.focus();
}

function closeComposer() {
  mode.value = 'idle';
  message.value = '';
}

function submitMessage() {
  const nextMessage = message.value.trim();
  if (!nextMessage) {
    void openComposer();
    return;
  }
  message.value = '';
  mode.value = 'working';
  emit('submit', nextMessage);
  // Covers local validation failures before the parent has started an async request.
  window.setTimeout(() => {
    if (!props.working && mode.value === 'working') mode.value = 'idle';
  }, 1000);
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    submitMessage();
  }
}
</script>

<template>
  <form class="agent-dock" @submit.prevent="mode === 'composing' ? submitMessage() : openComposer()">
    <div class="agent-dock__composer" :class="{ 'is-open': mode === 'composing' }">
      <button class="agent-dock__close" type="button" aria-label="关闭输入框" @click="closeComposer"><X :size="15" /></button>
      <textarea ref="textarea" v-model="message" aria-label="向 Pathlight 提问" placeholder="粘贴招聘方的问题，Pathlight 会基于当前岗位和事实档案起草回复" :disabled="props.working" @keydown="handleKeydown" />
      <span>Enter 发送 · Shift + Enter 换行</span>
    </div>
    <div class="agent-dock__bar">
      <div class="agent-dock__avatar"><Sparkles :size="17" /></div>
      <div class="agent-dock__identity">
        <strong>{{ props.agentName }}</strong>
        <span>{{ mode === 'working' ? props.workingStatus : props.idleStatus }}</span>
      </div>
      <div class="agent-dock__actions">
        <button type="button" aria-label="语音输入（即将支持）" title="语音输入（即将支持）" disabled><Mic :size="16" /></button>
        <button class="agent-dock__send" type="submit" :disabled="props.working" :aria-label="mode === 'composing' ? '发送消息' : '打开对话输入框'">
          <Send v-if="mode === 'composing'" :size="16" />
          <MessageCircle v-else :size="16" />
        </button>
      </div>
    </div>
  </form>
</template>
