<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="aside-container">
      <div class="logo" @click="toggleSidebar">
        <el-icon v-if="isCollapsed"><Expand /></el-icon>
        <span v-else>Cloud Manager</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
        :collapse="isCollapsed"
        :collapse-transition="false"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>
        
        <el-menu-item index="/tenant">
          <el-icon><Office /></el-icon>
          <template #title>My Portal</template>
        </el-menu-item>
        
        <el-sub-menu index="compute">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>Compute</span>
          </template>
          <el-menu-item index="/vms">Virtual Machines</el-menu-item>
          <el-menu-item index="/hosts">Hosts</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/topology">
          <el-icon><Connection /></el-icon>
          <template #title>Topology</template>
        </el-menu-item>
        
        <el-sub-menu index="storage">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>Storage</span>
          </template>
          <el-menu-item index="/datastores">Datastores</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="network">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>Network</span>
          </template>
          <el-menu-item index="/networks">Networks</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/tasks">
          <el-icon><Document /></el-icon>
          <template #title>Tasks</template>
        </el-menu-item>
        
        <el-menu-item index="/logs">
          <el-icon><List /></el-icon>
          <template #title>Logs</template>
        </el-menu-item>
        
        <el-menu-item index="/users" v-if="isAdmin">
          <el-icon><User /></el-icon>
          <template #title>Users</template>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>Settings</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header-container">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">Home</el-breadcrumb-item>
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.label }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" style="margin-right: 8px">{{ authStore.user?.username?.[0]?.toUpperCase() }}</el-avatar>
              <span class="username">{{ authStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">Profile</el-dropdown-item>
                <el-dropdown-item command="settings">Settings</el-dropdown-item>
                <el-dropdown-item command="logout" divided>Logout</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main-container">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { House, Cpu, Box, Connection, Document, Setting, User, List, Monitor, ArrowDown, Expand, Office } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const isCollapsed = ref(false)

const isAdmin = computed(() => authStore.user?.username === 'admin')

const breadcrumbs = computed(() => {
  const paths = route.path.split('/').filter(Boolean)
  return paths.map((p, i) => ({
    path: '/' + paths.slice(0, i + 1).join('/'),
    label: p.charAt(0).toUpperCase() + p.slice(1).replace(/-/g, ' ')
  }))
})

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
}

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'profile') {
    router.push('/users')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
}

.aside-container {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #2b3a4a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.logo span {
  white-space: nowrap;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 220px;
}

.el-menu--collapse {
  width: 64px;
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

.header-container {
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 8px;
  border-radius: 4px;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  color: #606266;
  margin-right: 4px;
}

.main-container {
  background-color: #f0f2f5;
  padding: 16px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .aside-container {
    position: fixed;
    z-index: 1000;
    height: 100vh;
  }
  
  .header-left {
    display: none;
  }
  
  .username {
    display: none;
  }
}
</style>
