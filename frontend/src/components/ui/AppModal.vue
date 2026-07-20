<script setup lang="ts">
import { Dialog } from '@headlessui/vue'

defineOptions({ name: 'AppModal' })

interface Props {
  modelValue: boolean
  title?: string
  description?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closeOnOverlayClick?: boolean
  showCloseButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  closeOnOverlayClick: true,
  showCloseButton: true,
  title: '',
  description: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-4xl',
}

const handleClose = () => {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Dialog as="div" class="relative z-50" :open="modelValue" @close="handleClose">
        <Dialog.Overlay
          class="fixed inset-0 bg-black/25 backdrop-blur-sm"
          data-testid="modal-overlay"
          @click.self="props.closeOnOverlayClick && handleClose"
        />
        <div class="fixed inset-0 overflow-y-auto">
          <div class="flex min-h-full items-center justify-center p-4 text-center">
            <Dialog.Panel
              class="w-full transform overflow-hidden rounded-2xl bg-white px-6 pb-4 pt-5 text-left align-middle shadow-xl transition-all"
              :class="sizeClasses[props.size]"
              data-testid="modal-container"
            >
              <div class="flex items-start justify-between" data-testid="modal-header">
                <div>
                  <h3 v-if="title" class="text-lg font-semibold text-gray-900" data-testid="modal-title">
                    {{ title }}
                  </h3>
                  <p v-if="description" class="mt-1 text-sm text-gray-500" data-testid="modal-description">
                    {{ description }}
                  </p>
                </div>
                <button
                  v-if="showCloseButton"
                  type="button"
                  class="text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg p-1"
                  data-testid="modal-close"
                  aria-label="閉じる"
                  @click="handleClose"
                >
                  <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div class="mt-4" data-testid="modal-content">
                <slot />
              </div>
            </Dialog.Panel>
          </div>
        </div>
      </Dialog>
  </Teleport>
</template>
