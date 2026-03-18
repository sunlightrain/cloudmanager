<template>
  <el-container class="layout-container">
    <el-aside width="220px">
      <div class="logo">Cloud Manager</div>
      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>Dashboard</span>
        </el-menu-item>
        
        <el-sub-menu index="compute">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>Compute</span>
          </template>
          <el-menu-item index="/vms">Virtual Machines</el-menu-item>
          <el-menu-item index="/hosts">Hosts</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="storage">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>Storage</span>
          </template>
          <el-menu-item index="/datastores">Datastores</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="network">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>Network</span>
          </template>
          <el-menu-item index="/networks">Networks</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/tasks">
          <el-icon><Document /></el-icon>
          <span>Tasks</span>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>Settings</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-right">
          <span class="username">{{ authStore.user?.username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">
            Logout
          </el-button>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { House, Cpu, Box, Connection, Document, Setting } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #2b3a4a;
}

.el-menu-vertical {
  border: none;
  background-color: #304156;
}

.el-menu-item, .el-sub-menu__title {
  color: #bfcbd9;
}

.el-menu-item:hover,
.el-sub-menu__title:hover,
.el-menu-item.is-active,
.el-sub-menu.is-active > .el-sub-menu__title {
  background-color: #263445;
  color: #409eff;
}

.el-header {
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  color: #606266;
}

.el-main {
  background-color: #f0f2f5;
}
</style>
