<script setup lang="ts" generic>
import { computed } from 'vue'

defineOptions({ name: 'AppLoadingContent' })

interface Props {
  size: 'sm' | 'md' | 'lg'
  variant: 'spinner' | 'dots' | 'pulse' | 'bars'
  color: 'primary' | 'white' | 'gray'
  message?: string
}

const props = defineProps<Props>()

const sizeClasses = {
  sm: { spinner: 'h-4 w-4', dots: 'h-1.5 w-1.5', pulse: 'h-4 w-4', bars: 'h-4 w-1' },
  md: { spinner: 'h-8 w-8', dots: 'h-2.5 w-2.5', pulse: 'h-8 w-8', bars: 'h-8 w-1.5' },
  lg: { spinner: 'h-12 w-12', dots: 'h-3 w-3', pulse: 'h-12 w-12', bars: 'h-12 w-2' },
}

const colorClasses = {
  primary: 'text-blue-600',
  white: 'text-white',
  gray: 'text-gray-400',
}

const sizeClass = computed(() => sizeClasses[props.size][props.variant])
const colorClass = computed(() => colorClasses[props.color])
</script>

<template>
  <div class="flex flex-col items-center gap-2" :class="colorClass" data-testid="loading-content">
    <!-- Spinner variant -->
    <div v-if="variant === 'spinner'" class="relative" :class="sizeClass" data-testid="loading-spinner">
      <svg class="absolute top-0 left-0 animate-spin" :class="sizeClass" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    </div>

    <!-- Dots variant -->
    <div v-else-if="variant === 'dots'" class="flex gap-1" :class="sizeClass" data-testid="loading-dots">
      <div class="bg-current rounded-full animate-bounce" style="animation-delay: 0ms" />
      <div class="bg-current rounded-full animate-bounce" style="animation-delay: 150ms" />
      <div class="bg-current rounded-full animate-bounce" style="animation-delay: 300ms" />
    </div>

    <!-- Pulse variant -->
    <div v-else-if="variant === 'pulse'" class="relative" :class="sizeClass" data-testid="loading-pulse">
      <div class="absolute inset-0 bg-current rounded-full animate-ping opacity-75" />
      <div class="relative bg-current rounded-full" />
    </div>

    <!-- Bars variant -->
    <div v-else-if="variant === 'bars'" class="flex items-end gap-1" :class="sizeClass" data-testid="loading-bars">
      <div class="bg-current rounded animate-pulse" style="animation-delay: 0ms" />
      <div class="bg-current rounded animate-pulse" style="animation-delay: 100ms; height: 60%" />
      <div class="bg-current rounded animate-pulse" style="animation-delay: 200ms; height: 80%" />
      <div class="bg-current rounded animate-pulse" style="animation-delay: 300ms" />
    </div>

    <p v-if="message" class="text-sm font-medium" data-testid="loading-message">{{ message }}</p>
  </div>
</template>

<style scoped>
/* No additional styles needed - using Tailwind classes */
</style>