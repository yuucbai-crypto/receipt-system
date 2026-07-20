<template>
  <div class="dashboard-view">
    <h1>Dashboard</h1>
    
    <!-- 合計金額表示 -->
    <div class="summary-cards">
      <div class="card" data-testid="total-amount-card">
        <h2>今月の合計金額</h2>
        <p>{{ formatCurrency(currentMonthTotal) }}</p>
      </div>
      <div class="card" data-testid="yearly-amount-card">
        <h2>今年の合計金額</h2>
        <p>{{ formatCurrency(yearlyTotal) }}</p>
      </div>
    </div>

    <!-- 勘定科目別集計 -->
    <div class="category-summary" data-testid="category-summary">
      <h2>勘定科目別集計</h2>
      <div class="category-chart">
        <div 
          v-for="(amount, category) in categoryTotals" 
          :key="category"
          class="category-item"
          :data-testid="`category-${category}-item`"
        >
          <span>{{ category }}</span>
          <span>{{ formatCurrency(amount) }}</span>
        </div>
      </div>
    </div>

    <!-- 月別推移グラフ -->
    <div class="monthly-trend" data-testid="monthly-trend">
      <h2>月別推移</h2>
      <div class="chart-container">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { formatCurrency } from '@/utils/currency';
import { getDashboardData } from '@/api/dashboard';

// ダッシュボードデータ
const currentMonthTotal = ref(0);
const yearlyTotal = ref(0);
const categoryTotals = ref<Record<string, number>>({});
const chartCanvas = ref<HTMLCanvasElement | null>(null);

// チャートインスタンス
let chartInstance: any = null;

// ダッシュボードデータ取得
const fetchDashboardData = async () => {
  try {
    const data = await getDashboardData();
    currentMonthTotal.value = data.current_month_total;
    yearlyTotal.value = data.yearly_total;
    categoryTotals.value = data.category_totals;
    
    // グラフ描画
    drawChart(data.monthly_trend);
  } catch (error) {
    console.error('ダッシュボードデータ取得エラー:', error);
  }
};

// チャート描画
const drawChart = (monthlyData: any[]) => {
  if (!chartCanvas.value || !monthlyData.length) return;
  
  const ctx = chartCanvas.value.getContext('2d');
  if (!ctx) return;
  
  // 前のチャートを破棄
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  // チャートデータ構築
  const labels = monthlyData.map(item => item.month);
  const amounts = monthlyData.map(item => item.total);
  
  // Chart.jsで描画
  chartInstance = new (window as any).Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '金額',
        data: amounts,
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value: any) {
              return formatCurrency(value);
            }
          }
        }
      }
    }
  });
};

// 初期データ取得
onMounted(() => {
  fetchDashboardData();
});

// データが変更されたら再描画
watch(
  () => [currentMonthTotal.value, yearlyTotal.value, categoryTotals.value],
  () => {
    // チャートの再描画はfetchDashboardDataで行う
  }
);
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
}

.summary-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card h2 {
  margin-top: 0;
  font-size: 1.1em;
  color: #333;
}

.card p {
  font-size: 1.5em;
  font-weight: bold;
  color: #4CAF50;
}

.category-summary {
  margin-bottom: 30px;
}

.category-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
}

.monthly-trend {
  margin-bottom: 30px;
}

.chart-container {
  height: 300px;
  position: relative;
}
</style>