import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '@/components/DashboardView.vue';
import ReceiptListView from '@/components/ReceiptListView.vue';
import ReceiptDetailView from '@/components/ReceiptDetailView.vue';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/receipts',
    name: 'ReceiptList',
    component: ReceiptListView
  },
  {
    path: '/receipts/:id',
    name: 'ReceiptDetail',
    component: ReceiptDetailView,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;