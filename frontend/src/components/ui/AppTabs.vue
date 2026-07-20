<script setup lang="ts">
import { computed, type Component } from 'vue'

defineOptions({ name: 'AppTabs' })

interface Tab {
  key: string
  label: string
  icon?: Component
  disabled?: boolean
  badge?: string | number
}

interface Props {
  modelValue: string
  tabs: Tab[]
  variant?: 'line' | 'enclosed' | 'soft'
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'line',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const variantClasses = {
  line: {
    container: 'border-b border-gray-200',
    tab: 'border-b-2 -mb-px',
    active: 'border-blue-600 text-blue-600',
    inactive: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
  },
  enclosed: {
    container: '',
    tab: 'rounded-t-lg',
    active: 'bg-white text-blue-600 shadow-sm',
    inactive: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
  },
  soft: {
    container: '',
    tab: 'rounded-lg',
    active: 'bg-blue-100 text-blue-700',
    inactive: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100',
  },
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

const selectedTab = computed(() => props.tabs.find(t => t.key === props.modelValue))

const handleTabClick = (tab: Tab) => {
  if (!tab.disabled) {
    emit('update:modelValue', tab.key)
  }
}
</script>

<template>
  <div class="tabs" data-testid="tabs">
    <nav
      v-if="variant === 'line'"
      :class="variantClasses[variant].container"
      aria-label="タブ"
      data-testid="tabs-nav"
    >
      <ul class="flex gap-1" role="tablist" data-testid="tabs-list">
        <li
          v-for="tab in tabs"
          :id="`tab-${tab.key}`"
          :key="tab.key"
          role="tab"
          :aria-selected="modelValue === tab.key"
          :aria-disabled="tab.disabled"
          data-testid="tab-item"
          :data-test-key="tab.key"
        >
          <button
            type="button"
            :class="[
              'flex items-center gap-1.5 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
              variantClasses[variant].tab,
              modelValue === tab.key ? variantClasses[variant].active : variantClasses[variant].inactive,
              sizeClasses[size],
              { 'opacity-50 cursor-not-allowed': tab.disabled },
            ]"
            :disabled="tab.disabled"
            data-testid="tab-button"
            :data-test-key="tab.key"
            @click="handleTabClick(tab)"
          >
            <component :is="tab.icon" v-if="tab.icon" class="h-4 w-4" aria-hidden="true" />
            <span>{{ tab.label }}</span>
            <span v-if="tab.badge !== undefined" class="ml-1 px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full" data-testid="tab-badge">
              {{ tab.badge }}
            </span>
          </button>
        </li>
      </ul>
    </nav>

    <nav
      v-else
      class="flex gap-1"
      :class="{ 'bg-gray-100 p-1 rounded-lg': variant === 'enclosed', 'bg-transparent': variant === 'soft' }"
      aria-label="タブ"
      data-testid="tabs-nav"
    >
      <button
        v-for="tab in tabs"
        :id="`tab-${tab.key}`"
        :key="tab.key"
        type="button"
        role="tab"
        :aria-selected="modelValue === tab.key"
        :aria-disabled="tab.disabled"
        :class="[
          'flex items-center gap-1.5 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          variantClasses[variant].tab,
          modelValue === tab.key ? variantClasses[variant].active : variantClasses[variant].inactive,
          sizeClasses[size],
          { 'opacity-50 cursor-not-allowed': tab.disabled },
        ]"
        :disabled="tab.disabled"
        data-testid="tab-button"
        :data-test-key="tab.key"
        @click="handleTabClick(tab)"
      >
        <component :is="tab.icon" v-if="tab.icon" class="h-4 w-4" aria-hidden="true" />
        <span>{{ tab.label }}</span>
        <span v-if="tab.badge !== undefined" class="ml-1 px-1.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full" data-testid="tab-badge">
          {{ tab.badge }}
        </span>
      </button>
    </nav>

    <div class="mt-4" data-testid="tabs-panel">
      <slot :active-tab="selectedTab" />
    </div>
  </div>
</template>
