<script setup lang="ts">
import AppLoading from './AppLoading.vue'

defineOptions({ name: 'AppTable' })

interface Column<T> {
  key: string
  header: string
  render?: (row: T) => string
  sortable?: boolean
  class?: string
  headerClass?: string
}

interface Props<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: keyof T | ((row: T) => string)
  striped?: boolean
  hoverable?: boolean
  bordered?: boolean
  compact?: boolean
  emptyMessage?: string
  loading?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

interface Emits<T> {
  sort: [key: string, order: 'asc' | 'desc']
  rowClick: [row: T]
}

const props = withDefaults(defineProps<Props<Record<string, unknown>>>(), {
  striped: true,
  hoverable: true,
  bordered: true,
  compact: false,
  emptyMessage: 'データがありません',
  loading: false,
  sortBy: '',
  sortOrder: 'asc',
})

const emit = defineEmits<Emits<Record<string, unknown>>>()

const getRowKey = (row: Record<string, unknown>): PropertyKey => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row) as PropertyKey
  }
  return row[props.rowKey as string] as PropertyKey
}

const handleSort = (column: Column<Record<string, unknown>>) => {
  if (!column.sortable) return
  const newOrder = props.sortBy === column.key && props.sortOrder === 'asc' ? 'desc' : 'asc'
  emit('sort', column.key, newOrder)
}

const sortIcon = (column: Column<Record<string, unknown>>) => {
  if (!column.sortable || props.sortBy !== column.key) return null
  return props.sortOrder === 'asc' ? '↑' : '↓'
}
</script>

<template>
  <div class="overflow-x-auto" data-testid="table-container">
    <div v-if="loading" class="flex items-center justify-center p-8" data-testid="table-loading">
      <AppLoading :size="'md'" :variant="'spinner'" message="読み込み中..." />
    </div>
    
    <table
      v-else
      class="w-full text-sm"
      :class="[
        'divide-y divide-gray-200',
        { 'divide-y-0': !bordered },
        { 'divide-gray-100': bordered },
      ]"
      data-testid="table"
    >
      <thead class="bg-gray-50">
        <tr data-testid="table-header-row">
          <th
            v-for="column in columns"
            :key="column.key"
            scope="col"
            :class="[
              'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
              column.headerClass,
              { 'cursor-pointer select-none': column.sortable },
            ]"
            :data-testid="`table-header-${column.key}`"
            :aria-sort="column.sortable && sortBy === column.key ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'"
            @click="handleSort(column)"
          >
            <div class="flex items-center gap-1">
              <span>{{ column.header }}</span>
              <span v-if="column.sortable" class="text-gray-400" data-testid="table-sort-icon">{{ sortIcon(column) }}</span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200" :class="{ 'divide-gray-100': bordered }">
        <tr
          v-if="rows.length === 0"
          data-testid="table-empty"
        >
          <td :colspan="columns.length" class="px-4 py-8 text-center text-gray-500">
            {{ emptyMessage }}
          </td>
        </tr>
        <tr
          v-for="(row, index) in rows"
          v-else
          :key="getRowKey(row)"
          :class="[
            { 'bg-gray-50': striped && index % 2 === 1 },
            { 'hover:bg-gray-50': hoverable },
            { 'cursor-pointer': true },
          ]"
          data-testid="table-row"
          :data-test-row-key="getRowKey(row)"
          @click="$emit('rowClick', row)"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-gray-900"
            :class="column.class"
            data-testid="table-cell"
            :data-test-column="column.key"
          >
            <span v-if="column.render">{{ column.render(row) }}</span>
            <span v-else>{{ row[column.key] }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>