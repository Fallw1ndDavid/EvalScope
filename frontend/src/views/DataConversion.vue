<template>
  <div class="data-conversion">
    <h1>格式转换</h1>
    <div class="menu-container">
      <div class="left-menu">
        <el-menu :default-active="activeMenu" @select="handleMenuSelect">
          <el-menu-item index="1">csv转换jsonl</el-menu-item>
          <el-menu-item index="2">转换后的列表</el-menu-item>
          <el-divider />
          <el-menu-item index="3">提示词管理</el-menu-item>
          <el-divider />
          <el-menu-item index="4">模型管理</el-menu-item>
          <el-divider />
          <el-menu-item index="5">任务跑批</el-menu-item>
          <el-menu-item index="6">跑批结果</el-menu-item>
          <el-menu-item index="7">JSONL验证</el-menu-item>
          <el-menu-item index="8">JSONL转CSV</el-menu-item>
          <el-menu-item index="9">NGINX日志解析</el-menu-item>
          <el-menu-item index="10">模型性能评估</el-menu-item>
        </el-menu>
      </div>
      <div class="right-content">
        <CsvConversionForm v-if="activeMenu === '1'" />
        <ConversionList v-if="activeMenu === '2'" />
        <PromptManagement v-if="activeMenu === '3'" />
        <ModelManagement v-if="activeMenu === '4'" />
        <BatchTask v-if="activeMenu === '5'" />
        <BatchResults v-if="activeMenu === '6'" />
        <JsonlValidation v-if="activeMenu === '7'" />
        <JsonlToCsv v-if="activeMenu === '8'" />
        <NginxLogParser v-if="activeMenu === '9'" />
        <EvalScope v-if="activeMenu === '10'" />
      </div>
    </div>
  </div>
</template>

<script>
import CsvConversionForm from '../components/CsvConversionForm.vue'
import ConversionList from '../components/ConversionList.vue'
import PromptManagement from '../views/PromptManagement.vue'
import ModelManagement from '../views/ModelManagement.vue'
import BatchTask from '../views/BatchTask.vue'
import BatchResults from '../views/BatchResults.vue'
import JsonlValidation from '../views/JsonlValidation.vue'
import JsonlToCsv from '../views/JsonlToCsv.vue'
import NginxLogParser from '../views/NginxLogParser.vue'
import EvalScope from '../views/EvalScope.vue'

export default {
  name: 'DataConversion',
  components: {
    CsvConversionForm,
    ConversionList,
    PromptManagement,
    ModelManagement,
    BatchTask,
    BatchResults,
    JsonlValidation,
    JsonlToCsv,
    NginxLogParser,
    EvalScope
  },
  data() {
    return {
      activeMenu: '1'
    }
  },
  methods: {
    handleMenuSelect(index) {
      this.activeMenu = index
    }
  }
}
</script>

<style scoped>
.menu-container {
  display: flex;
}

.left-menu {
  width: 200px;
  margin-right: 20px;
}

.right-content {
  flex: 1;
}
</style>