<template>
  <el-container class="main-layout">
    <el-container>
      <el-header class="main-header">
        <el-button text type="primary" @click="router.push('/copyright')">首页</el-button>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
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
