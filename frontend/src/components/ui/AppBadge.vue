<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ name: 'AppBadge' })

interface Props {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  removable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
  dot: false,
  removable: false,
})

const emit = defineEmits<{
  remove: []
}>()

const baseClasses = 'inline-flex items-center font-medium rounded-full'

const variantClasses = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
  outline: 'bg-transparent border border-gray-300 text-gray-700',
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs gap-1',
  md: 'px-2.5 py-0.5 text-sm gap-1.5',
  lg: 'px-3 py-1 text-base gap-2',
}

const dotColors = {
  default: 'bg-gray-500',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  danger: 'bg-red-500',
  info: 'bg-blue-500',
  outline: 'bg-gray-500',
}

const classNames = computed(() => [
  baseClasses,
  variantClasses[props.variant],
  sizeClasses[props.size],
].join(' '))

const handleRemove = (event: MouseEvent) => {
  event.stopPropagation()
  emit('remove')
}
</script>

<template>
  <span :class="classNames" data-testid="badge">
    <span v-if="dot" :class="['w-1.5 h-1.5 rounded-full', dotColors[variant]]" data-testid="badge-dot" />
    <slot />
    <button
      v-if="removable"
      type="button"
      class="ml-1 p-0.5 rounded-full hover:bg-black/10 focus:outline-none focus:ring-2 focus:ring-current"
      aria-label="削除"
      data-testid="badge-remove"
      @click="handleRemove"
    >
      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
</template>
