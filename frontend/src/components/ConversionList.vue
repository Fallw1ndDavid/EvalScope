<template>
  <div class="conversion-list">
    <h2>转换后的列表</h2>
    <el-table :data="conversionRecords" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80"></el-table-column>
      <el-table-column prop="csvFileName" label="CSV文件名" width="180"></el-table-column>
      <el-table-column prop="jsonlFileName" label="JSONL文件名" width="180"></el-table-column>
      <el-table-column prop="conversionTime" label="转换时间" width="180"></el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button size="mini" @click="downloadFile(scope.row.csvFileName)">下载CSV</el-button>
          <el-button size="mini" type="primary" @click="downloadFile(scope.row.jsonlFileName)">下载JSONL</el-button>
          <el-button size="mini" type="warning" @click="openRenameDialog(scope.row)">修改文件名</el-button>
          <el-button size="mini" type="danger" @click="deleteRecord(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>

  <!-- 修改文件名对话框 -->
  <el-dialog title="修改文件名" v-model="renameDialogVisible" width="500px">
    <el-form :model="currentRecord" label-width="100px">
      <el-form-item label="CSV文件名">
        <el-input v-model="currentRecord.csvFileName"></el-input>
      </el-form-item>
      <el-form-item label="JSONL文件名">
        <el-input v-model="currentRecord.jsonlFileName"></el-input>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFileNameChanges">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
export default {
  name: 'ConversionList',
  data() {
    return {
      conversionRecords: [],
      currentRecord: null,
      renameDialogVisible: false
    }
  },
  mounted() {
    this.fetchConversionRecords()
  },
  methods: {
    fetchConversionRecords() {
      fetch('/api/conversion-records')
        .then(response => response.json())
        .then(data => {
          this.conversionRecords = data
        })
        .catch(error => {
          this.$message.error(`获取转换记录失败: ${error.message}`)
        })
    },
    downloadFile(fileName) {
      // 调用后端API下载文件
      fetch(`/api/download/${fileName}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`下载失败: ${response.statusText}`)
          }
          return response.blob()
        })
        .then(blob => {
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = fileName
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
          window.URL.revokeObjectURL(url)
        })
        .catch(error => {
          this.$message.error(`下载文件失败: ${error.message}`)
        })
    },
    openRenameDialog(record) {
      // 深拷贝记录对象，避免直接修改表格数据
      this.currentRecord = {...record};
      this.renameDialogVisible = true;
    },

    saveFileNameChanges() {
      // 调用后端API更新文件名
      fetch(`/api/conversion-records/${this.currentRecord.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          csvFileName: this.currentRecord.csvFileName,
          jsonlFileName: this.currentRecord.jsonlFileName
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`更新失败: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        this.$message.success('文件名更新成功');
        this.renameDialogVisible = false;
        // 重新获取转换记录列表
        this.fetchConversionRecords();
      })
      .catch(error => {
        this.$message.error(`更新文件名失败: ${error.message}`);
      });
    },

    deleteRecord(recordId) {
      this.$confirm('此操作将永久删除该记录及其关联文件, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 调用后端API删除记录
        fetch(`/api/conversion-records/${recordId}`, {
          method: 'DELETE'
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`删除失败: ${response.statusText}`)
          }
          return response.json()
        })
        .then(data => {
          this.$message.success(data.message)
          // 重新获取转换记录列表
          this.fetchConversionRecords()
        })
        .catch(error => {
          this.$message.error(`删除记录失败: ${error.message}`)
        })
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    }
  }
}
</script>

<style scoped>
.conversion-list {
  padding: 20px;
}
</style>