<template>
  <div class="app-select">
    <label v-if="label" :for="id" class="app-select__label">{{ label }}</label>
    <select
      :id="id"
      v-model="selectedValue"
      :data-testid="dataTestid"
      class="app-select__input"
      :disabled="disabled"
    >
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useId } from '@/composables/useId'

const props = defineProps<{
  modelValue: string | number
  label?: string
  options: Array<{ value: string | number; label: string }>
  dataTestid?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
}>()

const id = useId('app-select')

const selectedValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newValue) => {
    selectedValue.value = newValue
  }
)

watch(selectedValue, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>

<style scoped>
.app-select {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.app-select__label {
  font-weight: bold;
  color: #333;
}

.app-select__input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  background-color: #fff;
  color: #333;
}

.app-select__input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}
</style>