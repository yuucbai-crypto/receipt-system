<script setup lang="ts">
import AppLoadingContent from './AppLoadingContent.vue'

defineOptions({ name: 'AppLoading' })

interface Props {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'spinner' | 'dots' | 'pulse' | 'bars'
  color?: 'primary' | 'white' | 'gray'
  overlay?: boolean
  message?: string
}

withDefaults(defineProps<Props>(), {
  size: 'md',
  variant: 'spinner',
  color: 'primary',
  overlay: false,
  message: '',
})
</script>

<template>
  <div
    v-if="overlay"
    class="fixed inset-0 z-50 flex items-center justify-center"
    data-testid="loading-overlay"
  >
    <AppLoadingContent :size="size" :variant="variant" :color="color" :message="message" />
  </div>
  <AppLoadingContent
    v-else
    :size="size"
    :variant="variant"
    :color="color"
    :message="message"
    data-testid="loading-inline"
  />
</template>

<style scoped>
/* No additional styles needed - using Tailwind classes */
</style>