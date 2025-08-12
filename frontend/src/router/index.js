import { createRouter, createWebHistory } from 'vue-router'
import DataConversion from '../views/DataConversion.vue'
import PromptManagement from '../views/PromptManagement.vue'
import ModelManagement from '../views/ModelManagement.vue'
import BatchTask from '../views/BatchTask.vue'
import BatchResults from '../views/BatchResults.vue'
import JsonlValidation from '../views/JsonlValidation.vue'
import JsonlToCsv from '../views/JsonlToCsv.vue'
import NginxLogParser from '../views/NginxLogParser.vue'
import EvalScope from '../views/EvalScope.vue'

const routes = [
  {
    path: '/',
    redirect: '/conversion'
  },
  {
    path: '/conversion',
    name: 'DataConversion',
    component: DataConversion
  },
  {
    path: '/prompts',
    name: 'PromptManagement',
    component: PromptManagement
  },
  {
    path: '/models',
    name: 'ModelManagement',
    component: ModelManagement
  },
  {
    path: '/batch-task',
    name: 'BatchTask',
    component: BatchTask
  },
  {
    path: '/batch-results',
    name: 'BatchResults',
    component: BatchResults
  },
  {
    path: '/batch-results/:id',
    name: 'BatchResultDetail',
    component: () => import('../views/BatchResultDetail.vue'),
    props: true
  },
  {
    path: '/jsonl-validation',
    name: 'JsonlValidation',
    component: JsonlValidation
  },
  {
    path: '/eval-scope',
    name: 'EvalScope',
    component: EvalScope
  },
  {
    path: '/jsonl-to-csv',
    name: 'JsonlToCsv',
    component: JsonlToCsv
  },
  {
    path: '/nginx-log-parser',
    name: 'NginxLogParser',
    component: NginxLogParser
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router