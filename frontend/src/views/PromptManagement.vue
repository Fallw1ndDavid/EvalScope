<template>
  <div class="prompt-management">
    <h1>提示词管理</h1>
    <PromptForm @prompt-added="refreshPrompts" />
    <PromptList ref="promptList" />
  </div>
</template>

<script>
import PromptForm from '../components/PromptForm.vue'
import PromptList from '../components/PromptList.vue'

export default {
  name: 'PromptManagement',
  components: {
    PromptForm,
    PromptList
  },
  methods: {
    refreshPrompts() {
      // 调用子组件的fetchPrompts方法刷新列表
      this.$refs.promptList.fetchPrompts()
    }
  }
}
</script>

<style scoped>
.prompt-management {
  padding: 20px;
}
</style>