<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <div class="login-kicker">软件著作权材料工作台</div>
      <h1 id="login-title">登录秒著</h1>
      <p class="login-intro">验证身份后继续管理申请与生成任务。</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="submit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model.trim="form.username"
            autocomplete="username"
            placeholder="输入用户名"
            size="large"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            autocomplete="current-password"
            placeholder="输入密码"
            show-password
            size="large"
            type="password"
            @keyup.enter="submit"
          />
        </el-form-item>

        <el-alert
          v-if="loginError"
          :title="loginError"
          class="login-error"
          type="error"
          :closable="false"
          show-icon
        />

        <el-button
          class="login-submit"
          type="primary"
          size="large"
          :loading="submitting"
          native-type="submit"
        >
          登录并继续
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const loginError = ref('')
const form = reactive({ username: '', password: '' })

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function redirectTarget() {
  const value = route.query.redirect
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')
    ? value
    : '/copyright'
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  loginError.value = ''
  try {
    await authApi.login(form)
    await router.replace(redirectTarget())
  } catch (error: any) {
    loginError.value = error.response?.data?.detail || '登录失败，请检查用户名和密码。'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 28px;
  background:
    radial-gradient(circle at 88% 12%, rgba(64, 158, 255, 0.16), transparent 28rem),
    linear-gradient(135deg, #f3f8ff 0%, #fafcff 48%, #edf5ff 100%);
}

.login-panel {
  width: min(100%, 424px);
  padding: 40px;
  border: 1px solid rgba(167, 197, 229, 0.75);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 22px 60px rgba(50, 92, 140, 0.14);
}

.login-kicker {
  margin-bottom: 14px;
  color: #3c80c5;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.13em;
}

h1 {
  margin: 0;
  color: #1f2d3d;
  font-size: clamp(30px, 5vw, 38px);
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.login-intro {
  margin: 12px 0 30px;
  color: #6b7b8d;
  font-size: 14px;
  line-height: 1.7;
}

.login-error {
  margin: -4px 0 16px;
}

.login-submit {
  width: 100%;
  margin-top: 8px;
  font-weight: 600;
}

@media (max-width: 480px) {
  .login-page {
    padding: 16px;
  }

  .login-panel {
    padding: 30px 24px;
  }
}
</style>
