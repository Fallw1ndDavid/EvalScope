<template>
  <div class="jsonl-validation">
    <h2>JSONL 格式验证</h2>
    <div class="upload-area">
      <input type="file" @change="handleFileUpload" accept=".jsonl" />
      <button @click="validateFile" :disabled="!selectedFile">验证文件</button>
    </div>
    <div v-if="validationError" class="error-message">
      <p>文件格式错误：</p>
      <p>第 {{ validationError.line }} 行: {{ validationError.message }}</p>
      <pre>{{ validationError.content }}</pre>
    </div>
    <div v-if="validationSuccess" class="success-message">
      <p>文件格式正确，共 {{ lineCount }} 行。</p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'JsonlValidation',
  setup() {
    const selectedFile = ref(null);
    const validationError = ref(null);
    const validationSuccess = ref(false);
    const lineCount = ref(0);

    const handleFileUpload = (event) => {
      selectedFile.value = event.target.files[0];
      validationError.value = null;
      validationSuccess.value = false;
    };

    const validateFile = async () => {
      if (!selectedFile.value) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        const lines = content.split('\n');
        lineCount.value = lines.length;

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (line === '') continue; // Skip empty lines

          try {
            JSON.parse(line);
          } catch (error) {
            validationError.value = {
              line: i + 1,
              message: error.message,
              content: line
            };
            validationSuccess.value = false;
            return;
          }
        }

        validationError.value = null;
        validationSuccess.value = true;
      };

      reader.readAsText(selectedFile.value);
    };

    return {
      selectedFile,
      validationError,
      validationSuccess,
      lineCount,
      handleFileUpload,
      validateFile
    };
  }
};
</script>

<style scoped>
.jsonl-validation {
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
</style>