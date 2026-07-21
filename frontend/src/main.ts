import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import './style.css'

// Import UI components
import AppButton from './components/ui/AppButton.vue'
import AppInput from './components/ui/AppInput.vue'
import AppModal from './components/ui/AppModal.vue'
import AppToast from './components/ui/AppToast.vue'
import AppLoading from './components/ui/AppLoading.vue'
import AppTable from './components/ui/AppTable.vue'
import AppImagePreview from './components/ui/AppImagePreview.vue'
import AppBadge from './components/ui/AppBadge.vue'
import AppTabs from './components/ui/AppTabs.vue'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// Register global components
app.component('AppButton', AppButton)
app.component('AppInput', AppInput)
app.component('AppModal', AppModal)
app.component('AppToast', AppToast)
app.component('AppLoading', AppLoading)
app.component('AppTable', AppTable)
app.component('AppImagePreview', AppImagePreview)
app.component('AppBadge', AppBadge)
app.component('AppTabs', AppTabs)

app.mount('#app')