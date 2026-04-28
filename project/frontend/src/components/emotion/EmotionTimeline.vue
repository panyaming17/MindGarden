<template>
  <div class="emotion-timeline">
    <div class="timeline-header">
      <span class="timeline-title">今日情绪时间线</span>
      <span class="timeline-count" v-if="allRecords.length > 0">
        今天共记录了 {{ allRecords.length }} 条
        <span v-if="allRecords.length >= maxTotal" class="limit-hint">（已达上限{{ maxTotal }}条）</span>
      </span>
    </div>

    <div v-if="allRecords.length === 0 && !loading" class="timeline-empty">
      <span class="empty-icon">📝</span>
      <span>今天还没有情绪记录，点击上方表情开始记录吧</span>
    </div>

    <div v-if="loading" class="timeline-loading">
      加载中...
    </div>

    <div class="timeline-list" v-if="allRecords.length > 0" ref="timelineListRef">
      <div
        v-for="record in allRecords"
        :key="record.id"
        class="timeline-row"
        @mouseenter="hoverId = record.id"
        @mouseleave="hoverId = null"
      >
        <span class="row-time">{{ formatTime(record.record_time) }}</span>
        <span class="row-emoji">{{ record.emotion_icon }}</span>
        <span
          v-if="editingId !== record.id"
          class="row-tag"
          :class="{ 'row-tag-empty': !record.signature }"
          @click="startEdit(record)"
        >
          {{ record.signature || '点击添加标签' }}
        </span>
        <input
          v-else
          ref="tagInput"
          class="row-tag-input"
          v-model="editingText"
          maxlength="50"
          placeholder="输入标签后，点击输入框外部实现保存"
          @blur="saveEdit(record)"
          @keydown.escape="cancelEdit"
        />
        <button
          v-show="hoverId === record.id"
          class="row-delete"
          title="删除此条记录"
          @click.stop="handleDelete(record)"
        >×</button>
      </div>
    </div>

    <div v-if="allRecords.length >= maxTotal" class="limit-warning">
      <el-alert type="warning" :closable="false" show-icon>
        <template #title>
          今日情绪记录已达上限（{{ maxTotal }}条）
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useEmotionStore } from '@/stores/emotion'

const props = defineProps({
  records: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['updated', 'deleted', 'viewAll'])

const emotionStore = useEmotionStore()
const maxTotal = 24  // 总数限制24条

const hoverId = ref(null)
const editingId = ref(null)
const editingText = ref('')
const tagInput = ref(null)
const timelineListRef = ref(null)

// 限制最多24条记录
const allRecords = computed(() => {
  const records = props.records || []
  return records.slice(0, maxTotal)
})

function formatTime(timeStr) {
  if (!timeStr) return ''
  return timeStr.substring(0, 5) // HH:mm
}

function startEdit(record) {
  editingId.value = record.id
  editingText.value = record.signature || ''
  nextTick(() => {
    if (tagInput.value) {
      const input = Array.isArray(tagInput.value) ? tagInput.value[0] : tagInput.value
      if (input) input.focus()
    }
  })
}

async function saveEdit(record) {
  if (!editingText.value.trim() && !record.signature) {
    cancelEdit()
    return
  }
  try {
    await emotionStore.updateRecord(record.id, editingText.value.trim())
    emit('updated')
  } catch (e) {
    console.error('保存标签失败:', e)
  } finally {
    cancelEdit()
  }
}

function cancelEdit() {
  editingId.value = null
  editingText.value = ''
}

async function handleDelete(record) {
  try {
    await emotionStore.deleteRecord(record.id)
    emit('deleted')
  } catch (e) {
    console.error('删除失败:', e)
  }
}
</script>

<style scoped>
.emotion-timeline {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  max-height: 100%;
  overflow: hidden;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.timeline-title {
  font-size: 15px;
  font-weight: 600;
  color: #2d3436;
}

.timeline-count {
  font-size: 13px;
  color: #636e72;
}

.limit-hint {
  color: #e17055;
  font-weight: 500;
}

.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  color: #b2bec3;
  font-size: 14px;
}

.empty-icon {
  font-size: 32px;
}

.timeline-loading {
  text-align: center;
  padding: 20px;
  color: #b2bec3;
  font-size: 14px;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  /* 5条记录的高度：每条约50px + gap 8px */
  max-height: 290px;
}

.timeline-list::-webkit-scrollbar {
  width: 4px;
}

.timeline-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.timeline-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.timeline-list::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.timeline-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f8f9fa;
  transition: background 0.2s;
  position: relative;
  flex-shrink: 0;
}

.timeline-row:hover {
  background: #f1f3f5;
}

.row-time {
  font-size: 13px;
  color: #636e72;
  min-width: 48px;
  font-family: 'SF Mono', 'Consolas', monospace;
}

.row-emoji {
  font-size: 22px;
  min-width: 28px;
  text-align: center;
}

.row-tag {
  flex: 1;
  font-size: 14px;
  color: #2d3436;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-tag:hover {
  background: #e1e5ea;
}

.row-tag-empty {
  color: #b2bec3;
  font-style: italic;
}

.row-tag-input {
  flex: 1;
  font-size: 14px;
  color: #2d3436;
  padding: 4px 8px;
  border: 1.5px solid #74b9ff;
  border-radius: 6px;
  outline: none;
  background: #fff;
  font-family: inherit;
}

.row-tag-input:focus {
  border-color: #0984e3;
  box-shadow: 0 0 0 3px rgba(9, 132, 227, 0.15);
}

.row-delete {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: #ff7675;
  color: #fff;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, transform 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.timeline-row:hover .row-delete {
  opacity: 1;
}

.row-delete:hover {
  transform: scale(1.15);
  background: #d63031;
}

.limit-warning {
  margin-top: 8px;
  flex-shrink: 0;
}

:deep(.el-alert) {
  padding: 8px 12px;
}

:deep(.el-alert__title) {
  font-size: 12px;
}
</style>
