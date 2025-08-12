<template>
  <div class="batch-task">
    <h1>任务跑批</h1>
    
    <!-- 步骤条 -->
    <el-steps :active="currentStep" finish-status="success" simple>
      <el-step title="选择提示词" />
      <el-step title="选择模型" />
      <el-step title="添加引用字段" />
      <el-step title="执行任务" />
    </el-steps>
    
    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 选择提示词 -->
      <div v-if="currentStep === 0" class="step">
        <h2>选择提示词</h2>
        <el-radio-group v-model="selectedPromptId" @change="handlePromptSelect">
          <el-radio
            v-for="prompt in prompts"
            :key="prompt.id"
            :label="prompt.id"
          >
            {{ prompt.title }}
          </el-radio>
        </el-radio-group>
        <div class="step-actions">
          <el-button @click="nextStep" type="primary" :disabled="!selectedPromptId">下一步</el-button>
        </div>
      </div>
      
      <!-- 步骤2: 选择模型 -->
      <div v-if="currentStep === 1" class="step">
        <h2>选择模型</h2>
        <el-radio-group v-model="selectedModelId" @change="handleModelSelect">
          <el-radio
            v-for="model in models"
            :key="model.id"
            :label="model.id"
          >
            {{ model.name }}
          </el-radio>
        </el-radio-group>
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="nextStep" type="primary" :disabled="!selectedModelId">下一步</el-button>
        </div>
      </div>
      
      <!-- 步骤3: 添加引用字段 -->
      <div v-if="currentStep === 2" class="step">
        <h2>添加引用字段</h2>
        
        <!-- 动态字段配置列表 -->
        <div v-for="(field, index) in fieldConfigs" :key="index" class="field-config">
          <el-card class="field-card">
            <div class="field-header">
              <span>引用字段 {{ index + 1 }}</span>
              <el-button 
                v-if="fieldConfigs.length > 1" 
                type="danger" 
                icon="el-icon-delete" 
                circle 
                size="small" 
                @click="removeFieldConfig(index)"
              ></el-button>
            </div>
            
            <el-form :model="field" label-width="120px">
              <el-form-item label="映射名称">
                <el-input v-model="field.selectedField" disabled placeholder="选择字段后自动生成（只读）"></el-input>
              </el-form-item>
              
              <el-form-item label="引用来源">
                <el-input v-model="field.sourceType" value="选择jsonl文件" disabled placeholder="固定值（只读）"></el-input>
              </el-form-item>
              
              <div>
                <el-form-item label="选择文件">
                  <el-select v-model="field.selectedFile" placeholder="请选择jsonl文件" @change="handleFileChange(index)">
                    <el-option
                      v-for="file in jsonlFiles"
                      :key="file"
                      :label="file"
                      :value="file"
                    ></el-option>
                  </el-select>
                </el-form-item>
                
                <el-form-item label="选择字段" v-if="field.fileFields && field.fileFields.length > 0">
                  <el-select v-model="field.selectedField" placeholder="请选择字段">
                    <el-option
                      v-for="fieldName in field.fileFields"
                      :key="fieldName"
                      :label="fieldName"
                      :value="fieldName"
                    ></el-option>
                  </el-select>
                </el-form-item>
              </div>
            </el-form>
          </el-card>
        </div>
        
        <!-- 添加字段配置按钮 -->
        <div class="add-field-button">
          <el-button type="primary" @click="addFieldConfig">添加引用字段</el-button>
        </div>
        
        <!-- 任务描述 -->
        <el-form label-width="120px">
          <el-form-item label="任务描述">
            <el-input
              v-model="taskDescription"
              type="textarea"
              :rows="4"
              placeholder="请输入任务描述，例如：比较 {映射名称1}和 {映射名称2}，哪个更好？"
            ></el-input>
          </el-form-item>
        </el-form>

        <div>特殊字段: &lt;dateTime&gt; 表示当前日期  </div>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="nextStep" type="primary">下一步</el-button>
        </div>
      </div>
      
      <!-- 步骤4: 执行任务 -->
      <div v-if="currentStep === 3" class="step">
        <h2>执行任务</h2>
        <div class="task-summary">
          <h3>任务配置摘要</h3>
          <p><strong>提示词:</strong> {{ selectedPrompt.title }}</p>
          <p><strong>模型:</strong> {{ selectedModel.name }}</p>
          <div><strong>引用字段:</strong>
            <div v-for="(field, index) in fieldConfigs" :key="index" class="field-summary">
              <p>映射名称: {{ field.selectedField }}</p>
              <p>引用来源: {{ field.sourceType }}</p>
              <p>文件: {{ field.selectedFile }}</p>
              <p>字段: {{ field.selectedField }}</p>
            </div>
          </div>
          <p><strong>任务描述:</strong> {{ taskDescription }}</p>
        </div>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="executeTask" type="primary" :loading="isExecuting">执行任务</el-button>
        </div>
        
        <!-- 进度文件显示 -->
        <div v-if="progressFileName" class="progress-file-display">
          <h3>进度文件</h3>
          <p>文件名: {{ progressFileName }}</p>
          <!-- 移除了【新窗口打开】按钮 -->
        </div>
        
        <!-- 请求日志显示 -->
        <div v-if="requestProgress.length > 0" class="request-log-display">
          <h3>请求日志</h3>
          <div class="log-content">
            <!-- 只显示最新的30条日志 -->
            <div v-for="(item, index) in requestProgress.slice(-30)" :key="index" class="log-item">
              <p><strong>{{ item.timestamp }}</strong>: {{ item.message }}</p>
            </div>
          </div>
        </div>
        
        <!-- 请求过程展示 -->
        <div v-if="isExecuting || requestProgress.length > 0" class="request-progress">
          <h3>请求过程</h3>
          <el-timeline>
            <!-- <el-timeline-item
              v-for="(item, index) in requestProgress"
              :key="index"
              :timestamp="item.timestamp"
              :type="item.type"
            >
              {{ item.message }}
            </el-timeline-item> -->
          </el-timeline>
        </div>
        
        <div v-if="executionResult" class="execution-result">
          <h3>执行结果</h3>
          <p>{{ executionResult }}</p>
        </div>
        
        <!-- 历史结果列表 -->
        <div class="history-results" v-if="batchResults.length > 0">
          <h3>历史跑批结果</h3>
          <el-table :data="batchResults" style="width: 100%" :default-sort="{prop: 'timestamp', order: 'descending'}">
            <el-table-column prop="fileName" label="结果文件" sortable></el-table-column>
            <el-table-column prop="timestamp" label="执行时间" sortable></el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" @click="downloadResult(scope.row.fileName)">下载</el-button>
                <el-button size="small" @click="viewResult(scope.row.fileName)">查看</el-button>
                <el-button size="small" type="danger" @click="deleteResult(scope.row.fileName)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, getCurrentInstance } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'BatchTask',
  setup() {
    // 获取全局axios实例
    const { proxy } = getCurrentInstance()
    const axios = proxy.$http
    
    // 步骤状态
    const currentStep = ref(0)
    
    // 提示词相关
    const prompts = ref([])
    const selectedPromptId = ref(null)
    
    // 模型相关
    const models = ref([])
    const selectedModelId = ref(null)
    
    // 字段配置列表
    const fieldConfigs = ref([
      {
        colName: '',
        sourceType: 'file',
        selectedFile: '',
        selectedField: '',
        fieldName: '',
        fileFields: []
      }
    ])
    
    // 任务描述
    const taskDescription = ref('')
    
    // 文件列表
    const jsonlFiles = ref([])
    
    // 执行状态
    const isExecuting = ref(false)
    const executionResult = ref('')
    const requestProgress = ref([])
    const batchResults = ref([])
    const progressFileName = ref('')
    
    // 修正后的计算属性
    const selectedPrompt = computed(() => {
      return prompts.value.find(p => p.id === selectedPromptId.value) || {};
    });
    
    const selectedModel = computed(() => {
      return models.value.find(m => m.id === selectedModelId.value) || {};
    });
    
    // 方法
    const nextStep = () => {
      if (currentStep.value < 3) {
        currentStep.value++
      }
    }
    
    // 添加字段配置
    const addFieldConfig = () => {
      fieldConfigs.value.push({
        sourceType: 'file',
        selectedFile: '',
        selectedField: '',
        fieldName: '',
        fileFields: []
      })
    }
    
    // 删除字段配置
    const removeFieldConfig = (index) => {
      fieldConfigs.value.splice(index, 1)
    }
    
    // 处理文件选择变化
    const handleFileChange = async (index) => {
      const selectedFile = fieldConfigs.value[index].selectedFile
      if (!selectedFile) {
        fieldConfigs.value[index].fileFields = []
        return
      }
      
      // 设置所有字段配置都使用相同的文件
      fieldConfigs.value.forEach((field, i) => {
        field.selectedFile = selectedFile
        if (i !== index) {
          field.fileFields = []
        }
      })
      
      try {
        // 调用后端API获取文件字段列表
        const response = await axios.get(`/api/jsonl-files/${selectedFile}/fields`)
        // 为所有字段配置设置相同的字段列表
        fieldConfigs.value.forEach((field) => {
          field.fileFields = response.data.fields
        })
        fieldConfigs.value[index].selectedField = ''
      } catch (error) {
        console.error('获取文件字段列表失败:', error)
        ElMessage.error('获取文件字段列表失败: ' + error.message)
        fieldConfigs.value.forEach((field) => {
          field.fileFields = []
        })
      }
    }
    
    const prevStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }
    
    const handlePromptSelect = (promptId) => {
      selectedPromptId.value = promptId
    }
    
    const handleModelSelect = (modelId) => {
      selectedModelId.value = modelId
    }
    

    
    // 在新窗口中打开进度文件
    const openProgressFile = () => {
      if (progressFileName.value) {
        // 在新窗口中打开进度文件
        window.open(`/api/progress/${progressFileName.value}`, '_blank');
      } else {
        ElMessage.warning('执行任务后将生成进度文件');
      }
    }
    
    const executeTask = async () => {
      // 检查是否所有字段配置都选择了文件
      for (let i = 0; i < fieldConfigs.value.length; i++) {
        if (!fieldConfigs.value[i].selectedFile) {
          ElMessage.error(`请为第${i + 1}个字段配置选择JSONL文件`)
          return
        }
      }
      
      // 自动生成进度文件名
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5).replace('T', '_');
      const randomString = Math.random().toString(36).substring(2, 10);
      progressFileName.value = `progress_${timestamp}_${randomString}.log`;
      
      isExecuting.value = true
      executionResult.value = ''
      requestProgress.value = []
      
      // 添加开始执行任务的消息
      requestProgress.value.push({
        timestamp: new Date().toLocaleTimeString(),
        type: 'primary',
        message: '开始执行任务'
      })
      
      // 用于存储轮询的定时器
      let progressInterval = null;
      // 用于跟踪上次读取的位置
      let lastPosition = 0;
      
      try {
        // 调用后端API执行实际的任务，传递前端生成的进度文件名
        const response = await axios.post('/api/batch-task', {
          promptId: selectedPromptId.value,
          modelId: selectedModelId.value,
          fieldConfigs: fieldConfigs.value,
          taskDescription: taskDescription.value,
          progressFile: progressFileName.value  // 传递前端生成的进度文件名
        }, {
          timeout: 300000
        });

        // 使用前端生成的进度文件名启动轮询
        if (progressFileName.value) {
          progressInterval = setInterval(async () => {
            const progressResponse = await axios.get(`/api/progress/${progressFileName.value}`, { timeout: 1000 });
            
            if (progressResponse.data.content?.trim()) {
              const newProgressItems = progressResponse.data.content
                .split('\n')
                .filter(line => line.trim())
                .map(line => ({
                  timestamp: '',
                  type: 'info',
                  message: line
                }));
              
              // 只保留最新的日志条目，限制总数不超过50条
              requestProgress.value = newProgressItems;
              //lastPosition = progressResponse.data.position || lastPosition;

              console.log("progressResponse.data.content",progressResponse.data.content)

              // 处理任务完成状态
              if (progressResponse.data.content.match(/任务执行(完成|失败)/)) {
                clearInterval(progressInterval);
                progressInterval = null;
                
                const resultResponse = await axios.get('/api/batch-results', { timeout: 300000 });
                if (resultResponse.data.results?.length > 0) {
                  const latestResult = resultResponse.data.results[0];
                  const resultContent = await axios.get(`/api/batch-results/${latestResult.fileName}`, { timeout: 300000 });
                  
                  requestProgress.value.push({
                    timestamp: new Date().toLocaleTimeString(),
                    type: 'success',
                    message: `任务执行完成，结果已保存到${latestResult.fileName}，共处理${resultContent.data.length}条记录。`
                  });
                  executionResult.value = `任务执行完成，共处理${resultContent.data.length}条记录。`;
                }
              }
            }
          }, 1000);

          // 5分钟后自动清除轮询
          setTimeout(() => clearInterval(progressInterval), 300000);
        }

        // 任务执行结果已经在轮询中处理，这里不再重复处理
        // 仅在需要时设置 executionResult 的默认值
        if (!executionResult.value) {
          executionResult.value = '任务已提交，正在处理中...';
        }

        ElMessage.success('任务执行成功！');
      } catch (error) {
        console.error('任务执行失败:', error);
        clearInterval(progressInterval);
        
        const errorMessage = error.response?.data?.detail || error.message;
        requestProgress.value.push({
          timestamp: new Date().toLocaleTimeString(),
          type: 'danger',
          message: `任务执行失败: ${errorMessage}`
        });
        executionResult.value = `执行失败: ${errorMessage}`;
        ElMessage.error(`任务执行失败: ${errorMessage}`);
      } finally {
        isExecuting.value = false;
      }
  }
  
  // 获取提示词和模型数据
  const fetchPromptsAndModels = async () => {
      try {
        // 获取提示词数据
        const promptResponse = await axios.get('/api/prompts', { timeout: 300000 }) // 30秒超时
        prompts.value = promptResponse.data
        
        // 默认选择第一个提示词
        if (prompts.value.length > 0) {
          selectedPromptId.value = prompts.value[0].id
        }
        
        // 获取模型数据
        const modelResponse = await axios.get('/api/models', { timeout: 300000 }) // 30秒超时
        models.value = modelResponse.data
        
        // 默认选择第一个模型
        if (models.value.length > 0) {
          selectedModelId.value = models.value[0].id
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        ElMessage.error('获取提示词或模型数据失败: ' + error.message)
      }
    }
    
    // 获取JSONL文件列表
    const fetchJsonlFiles = async () => {
      try {
        const response = await axios.get('/api/jsonl-files', { timeout: 300000 }) // 30秒超时
        jsonlFiles.value = response.data.files
      } catch (error) {
        console.error('获取文件列表失败:', error)
        ElMessage.error('获取JSONL文件列表失败: ' + error.message)
      }
    }
    
    // 获取批处理结果列表
    const fetchBatchResults = async () => {
      try {
        const response = await axios.get('/api/batch-results', { timeout: 300000 });
        console.log("response",response)
        batchResults.value = response.data.results || [];
      } catch (error) {
        console.error('获取批处理结果列表失败:', error);
        ElMessage.error('获取批处理结果列表失败: ' + error.message);
      }
    };
    
    // 下载结果文件
    const downloadResult = (fileName) => {
      // 将文件扩展名从.jsonl改为.csv
      const csvFileName = fileName.replace(/\.jsonl$/, '.csv');
      const link = document.createElement('a');
      link.href = `/api/batch-results/${fileName}`;
      link.download = csvFileName;
      link.click();
    };
    
    // 查看结果文件
    const viewResult = async (fileName) => {
      try {
        const response = await axios.get(`/api/batch-results/${fileName}`, { timeout: 300000 });
        // 这里可以添加一个模态框来显示结果内容
        console.log('查看结果:', response.data);
        ElMessage.info('结果内容已输出到控制台');
      } catch (error) {
        console.error('查看结果失败:', error);
        ElMessage.error('查看结果失败: ' + error.message);
      }
    };
    
    // 删除结果文件
    const deleteResult = async (fileName) => {
      try {
        await axios.delete(`/api/batch-results/${fileName}`, { timeout: 300000 });
        ElMessage.success('文件删除成功');
        // 重新获取批处理结果列表
        await fetchBatchResults();
      } catch (error) {
        console.error('删除结果失败:', error);
        ElMessage.error('删除结果失败: ' + error.message);
      }
    };
    
    // 组件挂载时获取数据
    onMounted(() => {
      console.log("跑批结果....")
      fetchPromptsAndModels();
      fetchJsonlFiles();
      fetchBatchResults();
    })
    
    return {
      currentStep,
      prompts,
      selectedPromptId,
      selectedPrompt,
      models,
      selectedModelId,
      selectedModel,
      fieldConfigs,
      taskDescription,
      jsonlFiles,
      isExecuting,
      executionResult,
      requestProgress,
      batchResults,
      progressFileName,
      nextStep,
      prevStep,
      handlePromptSelect,
      handleModelSelect,
      openProgressFile,
      executeTask,
      addFieldConfig,
      removeFieldConfig,
      handleFileChange,
      downloadResult,
      viewResult,
      deleteResult
    }
  }
}
</script>

<style scoped>
.step {
  margin-top: 20px;
}

.step-actions {
  margin-top: 20px;
}

.task-summary {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
}

.execution-result {
  margin-top: 20px;
  padding: 15px;
  background-color: #e8f5e9;
  border-radius: 4px;
}

.field-config {
  margin-bottom: 20px;
}

.field-card {
  margin-bottom: 15px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.add-field-button {
  margin: 20px 0;
}

.field-summary {
  margin-left: 20px;
}

.history-results {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.history-results h3 {
  margin-top: 0;
  color: #333;
}

.progress-file-display {
  margin-top: 20px;
  padding: 15px;
  background-color: #e8f5e9;
  border-radius: 4px;
  border: 1px solid #c8e6c9;
}

.progress-file-display h3 {
  margin-top: 0;
  color: #2e7d32;
}

.progress-file-display p {
  margin: 10px 0;
  font-weight: bold;
}

.request-log-display {
  margin-top: 20px;
  padding: 15px;
  background-color: #f1f8ff;
  border-radius: 4px;
  border: 1px solid #c5e1ff;
}

.request-log-display h3 {
  margin-top: 0;
  color: #0366d6;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.log-item {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.log-item:last-child {
  border-bottom: none;
}
</style>