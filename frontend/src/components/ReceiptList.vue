<template>
  <div class="receipt-list">
    <h2>Receipt List</h2>
    <div v-for="receipt in receipts" :key="receipt.id" class="receipt-item">
      <h3>{{ receipt.title }}</h3>
      <p>{{ receipt.description }}</p>
      <p>Amount: ${{ receipt.amount }}</p>
      <p>Date: {{ receipt.date }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const receipts = ref([]);

onMounted(() => {
  // Mock data for demonstration
  receipts.value = [
    { id: 1, title: 'Grocery Shopping', description: 'Weekly groceries', amount: 85.30, date: '2023-04-01' },
    { id: 2, title: 'Gas Station', description: 'Fuel for car', amount: 45.00, date: '2023-04-05' },
    { id: 3, title: 'Restaurant', description: 'Dinner with friends', amount: 120.00, date: '2023-04-10' }
  ];
});
</script>

<style scoped>
.receipt-list {
  padding: 20px;
}

.receipt-item {
  border: 1px solid #ccc;
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 5px;
}
</style>