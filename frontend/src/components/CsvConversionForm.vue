<template>
  <div class="csv-conversion-form">
    <h2>csv转换jsonl</h2>
    <el-steps :active="currentStep" finish-status="success">
      <el-step title="上传CSV文件"></el-step>
      <el-step title="字段映射"></el-step>
      <el-step title="导出JSONL文件"></el-step>
    </el-steps>
    
    <div class="step-content">
      <!-- 第一步：上传CSV文件 -->
      <div v-if="currentStep === 0" class="step-1">
        <el-upload
          class="upload-demo"
          drag
          action="/api/upload-csv"
          :on-success="handleCsvUploadSuccess"
          :on-error="handleCsvUploadError"
          accept=".csv">
          <i class="el-icon-upload"></i>
          <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          <div class="el-upload__tip" slot="tip">只能上传csv文件</div>
        </el-upload>
        <el-button style="margin-top: 20px" @click="nextStep" :disabled="!csvUploaded">下一步</el-button>
      </div>
      
      <!-- 第二步：字段映射 -->
      <div v-if="currentStep === 1" class="step-2">
        <div v-for="(field, index) in jsonlFields" :key="index" class="field-mapping">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-input v-model="field.jsonlField" placeholder="JSONL字段名"></el-input>
            </el-col>
            <el-col :span="5">
              <el-select v-model="field.mappingType" placeholder="映射类型" @change="handleMappingTypeChange(field)">
                <el-option label="映射单个字段" value="single"></el-option>
                <el-option label="映射多个字段" value="multiple"></el-option>
                <el-option label="自定义文本" value="custom"></el-option>
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-if="field.mappingType === 'single'" v-model="field.selectedColumn" placeholder="选择CSV列">
                <el-option
                  v-for="column in csvColumns"
                  :key="column"
                  :label="column"
                  :value="column">
                </el-option>
              </el-select>
              <el-input
                  v-if="field.mappingType === 'multiple'"
                  v-model="field.multipleMapping"
                  placeholder='row["列名1"] + ...'>
                  <template #append>
                    <el-button @click="parseMultipleMapping(field)" size="small">解析</el-button>
                  </template>
                </el-input>
              <el-input
                v-if="field.mappingType === 'custom'"
                v-model="field.customText"
                placeholder="任意文本">
              </el-input>
            </el-col>
            <el-col :span="4" v-if="field.mappingType === 'single'">
              <el-select v-model="field.filterType" placeholder="筛选条件" @change="handleFilterTypeChange(field)">
                <el-option label="任意" value="any"></el-option>
                <el-option label="不为空" value="not_empty"></el-option>
                <el-option label="等于特定值" value="equals"></el-option>
                <el-option label="大于" value="greater_than"></el-option>
                <el-option label="小于" value="less_than"></el-option>
                <el-option label="大于等于" value="greater_or_equal"></el-option>
                <el-option label="小于等于" value="less_or_equal"></el-option>
              </el-select>
            </el-col>
            <el-col :span="3" v-if="field.mappingType === 'single'">
              <el-input
                v-if="['equals', 'greater_than', 'less_than', 'greater_or_equal', 'less_or_equal'].includes(field.filterType)"
                v-model="field.filterValue"
                placeholder="值">
              </el-input>
            </el-col>
            <el-col :span="2">
              <el-button @click="removeField(index)" type="danger" size="small">删除</el-button>
            </el-col>
          </el-row>
        </div>
        <el-button @click="addField" type="primary" icon="el-icon-plus">添加字段</el-button>
        <div class="step-buttons">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="nextStep" type="primary">下一步</el-button>
        </div>
      </div>
      
      <!-- 第三步：导出JSONL文件 -->
      <div v-if="currentStep === 2" class="step-3">
        <p>确认导出设置</p>
        <el-button @click="prevStep">上一步</el-button>
        <el-button @click="exportJsonl" type="success">导出JSONL文件</el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CsvConversionForm',
  data() {
    return {
      currentStep: 0,
      csvUploaded: false,
      uploadedFileName: '',
      csvColumns: [],
      jsonlFields: [
        {
          jsonlField: '',
          mappingType: 'single',
          selectedColumn: '',
          multipleMapping: '',
          customText: '',
          filterType: 'any',
          filterValue: ''
        }
      ]
    }
  },
  methods: {
    nextStep() {
      if (this.currentStep < 2) {
        this.currentStep++
      }
    },
    prevStep() {
      if (this.currentStep > 0) {
        this.currentStep--
      }
    },
    handleCsvUploadSuccess(response) {
      this.csvUploaded = true
      this.uploadedFileName = response.filename
      this.csvColumns = response.columns || []
      this.$message.success('CSV文件上传成功')
    },
    handleCsvUploadError() {
      this.$message.error('CSV文件上传失败')
    },
    handleMappingTypeChange(field) {
        // 重置字段值
        field.selectedColumn = ''
        field.multipleMapping = ''
        field.customText = ''
        field.filterType = 'any'
        field.filterValue = ''
      },
      handleFilterTypeChange(field) {
        // 重置筛选值
        if (!['equals', 'greater_than', 'less_than', 'greater_or_equal', 'less_or_equal'].includes(field.filterType)) {
          field.filterValue = ''
        }
      },
      parseMultipleMapping(field) {
        // 简单的表达式解析示例
        const expression = field.multipleMapping
        if (!expression) {
          this.$message.warning('请输入表达式')
          return
        }
        
        // 这里可以添加更复杂的表达式解析逻辑
        // 目前只是简单地显示解析结果
        this.$message.info(`表达式已解析: ${expression}`)
      },
    addField() {
      this.jsonlFields.push({
        jsonlField: '',
        mappingType: 'single',
        selectedColumn: '',
        multipleMapping: '',
        customText: '',
        filterType: 'any',
        filterValue: ''
      })
    },
    removeField(index) {
      if (this.jsonlFields.length > 1) {
        this.jsonlFields.splice(index, 1)
      } else {
        this.$message.warning('至少需要保留一个字段')
      }
    },
    exportJsonl() {
      // 准备映射配置数据
      const mappingConfig = {
        csvFileName: this.uploadedFileName,
        fields: this.jsonlFields
      }
      
      // 调用后端API导出JSONL文件
      fetch('/api/export-jsonl', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mappingConfig)
      })
      .then(response => response.json())
      .then(data => {
        this.$message.success(`JSONL文件导出成功: ${data.filename}`)
        this.currentStep = 0
      })
      .catch(error => {
        this.$message.error(`导出失败: ${error.message}`)
      })
    }
  }
}
</script>

<style scoped>
.csv-conversion-form {
  padding: 20px;
}

.step-content {
  margin-top: 30px;
}

.field-mapping {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.step-buttons {
  margin-top: 20px;
}
</style>