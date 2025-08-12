import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'  // 直接使用完整的echarts库

// 配置全局axios实例
// 动态获取当前页面的协议和主机名，避免写死localhost
const baseURL = `${window.location.protocol}//${window.location.hostname}:8001`;
const axiosInstance = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const app = createApp(App)
app.config.globalProperties.$http = axiosInstance
app.use(router)
app.use(ElementPlus)
// 全局注册ECharts组件
app.component('v-chart', VChart)
app.mount('#app')