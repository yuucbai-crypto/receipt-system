<script setup lang="ts">
import { ref, computed } from 'vue'
import AppLoading from '@/components/ui/AppLoading.vue'

defineOptions({ name: 'AppImagePreview' })

interface Props {
  src: string
  alt?: string
  open: boolean
  title?: string
  onClose: () => void
}

const props = defineProps<Props>()

const isLoaded = ref(false)
const hasError = ref(false)
const zoom = ref(1)
const position = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

const handleLoad = () => {
  isLoaded.value = true
}

const handleError = () => {
  hasError.value = true
  isLoaded.value = true
}

const zoomIn = () => {
  zoom.value = Math.min(zoom.value * 1.2, 5)
}

const zoomOut = () => {
  zoom.value = Math.max(zoom.value / 1.2, 0.2)
}

const resetZoom = () => {
  zoom.value = 1
  position.value = { x: 0, y: 0 }
}

const handleWheel = (event: WheelEvent) => {
  event.preventDefault()
  if (event.ctrlKey || event.metaKey) {
    const factor = event.deltaY > 0 ? 0.9 : 1.1
    zoom.value = Math.min(Math.max(zoom.value * factor, 0.2), 5)
  }
}

const handleMouseDown = (event: MouseEvent) => {
  if (zoom.value <= 1) return
  isDragging.value = true
  dragStart.value = {
    x: event.clientX - position.value.x,
    y: event.clientY - position.value.y,
  }
  event.preventDefault()
}

const handleMouseMove = (event: MouseEvent) => {
  if (!isDragging.value) return
  position.value = {
    x: event.clientX - dragStart.value.x,
    y: event.clientY - dragStart.value.y,
  }
}

const handleMouseUp = () => {
  isDragging.value = false
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    props.onClose()
  }
}

const imageStyle = computed(() => ({
  transform: `translate(${position.value.x}px, ${position.value.y}px) scale(${zoom.value})`,
  transformOrigin: 'center center',
  cursor: zoom.value > 1 ? 'grab' : 'default',
  userSelect: 'none' as const,
  maxWidth: 'none',
  maxHeight: 'none',
}))
</script>

<template>
  <Transition appear @after-leave="props.onClose">
    <div v-if="props.open" class="relative z-50" @keydown="handleKeyDown">
      <Transition
        enter-active-class="transition-opacity duration-300"
        enter-from-class="opacity-0"
        leave-active-class="transition-opacity duration-300"
        leave-to-class="opacity-0"
      >
        <div v-if="props.open" class="fixed inset-0 bg-black/90 backdrop-blur-sm" data-testid="image-preview-backdrop" />
      </Transition>     
      <div class="fixed inset-0 flex items-center justify-center p-4" data-testid="image-preview-container">
        <Transition
          enter-active-class="transition ease-out duration-300"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-200"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div v-if="props.open" class="relative max-w-full max-h-full" data-testid="image-preview-dialog">
            <div
              v-if="!isLoaded && !hasError"
              class="flex items-center justify-center bg-gray-900 min-w-[300px] min-h-[200px]"
              data-testid="image-preview-loading"
            >
              <AppLoading :size="'lg'" :variant="'spinner'" color="white" message="画像を読み込み中..." />
            </div>

            <div v-else-if="hasError" class="flex items-center justify-center bg-gray-900 min-w-[300px] min-h-[200px] text-red-400" data-testid="image-preview-error">
              <div class="text-center p-4">
                <svg class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p class="mt-2">画像の読み込みに失敗しました</p>
              </div>
            </div>

            <div v-else class="relative bg-gray-900" data-testid="image-preview-image-wrapper" @wheel.passive="handleWheel">
              <img
                :src="props.src"
                :alt="props.alt || props.title || 'プレビュー'"
                :style="imageStyle"
                data-testid="image-preview-image"
                @load="handleLoad"
                @error="handleError"
                @mousedown="handleMouseDown"
                @mousemove="handleMouseMove"
                @mouseup="handleMouseUp"
                @mouseleave="handleMouseUp"
                @dblclick="resetZoom"
              />
            </div>

            <!-- Zoom controls -->
            <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/50 rounded-lg p-2" data-testid="image-preview-controls">
              <button
                type="button"
                class="p-2 text-white hover:bg-white/20 rounded transition-colors"
                :disabled="zoom <= 0.2"
                aria-label="縮小"
                data-testid="image-preview-zoom-out"
                @click="zoomOut"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
                </svg>
              </button>
              <span class="px-3 text-white text-sm font-mono" data-testid="image-preview-zoom-level">{{ Math.round(zoom * 100) }}%</span>
              <button
                type="button"
                class="p-2 text-white hover:bg-white/20 rounded transition-colors"
                :disabled="zoom >= 5"
                aria-label="拡大"
                data-testid="image-preview-zoom-in"
                @click="zoomIn"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
              </button>
              <button
                type="button"
                class="p-2 text-white hover:bg-white/20 rounded transition-colors"
                :disabled="zoom === 1"
                aria-label="リセット"
                data-testid="image-preview-zoom-reset"
                @click="resetZoom"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>

            <!-- Close button -->
            <button
              type="button"
              class="absolute top-4 right-4 p-2 text-white hover:bg-white/20 rounded-full transition-colors"
              aria-label="閉じる"
              data-testid="image-preview-close"
              @click="props.onClose"
            >
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <!-- Title -->
            <div v-if="props.title" class="absolute bottom-4 left-1/2 -translate-x-1/2 text-white text-sm text-center px-3 py-1 bg-black/50 rounded" data-testid="image-preview-title">
              {{ props.title }}
            </div>          </Transition>
        </div>
      </div>
    </Transition>
</template>