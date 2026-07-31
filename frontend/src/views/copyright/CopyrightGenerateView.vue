<template>
  <div class="copyright-generate-view">
    <!-- 软件信息摘要 -->
    <el-card v-if="appInfo">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>软件信息</span>
          <el-button link type="primary" @click="$router.push(`/copyright/${appId}/edit`)">编辑信息</el-button>
        </div>
      </template>
      <el-descriptions :column="2" border label-width="90px" label-class-name="desc-label">
        <el-descriptions-item label="软件名称">{{ appInfo.software_name }}</el-descriptions-item>
        <el-descriptions-item label="简称">{{ appInfo.software_short_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="appStatusTag(appInfo.status)">{{ appStatusLabel(appInfo.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">{{ appInfo.software_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="软件类别">{{ appInfo.software_category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="运行平台">{{ appInfo.runtime_platform || '-' }}</el-descriptions-item>
        <el-descriptions-item label="开发语言">{{ appInfo.development_language || '-' }}</el-descriptions-item>
        <el-descriptions-item label="开发方式">{{ appInfo.development_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="代码行数">{{ appInfo.code_line_count || '-' }}</el-descriptions-item>
        <el-descriptions-item label="完成日期">{{ appInfo.completion_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标行业">{{ appInfo.target_industry || '-' }}</el-descriptions-item>
        <el-descriptions-item label="技术特点">{{ appInfo.technical_features || '-' }}</el-descriptions-item>
        <el-descriptions-item label="生成选项" :span="2">
          <el-tag size="small" style="margin-right: 4px;">操作说明书</el-tag>
          <el-tag v-if="appInfo.generate_db_design" size="small" style="margin-right: 4px;">数据库设计</el-tag>
          <el-tag size="small" style="margin-right: 4px;">源程序代码</el-tag>
          <el-tag v-if="appInfo.generate_diagrams" size="small" type="warning">图表</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="主要功能" :span="2">{{ appInfo.main_features }}</el-descriptions-item>
        <el-descriptions-item v-if="appInfo.software_description" label="软件描述" :span="2">{{ appInfo.software_description }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- ========== 状态 A：无任务 — 显示生成表单 ========== -->
    <el-card v-if="!task" class="mt-16">
      <template #header>
        <span>AI 生成</span>
      </template>
      <el-form label-position="top">
        <el-form-item>
          <template #label>
            <span>额外指令</span>
            <span style="font-weight: normal; font-size: 12px; color: #909399; margin-left: 8px;">如果生成结果不满意，可以在此填写具体要求后重新生成</span>
          </template>
          <el-input
            v-model="extraPrompt"
            type="textarea"
            :rows="3"
            placeholder="可选：例如「功能模块要重点描述数据分析部分」「语言风格更正式一些」「多补充安全相关的内容」等"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate">开始生成</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ========== 状态 B / C：有任务 — 显示任务信息 ========== -->
    <el-card v-if="task" class="mt-16">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>生成任务</span>
          <el-button
            v-if="!isTaskRunning"
            link type="primary"
            @click="openTaskEditDialog"
          >编辑额外指令</el-button>
        </div>
      </template>

      <!-- 任务元信息 -->
      <el-descriptions :column="2" border label-width="90px" label-class-name="desc-label">
        <el-descriptions-item label="任务状态">
          <el-tag :type="taskStatusTag(task.status)">{{ taskStatusLabel(task.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatDate(task.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="额外指令">{{ task.extra_prompt || '无' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 进行中：进度条 -->
      <div v-if="isTaskRunning" class="task-progress">
        <el-progress
          :percentage="progressPercent"
          :stroke-width="12"
          style="max-width: 500px; width: 100%;"
        />
        <p class="task-progress-hint">正在生成中，请耐心等待...</p>
      </div>

      <!-- 失败提示 -->
      <div v-if="!isTaskRunning && task.status === 'failed'" class="task-status-msg">
        <el-alert type="error" :closable="false" show-icon title="生成失败，请重试" />
      </div>

      <!-- 完成提示 -->
      <div v-if="!isTaskRunning && task.status === 'completed'" class="task-status-msg">
        <el-alert
          type="success"
          :closable="false"
          show-icon
          :title="`生成完成，共 ${completedCount} 个章节` + (failedCount > 0 ? `（${failedCount} 个失败）` : '')"
        />
      </div>

      <!-- 重新生成按钮 -->
      <div v-if="!isTaskRunning" style="margin-top: 16px;">
        <el-button type="primary" @click="handleGenerate">重新生成</el-button>
      </div>
    </el-card>

    <!-- 重新生成中提示 -->
    <el-alert
      v-if="!isTaskRunning && regeneratingCount > 0"
      class="mt-16"
      type="info"
      show-icon
      :closable="false"
      :title="`${regeneratingCount} 个章节正在重新生成中...`"
    />

    <!-- ========== 生成结果 ========== -->
    <el-card v-if="task && allSections.length" class="mt-16">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>生成结果</span>
          <el-tooltip content="提交导出任务，完成后可在下方最近导出中下载" placement="top">
            <el-dropdown split-button type="primary" size="small" @click="handleExportManualWord" @command="handleExportCommand">
              <template v-if="exporting">
                <el-icon class="is-loading"><Loading /></el-icon> 提交中...
              </template>
              <template v-else>导出文档鉴别材料</template>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="application-form-txt">申请表信息（TXT）</el-dropdown-item>
                  <el-dropdown-item command="manual-word">文档鉴别材料（Word）</el-dropdown-item>
                  <el-dropdown-item command="manual-pdf">文档鉴别材料（PDF）</el-dropdown-item>
                  <el-dropdown-item divided command="source-code-word">源程序鉴别材料（Word）</el-dropdown-item>
                  <el-dropdown-item command="source-code-pdf">源程序鉴别材料（PDF）</el-dropdown-item>
                  <el-dropdown-item divided command="all">全部导出（ZIP）</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-tooltip>
        </div>
      </template>

      <!-- 操作说明书 -->
      <template v-if="manualSections.length">
        <div class="section-group-title">操作说明书</div>
        <el-collapse v-model="activeCollapse">
          <el-collapse-item
            v-for="section in manualSections"
            :key="section.id"
            :name="section.id"
          >
            <template #title>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>{{ section.title }}</span>
                <el-tag :type="getSectionStatusTag(section.status).type" size="small">
                  <span v-if="section.status === 'running'" style="display: inline-flex; align-items: center; gap: 3px;">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ getSectionStatusTag(section.status).label }}</span>
                  </span>
                  <span v-else>{{ getSectionStatusTag(section.status).label }}</span>
                </el-tag>
              </div>
            </template>
            <div class="section-content">
              <el-alert
                v-if="section.status === 'failed'"
                type="error"
                :closable="false"
                show-icon
                style="margin-bottom: 12px;"
              >
                <template #title>生成失败</template>
                {{ section.error_message || '生成过程出现错误，请重新生成' }}
              </el-alert>
              <div v-if="section.status === 'pending'" style="color: #909399; padding: 20px; text-align: center;">
                等待生成...
              </div>
              <div v-else-if="section.status === 'running'" style="color: #409EFF; padding: 20px; text-align: center;">
                <el-icon class="is-loading" style="font-size: 20px;"><Loading /></el-icon>
                <p style="margin-top: 8px;">正在生成中，请稍候...</p>
              </div>
              <div v-else-if="section.content" class="content-preview markdown-body" v-html="renderMarkdown(section.content)">
              </div>
              <el-empty v-else-if="section.status === 'completed'" description="内容为空" />
              <div v-if="section.status === 'completed' || section.status === 'failed'" style="margin-top: 12px; display: flex; gap: 8px;">
                <el-button v-if="section.status === 'completed'" size="small" @click="openEditDialog(section)">编辑</el-button>
                <el-button size="small" type="warning" @click="openRegenerateDialog(section)">重新生成</el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </template>

      <!-- 数据库设计 -->
      <template v-if="dbSections.length">
        <div class="section-group-title">数据库设计</div>
        <el-collapse v-model="activeCollapse">
          <el-collapse-item
            v-for="section in dbSections"
            :key="section.id"
            :name="section.id"
          >
            <template #title>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>{{ section.title }}</span>
                <el-tag :type="getSectionStatusTag(section.status).type" size="small">
                  <span v-if="section.status === 'running'" style="display: inline-flex; align-items: center; gap: 3px;">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ getSectionStatusTag(section.status).label }}</span>
                  </span>
                  <span v-else>{{ getSectionStatusTag(section.status).label }}</span>
                </el-tag>
              </div>
            </template>
            <div class="section-content">
              <el-alert
                v-if="section.status === 'failed'"
                type="error"
                :closable="false"
                show-icon
                style="margin-bottom: 12px;"
              >
                <template #title>生成失败</template>
                {{ section.error_message || '生成过程出现错误，请重新生成' }}
              </el-alert>
              <div v-if="section.status === 'pending'" style="color: #909399; padding: 20px; text-align: center;">
                等待生成...
              </div>
              <div v-else-if="section.status === 'running'" style="color: #409EFF; padding: 20px; text-align: center;">
                <el-icon class="is-loading" style="font-size: 20px;"><Loading /></el-icon>
                <p style="margin-top: 8px;">正在生成中，请稍候...</p>
              </div>
              <div v-else-if="section.content" class="content-preview markdown-body" v-html="renderMarkdown(section.content)">
              </div>
              <el-empty v-else-if="section.status === 'completed'" description="内容为空" />
              <div v-if="section.status === 'completed' || section.status === 'failed'" style="margin-top: 12px; display: flex; gap: 8px;">
                <el-button v-if="section.status === 'completed'" size="small" @click="openEditDialog(section)">编辑</el-button>
                <el-button size="small" type="warning" @click="openRegenerateDialog(section)">重新生成</el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </template>

      <!-- 源程序代码 -->
      <template v-if="codeSections.length">
        <div class="section-group-title">源程序代码</div>
        <el-collapse v-model="activeCollapse">
          <el-collapse-item
            v-for="section in codeSections"
            :key="section.id"
            :name="section.id"
          >
            <template #title>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>{{ section.title }}</span>
                <el-tag :type="getSectionStatusTag(section.status).type" size="small">
                  <span v-if="section.status === 'running'" style="display: inline-flex; align-items: center; gap: 3px;">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>{{ getSectionStatusTag(section.status).label }}</span>
                  </span>
                  <span v-else>{{ getSectionStatusTag(section.status).label }}</span>
                </el-tag>
              </div>
            </template>
            <div class="section-content">
              <el-alert
                v-if="section.status === 'failed'"
                type="error"
                :closable="false"
                show-icon
                style="margin-bottom: 12px;"
              >
                <template #title>生成失败</template>
                {{ section.error_message || '生成过程出现错误，请重新生成' }}
              </el-alert>
              <div v-if="section.status === 'pending'" style="color: #909399; padding: 20px; text-align: center;">
                等待生成...
              </div>
              <div v-else-if="section.status === 'running'" style="color: #409EFF; padding: 20px; text-align: center;">
                <el-icon class="is-loading" style="font-size: 20px;"><Loading /></el-icon>
                <p style="margin-top: 8px;">正在生成中，请稍候...</p>
              </div>
              <div v-else-if="section.content" class="content-preview markdown-body" v-html="renderMarkdown(section.content)">
              </div>
              <el-empty v-else-if="section.status === 'completed'" description="内容为空" />
              <div v-if="section.status === 'completed' || section.status === 'failed'" style="margin-top: 12px; display: flex; gap: 8px;">
                <el-button v-if="section.status === 'completed'" size="small" @click="openEditDialog(section)">编辑</el-button>
                <el-button size="small" type="warning" @click="openRegenerateDialog(section)">重新生成</el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </template>
    </el-card>

    <!-- 最新导出记录 -->
    <el-card v-if="latestExports.length" class="mt-16">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>最近导出</span>
          <div style="display: flex; gap: 8px;">
            <el-button
              v-if="hasFailedExports"
              size="small"
              type="danger"
              plain
              @click="handleCleanFailedExports"
            >清理失败任务</el-button>
          </div>
        </div>
      </template>
      <el-table :data="latestExports" size="small" style="width: 100%;">
        <el-table-column label="格式" min-width="180">
          <template #default="{ row }">{{ formatExportFormat(row.format) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="exportStatusTag(row.status)">
              <span style="display: inline-flex; align-items: center; gap: 3px; white-space: nowrap;">
                <el-icon v-if="row.status === 'processing'" class="is-loading"><Loading /></el-icon>
                <span>{{ exportStatusLabel(row.status) }}</span>
              </span>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px; justify-content: center;">
              <el-tooltip v-if="row.status === 'completed'" content="下载文件" placement="top">
                <el-button
                  link type="primary" size="small"
                  @click="handleDownloadExport(row.id)"
                >下载</el-button>
              </el-tooltip>
              <el-popconfirm
                title="确认删除此任务？"
                confirm-button-text="删除"
                cancel-button-text="取消"
                @confirm="handleDeleteExport(row.id)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑章节弹窗（左右分栏） -->
    <el-dialog v-model="editDialogVisible" title="编辑章节内容" width="90%" top="3vh">
      <div class="edit-split-pane">
        <div class="edit-pane-left">
          <div class="edit-pane-header">编辑（Markdown）</div>
          <el-input
            v-model="editContent"
            type="textarea"
            :rows="25"
            placeholder="编辑章节内容（Markdown 格式）"
            class="edit-textarea"
          />
        </div>
        <div class="edit-pane-right">
          <div class="edit-pane-header">预览</div>
          <div class="edit-preview markdown-body" v-html="editPreviewHtml"></div>
        </div>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重新生成弹窗 -->
    <el-dialog v-model="regenerateDialogVisible" title="重新生成章节" width="500px">
      <p style="margin-bottom: 12px; color: #606266;">
        将重新生成「{{ regenerateSection?.title }}」章节，当前内容将被覆盖。
      </p>
      <el-input v-model="regeneratePrompt" type="textarea" :rows="4" placeholder="可选：输入额外的生成指令" />
      <template #footer>
        <el-button @click="regenerateDialogVisible = false">取消</el-button>
        <el-button type="warning" @click="handleRegenerate">确认重新生成</el-button>
      </template>
    </el-dialog>

    <!-- 编辑任务额外指令弹窗 -->
    <el-dialog v-model="taskEditDialogVisible" title="编辑额外指令" width="500px">
      <el-form label-position="top">
        <el-form-item label="额外指令">
          <el-input
            v-model="taskEditExtraPrompt"
            type="textarea"
            :rows="4"
            placeholder="可选：提供额外的生成指令"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskEditDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="taskEditSaving" @click="handleSaveTaskEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { applicationApi, generationApi, exportApi } from '@/api'
import type { ApplicationRecord } from '@/api/application'
import type { TaskRecord, SectionRecord } from '@/api/generation'
import { createSSE } from '@/utils/sse'
import { formatDate } from '@/utils/format'
import { marked } from 'marked'

function renderMarkdown(content: string): string {
  return marked.parse(content, { async: false }) as string
}

const route = useRoute()
const appId = computed(() => Number(route.params.id))

const appInfo = ref<ApplicationRecord | null>(null)
const task = ref<TaskRecord | null>(null)
const extraPrompt = ref('')
const activeCollapse = ref<number[]>([])
const exporting = ref<string | null>(null)

// 编辑章节弹窗
const editDialogVisible = ref(false)
const editContent = ref('')
const editSectionId = ref<number | null>(null)
const saving = ref(false)
const editPreviewHtml = computed(() => {
  if (!editContent.value) return ''
  return renderMarkdown(editContent.value)
})

// 重新生成弹窗
const regenerateDialogVisible = ref(false)
const regeneratePrompt = ref('')
const regenerateSection = ref<SectionRecord | null>(null)

// 编辑任务弹窗
const taskEditDialogVisible = ref(false)
const taskEditSaving = ref(false)
const taskEditExtraPrompt = ref('')

// SSE 连接
let genSSE: EventSource | null = null
let exportSSE: EventSource | null = null

const isTaskRunning = computed(() => {
  if (!task.value) return false
  return task.value.status === 'pending' || task.value.status === 'running'
})

const progressPercent = computed(() => {
  if (!task.value || !task.value.sections.length) return 0
  const total = task.value.sections.length
  const done = task.value.sections.filter(
    s => s.status === 'completed' || s.status === 'failed'
  ).length
  return Math.min(100, Math.round((done / total) * 100))
})

const HIDDEN_SECTION_KEYS = ['form_autofill', 'arch_diagram', 'uml_diagram', 'ui_diagrams']

const allSections = computed(() => {
  if (!task.value) return []
  // 排除元数据章节和图表章节（图表作为主流程一部分，不单独展示）
  return task.value.sections.filter(s => !HIDDEN_SECTION_KEYS.includes(s.section_key))
})

const manualSections = computed(() =>
  allSections.value.filter(s => s.section_key.startsWith('manual_'))
)

const dbSections = computed(() =>
  allSections.value.filter(s => s.section_key.startsWith('db_design'))
)

const codeSections = computed(() =>
  allSections.value.filter(s => s.section_key.startsWith('source_code_'))
)

const completedSections = computed(() => {
  if (!task.value) return []
  return task.value.sections.filter(s => s.status === 'completed')
})

function getSectionStatusTag(status: string) {
  const map: Record<string, { type: any; label: string }> = {
    pending: { type: 'info', label: '待生成' },
    running: { type: '', label: '生成中' },
    completed: { type: 'success', label: '已完成' },
    failed: { type: 'danger', label: '失败' },
  }
  return map[status] || { type: 'info', label: status }
}

const completedCount = computed(() => completedSections.value.length)

const failedCount = computed(() => {
  if (!task.value) return 0
  return task.value.sections.filter(s => s.status === 'failed').length
})

const regeneratingCount = computed(() => {
  if (!task.value) return 0
  return task.value.sections.filter(s => s.status === 'pending' || s.status === 'running').length
})

const hasFailedExports = computed(() => latestExports.value.some(e => e.status === 'failed'))

function appStatusLabel(s: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    generating: '生成中',
    generated: '已生成',
    ready: '可导出',
    submitted: '已提交',
    approved: '已通过',
    rejected: '已驳回',
    archived: '已归档',
    completed: '已完成',
  }
  return map[s] || s
}

function appStatusTag(s: string) {
  const map: Record<string, string> = {
    draft: 'info',
    generating: '',
    generated: 'success',
    ready: 'success',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    archived: 'info',
    completed: 'success',
  }
  return (map[s] || '') as any
}

function taskStatusLabel(s: string) {
  const map: Record<string, string> = { pending: '等待中', running: '生成中', completed: '已完成', failed: '失败' }
  return map[s] || s
}

function taskStatusTag(s: string) {
  const map: Record<string, string> = { pending: 'info', running: '', completed: 'success', failed: 'danger' }
  return (map[s] || 'info') as any
}

async function fetchApp() {
  try {
    const res = await applicationApi.getApplication(appId.value)
    appInfo.value = res.data
  } catch {
    // handled by interceptor
  }
}

async function fetchGeneration() {
  try {
    const res = await generationApi.getGeneration(appId.value)
    task.value = res.data
  } catch {
    task.value = null
  }
}

function startGenSSE() {
  stopGenSSE()
  genSSE = createSSE(`/generation/${appId.value}`)

  // 记录上一次的 sections 状态，用于检测变化
  let lastSectionsState = ''

  genSSE.onmessage = async (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.error) return

      // 计算当前 sections 状态的指纹（用于检测变化）
      const currentState = data.sections?.map((s: any) => `${s.id}:${s.status}`).join(',') || ''

      // 检测到 sections 状态变化，获取完整数据（包含 content）
      if (currentState !== lastSectionsState && currentState) {
        lastSectionsState = currentState
        await fetchGeneration()
      } else {
        // 没有变化时，只更新轻量级进度数据
        if (task.value) {
          task.value.status = data.status
          task.value.total_sections = data.total_sections
          task.value.completed_sections = data.completed_sections
          task.value.updated_at = data.updated_at
        }
      }

      const running = data.status === 'pending' || data.status === 'running'
      if (!running) {
        stopGenSSE()

        // 任务完成，再次获取完整数据确保最新
        await fetchGeneration()
      }
    } catch { /* ignore parse errors */ }
  }
  genSSE.onerror = () => {
    stopGenSSE()
  }
}

function stopGenSSE() {
  if (genSSE) {
    genSSE.close()
    genSSE = null
  }
}

async function handleGenerate() {
  const msg = task.value
    ? '将创建新的生成任务，当前结果将被替换，确认继续？'
    : '确认开始生成？'
  try {
    await ElMessageBox.confirm(msg, '确认', { type: 'info' })
  } catch {
    return
  }

  try {
    const res = await generationApi.startGeneration(appId.value, {
      extra_prompt: extraPrompt.value || undefined,
    })
    task.value = res.data

    ElMessage.success('生成任务已提交')
    startGenSSE()
  } catch {
    // handled by interceptor
  }
}

// 编辑章节
function openEditDialog(section: SectionRecord) {
  editSectionId.value = section.id
  editContent.value = section.content || ''
  editDialogVisible.value = true
}

async function handleSaveEdit() {
  if (!editSectionId.value) return
  saving.value = true
  try {
    await generationApi.updateSection(editSectionId.value, { content: editContent.value })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    await fetchGeneration()
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}

// 重新生成章节
function openRegenerateDialog(section: SectionRecord) {
  regenerateSection.value = section
  regeneratePrompt.value = ''
  regenerateDialogVisible.value = true
}

async function handleRegenerate() {
  if (!regenerateSection.value) return
  try {
    await generationApi.regenerateSection(regenerateSection.value.id, {
      extra_prompt: regeneratePrompt.value || undefined,
    })

    ElMessage.success('重新生成已提交')
    regenerateDialogVisible.value = false
    startGenSSE()
  } catch {
    // handled by interceptor
  }
}

// 编辑任务额外指令
function openTaskEditDialog() {
  if (!task.value) return
  taskEditExtraPrompt.value = task.value.extra_prompt || ''
  taskEditDialogVisible.value = true
}

async function handleSaveTaskEdit() {
  taskEditSaving.value = true
  try {
    const res = await generationApi.updateTask(appId.value, {
      extra_prompt: taskEditExtraPrompt.value || undefined,
    })
    task.value = res.data
    ElMessage.success('保存成功')
    taskEditDialogVisible.value = false
  } catch {
    // handled by interceptor
  } finally {
    taskEditSaving.value = false
  }
}


// 导出（异步任务）
async function handleExportManualWord() {
  await doExport('manual-word')
}

async function handleExportCommand(command: string) {
  await doExport(command)
}

async function doExport(command: string) {
  if (exporting.value) return

  exporting.value = command
  try {
    await exportApi.createExportTask(appId.value, { format: command as any })
    ElMessage.success('导出任务已提交，请在下方最近导出中查看')
    await fetchLatestExports()
    startExportSSE()

  } catch {
    // handled by interceptor
  } finally {
    exporting.value = null
  }
}

// 最新导出记录
const latestExports = ref<import('@/api/export').ExportTaskRecord[]>([])

async function fetchLatestExports() {
  try {
    const res = await exportApi.getLatestExports(appId.value)
    latestExports.value = res.data
  } catch {
    latestExports.value = []
  }
}

function exportStatusTag(s: string) {
  const map: Record<string, string> = { pending: 'info', processing: '', completed: 'success', failed: 'danger' }
  return (map[s] || 'info') as any
}

function exportStatusLabel(s: string) {
  const map: Record<string, string> = { pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败' }
  return map[s] || s
}

function formatExportFormat(f: string) {
  const map: Record<string, string> = {
    'application-form-txt': '申请表信息（TXT）',
    'manual-word': '文档鉴别材料（Word）',
    'manual-pdf': '文档鉴别材料（PDF）',
    'source-code-word': '源程序鉴别材料（Word）',
    'source-code-pdf': '源程序鉴别材料（PDF）',
    'all': '全部导出（ZIP）',
  }
  return map[f] || f
}

function formatFileSize(bytes: number | null) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleDownloadExport(taskId: number) {
  window.open(`/api/v1/export-tasks/${taskId}/download`, '_blank')
}

async function handleDeleteExport(taskId: number) {
  try {
    await exportApi.deleteExportTask(taskId)
    ElMessage.success('删除成功')
    await fetchLatestExports()
  } catch {
    // handled by interceptor
  }
}

async function handleCleanFailedExports() {
  try {
    await ElMessageBox.confirm('确认删除所有失败的任务？', '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    const res = await exportApi.deleteFailedExportTasks()
    ElMessage.success(res.data.message)
    await fetchLatestExports()
  } catch (e) {
    if (e !== 'cancel') {
      // handled by interceptor
    }
  }
}

function startExportSSE() {
  stopExportSSE()
  exportSSE = createSSE('/export-tasks', { app_id: String(appId.value) })
  exportSSE.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.items) latestExports.value = data.items
      const hasPending = data.items?.some((i: any) => i.status === 'pending' || i.status === 'processing')
      if (!hasPending) stopExportSSE()
    } catch { /* ignore */ }
  }
  exportSSE.onerror = () => {
    stopExportSSE()
  }
}

function stopExportSSE() {
  if (exportSSE) {
    exportSSE.close()
    exportSSE = null
  }
}

onMounted(async () => {
  await fetchApp()
  await Promise.all([fetchGeneration(), fetchLatestExports()])
  if (isTaskRunning.value) {
    startGenSSE()
  }
  const hasPendingExport = latestExports.value.some(e => e.status === 'pending' || e.status === 'processing')
  if (hasPendingExport) {
    startExportSSE()
  }
})

onUnmounted(() => {
  stopGenSSE()
  stopExportSSE()
})
</script>

<style scoped lang="scss">
.mt-16 {
  margin-top: 16px;
}

.copyright-generate-view {
  max-width: 1200px;
}

.task-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0 8px;
}

.task-progress-hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: $text-secondary;
}

.task-status-msg {
  margin-top: 16px;
}

.section-content {
  padding: 8px 0;
}

.content-preview {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px 16px;
}

/* Split-pane editor */
.edit-split-pane {
  display: flex;
  gap: 16px;
  height: 60vh;
}

.edit-pane-left,
.edit-pane-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.edit-pane-header {
  font-size: 13px;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 8px;
}

.edit-pane-left :deep(.el-textarea) {
  flex: 1;
}

.edit-pane-left :deep(.el-textarea__inner) {
  height: 100% !important;
  resize: none;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.edit-preview {
  flex: 1;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 4px;
  border: 1px solid $border-color;
  padding: 12px 16px;
}

/* Markdown body styles */
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  word-break: break-word;

  :deep(h1) { font-size: 22px; font-weight: 600; margin: 20px 0 12px; border-bottom: 1px solid #ebeef5; padding-bottom: 8px; }
  :deep(h2) { font-size: 18px; font-weight: 600; margin: 18px 0 10px; border-bottom: 1px solid #ebeef5; padding-bottom: 6px; }
  :deep(h3) { font-size: 16px; font-weight: 600; margin: 16px 0 8px; }
  :deep(h4) { font-size: 15px; font-weight: 600; margin: 14px 0 6px; }
  :deep(p) { margin: 8px 0; }
  :deep(ul), :deep(ol) { padding-left: 24px; margin: 8px 0; }
  :deep(li) { margin: 4px 0; }
  :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
  :deep(th), :deep(td) { border: 1px solid #dcdfe6; padding: 8px 12px; text-align: left; font-size: 13px; }
  :deep(th) { background: #f5f7fa; font-weight: 600; }
  :deep(code) { background: #f5f7fa; padding: 2px 6px; border-radius: 3px; font-size: 13px; font-family: 'SF Mono', 'Menlo', 'Consolas', monospace; }
  :deep(pre) { background: #f5f7fa; padding: 12px; border-radius: 4px; overflow-x: auto; margin: 12px 0; }
  :deep(pre code) { padding: 0; background: none; }
  :deep(blockquote) { border-left: 3px solid #dcdfe6; padding-left: 12px; color: #909399; margin: 12px 0; }
  :deep(hr) { border: none; border-top: 1px solid #ebeef5; margin: 16px 0; }
  :deep(strong) { font-weight: 600; }
}

// 防止 el-descriptions label 换行
:deep(.desc-label) {
  white-space: nowrap !important;
  min-width: 100px;
}

.section-group-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 8px;
  padding-left: 4px;

  &:first-child {
    margin-top: 0;
  }
}
</style>
