<template>
  <div class="prompt-form">
    <h2>添加/编辑提示词</h2>
    <el-form :model="promptForm" :rules="rules" ref="promptForm" label-width="100px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="promptForm.title" placeholder="请输入提示词标题（约10个字）"></el-input>
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <el-input
          type="textarea"
          v-model="promptForm.content"
          placeholder="请输入提示词内容（约500个字）"
          :rows="6">
        </el-input>
      </el-form-item>
      <el-form-item label="备注" prop="remark">
        <el-input
          type="textarea"
          v-model="promptForm.remark"
          placeholder="请输入备注（选填）"
          :rows="3">
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submitForm">保存</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  name: 'PromptForm',
  data() {
    return {
      promptForm: {
        title: '',
        content: ''
      },
      rules: {
        title: [
          { required: true, message: '请输入标题', trigger: 'blur' },
          { min: 1, max: 20, message: '长度在 1 到 20 个字符', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入内容', trigger: 'blur' }
        ]
      }
    }
  },
  methods: {
    submitForm() {
      this.$refs.promptForm.validate((valid) => {
        if (valid) {
          // 准备提示词数据
          const promptData = {
            id: Date.now(), // 简单生成唯一ID
            title: this.promptForm.title,
            content: this.promptForm.content,
            remark: this.promptForm.remark,
            createTime: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
          }
          
          // 调用后端API保存提示词
          fetch('/api/prompts', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(promptData)
          })
          .then(response => {
            if (response.ok) {
              this.$message.success('提示词保存成功')
              this.resetForm()
              // 触发父组件刷新列表
              this.$emit('prompt-added')
            } else {
              throw new Error('保存失败')
            }
          })
          .catch(error => {
            this.$message.error(`保存失败: ${error.message}`)
          })
        } else {
          console.log('表单验证失败')
          this.$message.error('请检查表单填写是否正确')
          return false
        }
      })
    },
    resetForm() {
      this.$refs.promptForm.resetFields()
    }
  }
}
</script>

<style scoped>
.prompt-form {
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 20px;
}
</style>