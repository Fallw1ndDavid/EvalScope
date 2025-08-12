<template>
  <div class="prompt-list">
    <h2>提示词列表</h2>
    <el-table :data="prompts" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="title" label="标题" width="200"></el-table-column>
      <el-table-column prop="content" label="内容">
        <template #default="scope">
          <div class="prompt-content">{{ scope.row.content }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180"></el-table-column>
      <el-table-column prop="remark" label="备注" width="200"></el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="mini" @click="editPrompt(scope.row)">编辑</el-button>
          <el-button size="mini" type="danger" @click="deletePrompt(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog title="编辑提示词" v-model="dialogVisible" width="50%">
      <el-form :model="editingPrompt" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="editingPrompt.title"></el-input>
        </el-form-item>
        <el-form-item label="内容">
          <el-input type="textarea" v-model="editingPrompt.content" :rows="6"></el-input>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" v-model="editingPrompt.remark" :rows="3"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="updatePrompt">确 定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'PromptList',
  data() {
    return {
      prompts: [],
      dialogVisible: false,
      editingPrompt: {
        id: 0,
        title: '',
        content: '',
        remark: ''
      }
    }
  },
  mounted() {
    this.fetchPrompts()
  },
  methods: {
    fetchPrompts() {
      fetch('/api/prompts')
        .then(response => response.json())
        .then(data => {
          this.prompts = data
        })
        .catch(error => {
          this.$message.error(`获取提示词失败: ${error.message}`)
        })
    },
    editPrompt(prompt) {
      this.editingPrompt = { ...prompt }
      this.dialogVisible = true
    },
    updatePrompt() {
      // 调用后端API更新提示词
      fetch(`/api/prompts/${this.editingPrompt.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.editingPrompt)
      })
      .then(response => {
        if (response.ok) {
          this.$message.success('提示词更新成功')
          this.dialogVisible = false
          
          // 更新本地数据
          const index = this.prompts.findIndex(p => p.id === this.editingPrompt.id)
          if (index !== -1) {
            this.prompts.splice(index, 1, { ...this.editingPrompt })
          }
        } else {
          throw new Error('更新失败')
        }
      })
      .catch(error => {
        this.$message.error(`更新失败: ${error.message}`)
      })
    },
    deletePrompt(id) {
      this.$confirm('确定要删除这个提示词吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 调用后端API删除提示词
        fetch(`/api/prompts/${id}`, {
          method: 'DELETE'
        })
        .then(response => {
          if (response.ok) {
            this.prompts = this.prompts.filter(p => p.id !== id)
            this.$message.success('提示词删除成功')
          } else {
            throw new Error('删除失败')
          }
        })
        .catch(error => {
          this.$message.error(`删除失败: ${error.message}`)
        })
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    }
  }
}
</script>

<style scoped>
.prompt-list {
  padding: 20px;
}

.prompt-content {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.dialog-footer {
  text-align: right;
}
</style>