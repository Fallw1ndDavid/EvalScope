<template>
  <div class="nginx-log-parser">
    <h2>NGINX日志解析</h2>
    <el-upload
      class="upload-demo"
      drag
      action="/api/parse-nginx-log"
      :auto-upload="true"
      :on-change="handleChange"
      :on-remove="handleRemove"
      :file-list="fileList"
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          请上传NGINX日志文件（基础解析）
        </div>
      </template>
    </el-upload>
    
    <div v-if="parsing" class="parsing-status">
      <el-skeleton />
      <p>正在解析日志文件并生成CSV...</p>
    </div>
    
    <h3>按Agent ID汇总</h3>
    <el-upload
      class="upload-demo"
      drag
      action="/api/parse-nginx-log-summary"
      :auto-upload="true"
      :on-change="handleChangeSummary"
      :on-remove="handleRemoveSummary"
      :file-list="fileListSummary"
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          请上传NGINX日志文件（按agent_id汇总最近2天每小时请求数量及平均request_length）
        </div>
      </template>
    </el-upload>
    
    <div v-if="parsingSummary" class="parsing-status">
      <el-skeleton />
      <p>正在按agent_id汇总日志数据并生成CSV...</p>
    </div>
  </div>
</template>

<script>
import { ref, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

export default {
  name: 'NginxLogParser',
  components: {
    UploadFilled
  },
  setup() {
    const { proxy } = getCurrentInstance()
    const axios = proxy.$http
    
    const fileList = ref([])
    const parsing = ref(false)
    const parsedFileName = ref('')
    
    const handleChange = async (file, fileList) => {
      // 文件改变时自动触发解析
      fileList.value = [...fileList]
      
      // 如果是新添加的文件，自动开始解析
      if (file.status === 'ready') {
        // 使用nextTick确保fileList.value更新完成后再执行上传
        await proxy.$nextTick()
        await submitUpload()
      }
    }
    
    const handleRemove = (file, fileList) => {
      fileList.value = [...fileList]
    }
    
    const submitUpload = async () => {
      if (fileList.value.length === 0) {
        ElMessage.warning('请先选择文件')
        return
      }
      
      // 获取第一个文件进行解析
      const file = fileList.value[0].raw || fileList.value[0]
      
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        parsing.value = true
        const response = await axios.post('/api/parse-nginx-log', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // 从响应中获取文件名和下载链接
        parsedFileName.value = response.data.fileName || response.data.filename || ''
        const downloadUrl = response.data.downloadUrl
        
        // 自动触发下载
        if (downloadUrl) {
          // 使用setTimeout确保提示信息能够显示
          setTimeout(() => {
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = parsedFileName.value.replace('.log', '.csv')
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            ElMessage.success('日志解析完成，文件已开始下载')
          }, 100)
        } else {
          ElMessage.success('日志解析完成')
        }
      } catch (error) {
        console.error('解析失败:', error)
        ElMessage.error('解析失败: ' + (error.message || '未知错误'))
      } finally {
        parsing.value = false
      }
    }
    
    // 汇总功能相关变量和方法
    const fileListSummary = ref([])
    const parsingSummary = ref(false)
    const parsedFileNameSummary = ref('')
    
    const handleChangeSummary = async (file, fileList) => {
      // 文件改变时自动触发解析
      fileListSummary.value = [...fileList]
      
      // 如果是新添加的文件，自动开始解析
      if (file.status === 'ready') {
        // 使用nextTick确保fileListSummary.value更新完成后再执行上传
        await proxy.$nextTick()
        await submitUploadSummary()
      }
    }
    
    const handleRemoveSummary = (file, fileList) => {
      fileListSummary.value = [...fileList]
    }
    
    const submitUploadSummary = async () => {
      if (fileListSummary.value.length === 0) {
        ElMessage.warning('请先选择文件')
        return
      }
      
      // 获取第一个文件进行解析
      const file = fileListSummary.value[0].raw || fileListSummary.value[0]
      
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        parsingSummary.value = true
        const response = await axios.post('/api/parse-nginx-log-summary', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // 从响应中获取文件名和下载链接
        parsedFileNameSummary.value = response.data.fileName || response.data.filename || ''
        const downloadUrl = response.data.downloadUrl
        
        // 自动触发下载
        if (downloadUrl) {
          // 使用setTimeout确保提示信息能够显示
          setTimeout(() => {
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = parsedFileNameSummary.value.replace('.log', '.csv')
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            ElMessage.success('日志汇总完成，文件已开始下载')
          }, 100)
        } else {
          ElMessage.success('日志汇总完成')
        }
      } catch (error) {
        console.error('汇总失败:', error)
        ElMessage.error('汇总失败: ' + (error.message || '未知错误'))
      } finally {
        parsingSummary.value = false
      }
    }
    
    // 移除了downloadCSV方法，因为现在在解析完成后会自动下载
    
    return {
      fileList,
      parsing,
      parsedFileName,
      handleChange,
      handleRemove,
      submitUpload,
      // 汇总功能相关返回
      fileListSummary,
      parsingSummary,
      parsedFileNameSummary,
      handleChangeSummary,
      handleRemoveSummary,
      submitUploadSummary
    }
  }
}
</script>

<style scoped>
.nginx-log-parser {
  padding: 20px;
}

.upload-demo {
  margin-bottom: 20px;
}

.parsing-status {
  text-align: center;
  padding: 20px;
}

.parsed-data {
  margin-top: 20px;
}
</style>