<template>
  <div class="model-management">
    <h1>模型管理</h1>
    
    <!-- 添加/编辑模型表单 -->
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>{{ isEditing ? '编辑模型' : '添加模型' }}</span>
        </div>
      </template>
      
      <el-form :model="modelForm" :rules="rules" ref="modelFormRef" label-width="120px">
        
        
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="modelForm.name"></el-input>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input v-model="modelForm.description" type="textarea"></el-input>
        </el-form-item>
        
        <el-form-item label="自定义Header" prop="customHeader">
          <el-input v-model="modelForm.customHeader" type="textarea" placeholder='例如: {"Authorization": "Bearer token"}'></el-input>
        </el-form-item>
        
        <el-form-item label="URL" prop="url">
          <el-input v-model="modelForm.url" placeholder="例如: https://api.example.com/v1/chat/completions"></el-input>
        </el-form-item>
        
        <el-form-item label="其他入参" prop="otherParams">
          <el-input v-model="modelForm.otherParams" type="textarea" placeholder='例如: {"model": "gpt-3.5-turbo", "temperature": 0.7}'></el-input>
        </el-form-item>

        <el-form-item label="API密钥" prop="apiKey">
          <el-input v-model="modelForm.apiKey" type="textarea" placeholder='模型的API密钥，如sk-开头的字符串'></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitForm">{{ isEditing ? '更新' : '添加' }}</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 模型列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模型列表</span>
        </div>
      </template>
      
      <el-table :data="models" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="模型名称">
          <template #default="scope">
            <el-link type="primary" @click="showModelDetails(scope.row)">{{ scope.row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述"></el-table-column>
        <el-table-column prop="url" label="URL"></el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editModel(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteModel(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 模型详情对话框 -->
    <el-dialog v-model="dialogVisible" title="模型详情" width="50%">
      <el-form label-width="120px">
        <el-form-item label="模型名称">
          <el-input v-model="currentModel.name" disabled></el-input>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="currentModel.description" type="textarea" disabled></el-input>
        </el-form-item>
        <el-form-item label="自定义Header">
          <el-input v-model="currentModel.customHeader" type="textarea" disabled></el-input>
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="currentModel.url" disabled></el-input>
        </el-form-item>
        <el-form-item label="其他入参">
          <el-input v-model="currentModel.otherParams" type="textarea" disabled></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 获取全局axios实例
const { proxy } = getCurrentInstance()
const axios = proxy.$http

// 数据
const models = ref([])
const loading = ref(false)
const isEditing = ref(false)
const dialogVisible = ref(false)
const currentModel = ref({
  name: '',
  description: '',
  customHeader: '',
  url: '',
  otherParams: ''
})

// 表单数据
const modelForm = ref({
  name: '',
  description: '',
  customHeader: '',
  url: '',
  otherParams: '',
  apiKey: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入URL', trigger: 'blur' }
  ]
}

// 表单引用
const modelFormRef = ref(null)

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/models')
    models.value = response.data
  } catch (error) {
    ElMessage.error('获取模型列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await modelFormRef.value.validate()
    
    // 处理customHeader和otherParams字段，确保它们是有效的JSON
    const formData = {...modelForm.value};
    
    // 为新模型生成唯一ID
    if (!isEditing.value) {
      // 生成比现有模型最大ID大1的新ID
      const maxId = models.value.reduce((max, model) => Math.max(max, model.id), 0);
      formData.id = maxId + 1;
    } else {
      // 编辑模式下使用现有ID
      formData.id = currentModel.value.id;
    }
    
    // 验证并清理customHeader
    if (formData.customHeader) {
      try {
        // 处理可能的转义引号
        const cleanedHeader = formData.customHeader.replace(/\\"/g, '"');
        // 验证JSON格式
        JSON.parse(cleanedHeader);
        formData.customHeader = cleanedHeader;
      } catch (e) {
        ElMessage.error('自定义Header必须是有效的JSON字符串');
        return;
      }
    } else {
      formData.customHeader = '';
    }
    
    // 验证并清理otherParams
    if (formData.otherParams) {
      try {
        // 处理可能的转义引号
        const cleanedParams = formData.otherParams.replace(/\\"/g, '"');
        // 验证JSON格式
        JSON.parse(cleanedParams);
        formData.otherParams = cleanedParams;
      } catch (e) {
        ElMessage.error('其他入参必须是有效的JSON字符串');
        return;
      }
    } else {
      formData.otherParams = '';
    }
    
    if (isEditing.value) {
      // 更新模型
      await axios.put(`/api/models/${currentModel.value.id}`, formData)
      ElMessage.success('模型更新成功')
    } else {
      // 添加模型
      await axios.post('/api/models', formData)
      ElMessage.success('模型添加成功')
    }
    
    resetForm()
    fetchModels()
  } catch (error) {
    if (error.response && error.response.status === 400) {
      ElMessage.error('模型ID已存在')
    } else if (error.response && error.response.status === 422) {
      ElMessage.error('数据格式不正确，请检查输入的JSON格式');
    } else {
      ElMessage.error((isEditing.value ? '更新' : '添加') + '模型失败: ' + error.message)
    }
  }
}

// 编辑模型
  const editModel = (model) => {
    modelForm.value = { ...model }
    currentModel.value = { ...model }
    isEditing.value = true
  }

// 删除模型
const deleteModel = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模型吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 删除模型
      await axios.delete(`/api/models/${id}`)
    ElMessage.success('模型删除成功')
    fetchModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除模型失败: ' + error.message)
    }
  }
}

// 显示模型详情
const showModelDetails = (model) => {
  currentModel.value = { ...model }
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  modelFormRef.value.resetFields()
  isEditing.value = false
}

// 组件挂载时获取数据
onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.mb-4 {
  margin-bottom: 1rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>