import client from './client'

export interface CreateExportTaskRequest {
  format:
    | 'application-form-txt'
    | 'manual-word'
    | 'manual-pdf'
    | 'source-code-word'
    | 'source-code-pdf'
    | 'all'
}

export interface ExportTaskRecord {
  id: number
  application_id: number
  format: string
  status: string
  file_name: string | null
  file_size: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
}

export function createExportTask(appId: number, data: CreateExportTaskRequest) {
  return client.post<ExportTaskRecord>(`/applications/${appId}/export-tasks`, data)
}

export function listExportTasks(page = 1, pageSize = 20) {
  return client.get<PaginatedResult<ExportTaskRecord>>('/export-tasks', { params: { page, page_size: pageSize } })
}

export function getLatestExports(appId: number) {
  return client.get<ExportTaskRecord[]>(`/applications/${appId}/export-tasks/latest`)
}

export function deleteExportTask(taskId: number) {
  return client.delete<{ message: string }>(`/export-tasks/${taskId}`)
}

export function deleteFailedExportTasks() {
  return client.delete<{ message: string; count: number }>('/export-tasks/failed/batch')
}
