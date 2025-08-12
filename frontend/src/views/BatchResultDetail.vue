<template>
  <div class="batch-result-detail">
    <h1>跑批结果详情</h1>
    <div v-if="loading" class="loading">
      <el-skeleton />
    </div>
    <div v-else>
      <el-card>
        <template #header>
          <div class="card-header">
            <span>{{ fileName }}</span>
            <el-button class="button" type="primary" @click="downloadResult">下载</el-button>
          </div>
        </template>
        <el-table :data="results" height="500" style="width: 100%">
          <el-table-column prop="system_prompt" label="系统提示词" width="300"></el-table-column>
          <el-table-column prop="task_description" label="任务描述" width="300"></el-table-column>
          <el-table-column prop="reasoning_content" label="Reasoning Content" width="300"></el-table-column>
          <el-table-column prop="content" label="Content"></el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, getCurrentInstance } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'BatchResultDetail',
  setup() {
    const { proxy } = getCurrentInstance()
    const axios = proxy.$http
    const route = useRoute()
    
    const fileName = ref('')
    const results = ref([])
    const loading = ref(true)
    
    // 获取结果详情
    const fetchResultDetail = async () => {
      try {
        loading.value = true
        fileName.value = route.params.id
        const response = await axios.get(`/api/batch-results/${fileName.value}`)
        results.value = response.data
      } catch (error) {
        console.error('获取结果详情失败:', error)
        ElMessage.error('获取结果详情失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 下载结果文件
    const downloadResult = () => {
      // 将文件扩展名从.jsonl改为.csv
      const csvFileName = fileName.value.replace(/\.jsonl$/, '.csv');
      const link = document.createElement('a');
      link.href = `/api/download-batch-result/${fileName.value}`;
      link.download = csvFileName;
      link.click();
    }
    
    // 组件挂载时获取数据
    onMounted(() => {
      fetchResultDetail()
    })
    
    return {
      fileName,
      results,
      loading,
      downloadResult
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading {
  padding: 20px;
}
</style>