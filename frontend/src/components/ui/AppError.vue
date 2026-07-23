<script setup lang="ts">
defineProps<{
  error?: string
  retry?: () => void
}>()
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white rounded-xl border border-gray-200 p-8 text-center shadow-lg" data-testid="error-container">
      <div class="flex justify-center mb-4">
        <div class="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
      </div>
      
      <h2 class="text-xl font-bold text-gray-900 mb-2" data-testid="error-title">エラーが発生しました</h2>
      
      <p v-if="error" class="text-gray-600 mb-6" data-testid="error-message">
        {{ error }}
      </p>
      
      <p class="text-gray-500 text-sm mb-6" data-testid="error-description">
        しばらくしてからもう一度お試しください。
      </p>
      
      <AppButton 
        v-if="retry" 
        variant="primary" 
        @click="retry"
        data-testid="error-retry-btn"
      >
        もう一度試す
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles for error component */
</style>