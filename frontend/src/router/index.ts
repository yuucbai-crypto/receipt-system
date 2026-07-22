import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '@/components/DashboardView.vue';
import ReceiptListView from '@/components/ReceiptListView.vue';
import ReceiptDetailView from '@/components/ReceiptDetailView.vue';
import DuplicateApprovalView from '@/components/DuplicateApprovalView.vue';
import FinalApprovalView from '@/components/FinalApprovalView.vue';

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
  },
  {
    path: '/duplicate-approval/:id',
    name: 'DuplicateApproval',
    component: DuplicateApprovalView,
    props: true
  },
  {
    path: '/final-approval/:receiptId/duplicate/:duplicateDecision',
    name: 'FinalApproval',
    component: FinalApprovalView,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;