<script setup lang="ts">
import { h } from 'vue'

defineOptions({ name: 'AppToast' })

interface ToastItem {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

interface Props {
  toasts: ToastItem[]
}

defineProps<Props>()

const emit = defineEmits<{
  remove: [id: string]
}>()

const typeClasses = {
  success: 'bg-green-50 text-green-800 border-green-200',
  error: 'bg-red-50 text-red-800 border-red-200',
  warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  info: 'bg-blue-50 text-blue-800 border-blue-200',
}

const typeIcons = {
  success: () => h('svg', { class: 'h-5 w-5', fill: 'currentColor', viewBox: '0 0 20 20' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z', 'clip-rule': 'evenodd' })
  ]),
  error: () => h('svg', { class: 'h-5 w-5', fill: 'currentColor', viewBox: '0 0 20 20' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z', 'clip-rule': 'evenodd' })
  ]),
  warning: () => h('svg', { class: 'h-5 w-5', fill: 'currentColor', viewBox: '0 0 20 20' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z', 'clip-rule': 'evenodd' })
  ]),
  info: () => h('svg', { class: 'h-5 w-5', fill: 'currentColor', viewBox: '0 0 20 20' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-5a1 1 0 011 1v3a1 1 0 11-2 0v-3a1 1 0 011-1zm0 10a1 1 0 100-2 1 1 0 000 2z', 'clip-rule': 'evenodd' })
  ]),
}

const removeToast = (id: string) => {
  emit('remove', id)
}
</script>

<template>
  <TransitionGroup
    as="div"
    class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
    enter="transition ease-out duration-300"
    enter-from="opacity-0 translate-x-full"
    leave="transition ease-in duration-200"
    leave-to="opacity-0 translate-x-full"
    data-testid="toast-container"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['flex items-start gap-3 p-4 rounded-lg border shadow-lg min-w-[300px] max-w-md pointer-events-auto', typeClasses[toast.type]]"
      data-testid="toast-item"
      :data-test-type="toast.type"
    >
      <div class="flex-shrink-0" data-testid="toast-icon">
        <component :is="typeIcons[toast.type]" />
      </div>
      <div class="flex-1 min-w-0" data-testid="toast-message">
        <p class="text-sm font-medium">{{ toast.message }}</p>
      </div>
      <button
        type="button"
        class="flex-shrink-0 text-current opacity-50 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current"
        data-testid="toast-close"
        aria-label="閉じる"
        @click="removeToast(toast.id)"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </TransitionGroup>
</template>
