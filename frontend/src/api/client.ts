import axios from 'axios'
import { ElMessage } from 'element-plus'

declare module 'axios' {
  export interface AxiosRequestConfig {
    silentError?: boolean
    skipAuthRedirect?: boolean
  }
}

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor: handle errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { data } = error.response
      const msg = data?.detail || data?.message || '请求失败'
      const config = error.config || {}

      if (
        error.response.status === 401 &&
        !config.skipAuthRedirect &&
        window.location.pathname !== '/login'
      ) {
        const redirect = `${window.location.pathname}${window.location.search}`
        window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
      }

      if (!config.silentError) {
        ElMessage.error(msg)
      }
    } else {
      if (!error.config?.silentError) {
        ElMessage.error('网络连接失败，请检查网络')
      }
    }
    return Promise.reject(error)
  },
)

export default client
