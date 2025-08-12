<template>
  <div class="jsonl-to-csv">
    <h2>JSONL 转 CSV</h2>
    <div class="upload-area">
      <input type="file" @change="handleFileUpload" accept=".jsonl" />
      <button @click="convertFile" :disabled="!selectedFile">转换文件</button>
    </div>
    <div v-if="conversionError" class="error-message">
      <p>转换过程中出现错误：</p>
      <p>{{ conversionError }}</p>
    </div>
    <div v-if="conversionSuccess" class="success-message">
      <p>文件转换成功！</p>
      <a :href="downloadUrl" download="converted.csv">点击下载 CSV 文件</a>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'JsonlToCsv',
  setup() {
    const selectedFile = ref(null);
    const conversionError = ref(null);
    const conversionSuccess = ref(false);
    const downloadUrl = ref('');

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0];
      conversionError.value = null;
      conversionSuccess.value = false;
    };

    const convertFile = async () => {
      if (!selectedFile.value) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target.result;
          const lines = content.split('\n');
          
          // 解析JSONL并转换为CSV
          const csvData = [];
          let headers = new Set();
          
          // 收集所有可能的字段名
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line === '') continue;
            
            try {
              const jsonObj = JSON.parse(line);
              Object.keys(jsonObj).forEach(key => headers.add(key));
            } catch (error) {
              conversionError.value = `第 ${i + 1} 行 JSON 格式错误: ${error.message}`;
              conversionSuccess.value = false;
              return;
            }
          }
          
          // 转换为数组以便处理
          headers = Array.from(headers);
          csvData.push(headers);
          
          // 填充数据行
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line === '') continue;
            
            const jsonObj = JSON.parse(line);
            const row = headers.map(header => {
              const value = jsonObj[header];
              // 处理特殊值
              if (value === null || value === undefined) {
                return '';
              } else if (typeof value === 'object') {
                return JSON.stringify(value);
              } else {
                return String(value);
              }
            });
            csvData.push(row);
          }
          
          // 生成CSV内容
          const csvContent = csvData.map(row => 
            row.map(field => {
              // 转义CSV特殊字符
              if (typeof field === 'string' && (field.includes(',') || field.includes('"') || field.includes('\n'))) {
                return `"${field.replace(/"/g, '""')}"`;
              }
              return field;
            }).join(',')
          ).join('\n');
          
          // 创建下载链接
          const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
          downloadUrl.value = URL.createObjectURL(blob);
          conversionSuccess.value = true;
          conversionError.value = null;
        } catch (error) {
          conversionError.value = error.message;
          conversionSuccess.value = false;
        }
      };

      reader.readAsText(selectedFile.value);
    };

    return {
      selectedFile,
      conversionError,
      conversionSuccess,
      downloadUrl,
      handleFileUpload,
      convertFile
    };
  }
};
</script>

<style scoped>
.jsonl-to-csv {
  padding: 20px;
}

.upload-area {
  margin-bottom: 20px;
}

.error-message {
  color: red;
  white-space: pre-wrap;
}

.success-message {
  color: green;
}

.success-message a {
  display: inline-block;
  margin-top: 10px;
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 4px;
}
</style>