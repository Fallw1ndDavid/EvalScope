import { App } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'

// 注册VChart组件
export default function (app) {
  // 手动引入ECharts模块以减小打包体积
  // 引入柱状图
  import('echarts/lib/chart/bar')
  // 引入饼图
  import('echarts/lib/chart/pie')
  // 引入折线图
  import('echarts/lib/chart/line')
  // 引入提示框
  import('echarts/lib/component/tooltip')
  // 引入图例
  import('echarts/lib/component/legend')
  // 引入网格
  import('echarts/lib/component/grid')
  // 引入坐标轴
  import('echarts/lib/component/axis')

  // 全局注册VChart组件
  app.component('v-chart', VChart)
}