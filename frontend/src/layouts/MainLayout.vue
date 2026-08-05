<template>
  <el-container class="main-layout">
    <el-container>
      <el-header class="main-header">
        <el-button text type="primary" @click="router.push('/copyright')">首页</el-button>
        <el-button text @click="handleLogout">退出登录</el-button>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'

const router = useRouter()

async function handleLogout() {
  try {
    await authApi.logout()
    ElMessage.success('已退出登录')
    await router.replace('/login')
  } catch {
    // The global interceptor already displays the error and redirects if needed.
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid $border-color;
  background: #fff;
}

.main-content {
  background: #f5f7fa;
  padding: $content-padding;
}


.footer-contact {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.footer-sep {
  color: #dcdfe6;
  margin: 0 4px;
}
</style>
