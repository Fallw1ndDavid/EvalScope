<template>
  <div class="batch-results">
    <h1>跑批结果</h1>
    <el-row type="flex" justify="end" class="pagination-row">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-row>
    
    <div v-if="loading" class="loading">
      <el-skeleton />
    </div>
    
    <div v-else>
      <el-table :data="pagedResults" style="width: 100%" @row-click="viewResult">
        <el-table-column prop="fileName" label="文件名" width="300"></el-table-column>
        <el-table-column prop="modTime" label="生成时间" width="200">
          <template #default="scope">
            {{ formatDate(scope.row.modTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click.stop="downloadResult(scope.row.fileName)">下载</el-button>
            <el-button size="small" type="danger" @click.stop="deleteResult(scope.row.fileName)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="results.length === 0" class="no-results">
        <p>暂无跑批结果</p>
      </div>
    </div>

    <el-row type="flex" justify="end" class="pagination-row">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'BatchResults',
  setup() {
    const { proxy } = getCurrentInstance()
    const axios = proxy.$http
    
    const results = ref([])
    const loading = ref(true)
    const dialogVisible = ref(false)
    const selectedFile = ref('')
    const selectedResult = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const pagedResults = ref([])
    
    // 格式化时间
    const formatDate = (timestamp) => {
      const date = new Date(timestamp * 1000)
      return date.toLocaleString()
    }
    
    // 获取跑批结果列表
    const fetchResults = async () => {
      try {
        loading.value = true
        // 添加分页参数
        const response = await axios.get('/api/batch-results', {
          params: {
            page: currentPage.value,
            pageSize: pageSize.value
          }
        })
        results.value = response.data.results
        total.value = response.data.total
        // 计算分页数据
        updatePagedResults()
      } catch (error) {
        console.error('获取跑批结果列表失败:', error)
        ElMessage.error('获取跑批结果列表失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    // 更新分页数据
    const updatePagedResults = () => {
      pagedResults.value = results.value
      // 如果后端不支持分页，前端进行分页处理
      // const startIndex = (currentPage.value - 1) * pageSize.value
      // const endIndex = startIndex + pageSize.value
      // pagedResults.value = results.value.slice(startIndex, endIndex)
    }

    // 处理页码变化
    const handleCurrentChange = (current) => {
      currentPage.value = current
      fetchResults()
    }

    // 处理每页条数变化
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      fetchResults()
    }
    
    // 查看结果详情
    const viewResult = (row) => {
      // 导航到结果详情页面
      proxy.$router.push(`/batch-results/${row.fileName}`)
    }
    
    // 下载结果文件
    const downloadResult = (fileName) => {
      // 将文件扩展名从.jsonl改为.csv
      const csvFileName = fileName.replace(/\.jsonl$/, '.csv');
      const link = document.createElement('a');
      link.href = `/api/download-batch-result/${fileName}`;
      link.download = csvFileName;
      link.click();
    }
    
    // 删除结果文件
    const deleteResult = async (fileName) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除文件 ${fileName} 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await axios.delete(`/api/batch-results/${fileName}`)
        ElMessage.success('删除成功')
        // 重新获取结果列表
        fetchResults()
      } catch (error) {
        // 如果用户取消删除操作，error 是 'cancel' 字符串
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }
    
    // 组件挂载时获取数据
    onMounted(() => {
      fetchResults()
    })
    
    return {
      results,
      pagedResults,
      loading,
      dialogVisible,
      selectedFile,
      selectedResult,
      currentPage,
      pageSize,
      total,
      formatDate,
      viewResult,
      downloadResult,
      deleteResult,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.loading {
  padding: 20px;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.pagination-row {
  margin-top: 20px;
  margin-bottom: 20px;
}
</style>