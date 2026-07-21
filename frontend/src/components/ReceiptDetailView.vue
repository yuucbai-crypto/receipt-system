<template>
  <div class="receipt-detail-view" data-testid="receipt-detail-view">
    <!-- レシート情報 -->
    <div class="receipt-info" data-testid="receipt-info">
      <h2>レシート詳細</h2>
      
      <div class="info-grid">
        <div class="info-item">
          <label>日付</label>
          <p>{{ formatDate(receipt.date) }}</p>
        </div>
        <div class="info-item">
          <label>金額</label>
          <p>{{ formatCurrency(receipt.amount) }}</p>
        </div>
        
        <div class="info-item">
          <label>勘定科目</label>
          <p>{{ receipt.category }}</p>
        </div>
        
        <div class="info-item">
          <label>ステータス</label>
          <AppBadge :status="receipt.status" :text="getStatusText(receipt.status)" />
        </div>
      </div>
      
      <div class="tags-section" data-testid="receipt-tags">
        <label>タグ</label>
        <div class="tags">
          <span 
            v-for="tag in receipt.tags" 
            :key="tag"
            class="tag-badge"
            data-testid="receipt-tag"
          >
            {{ tag }}
          </span>
        </div>
      </div>
      
      <div class="description-section" data-testid="receipt-description">
        <label>説明</label>
        <p>{{ receipt.description }}</p>
      </div>
    </div>

    <!-- 画像プレビュー -->
    <div class="image-preview" data-testid="receipt-image-preview">
      <h3>レシート画像</h3>
      <AppImagePreview 
        :src="receipt.image_url" 
        :alt="`レシート画像 - ${receipt.id}`"
        :open="true"
        data-testid="receipt-image"
        @close="$emit('close')"
      />
    </div>

    <!-- OCR結果 -->
    <div class="ocr-section" data-testid="receipt-ocr">
      <h3>OCR結果</h3>
      <div class="ocr-content">
        <pre>{{ receipt.ocr_content }}</pre>
      </div>
    </div>

    <!-- AIコメント -->
    <div class="ai-comment-section" data-testid="receipt-ai-comment">
      <h3>AIコメント</h3>
      <div class="comment-content">
        {{ receipt.ai_comment }}
      </div>
    </div>

    <!-- 操作ボタン -->
    <div class="actions" data-testid="receipt-detail-actions">
      <AppButton 
        v-if="receipt.status === 'pending'" 
        data-testid="approve-receipt-button"
        @click="approveReceiptAction"
      >
        承認
      </AppButton>
      
      <AppButton 
        v-if="receipt.status === 'pending'" 
        data-testid="reject-receipt-button"
        @click="rejectReceiptAction"
      >
        却下
      </AppButton>
      
      <!-- 再解析ボタン (Backend API未提供のため、実装保留) -->
      <!--
      <AppButton 
        @click="reprocessReceiptAction"
        data-testid="reprocess-receipt-button"
      >
        再解析
      </AppButton>
      -->
      
      <AppButton 
        data-testid="close-detail-button"
        @click="$emit('close')"
      >
        閉じる
      </AppButton>
    </div>
  </div>
</template>

<script setup lang="ts">

import { formatDate, formatCurrency } from '@/utils/currency';
import AppBadge from '@/components/ui/AppBadge.vue';
import AppImagePreview from '@/components/ui/AppImagePreview.vue';
import AppButton from '@/components/ui/AppButton.vue';
import { approveReceipt, rejectReceipt } from '@/api/receipts';

// プロパティ
const props = defineProps<{
  receipt: any;
  open?: boolean;
  onClose?: () => void;
}>();

// イベント
const emit = defineEmits(['close']);

// ステータスのテキスト取得
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '承認待ち',
    approved: '承認済み',
    rejected: '却下済み'
  };
  
  return statusMap[status] || status;
};

// 承認
const approveReceiptAction = async () => {
  try {
    await approveReceipt(props.receipt.id);
    // 成功時は親コンポーネントに通知
    emit('close');
  } catch (error) {
    console.error('レシート承認エラー:', error);
    // エラーメッセージの表示などはここで処理
  }
};

// 卻下
const rejectReceiptAction = async () => {
  try {
    // 却下理由を入力するモーダルを表示
    const reason = prompt('却下理由を入力してください');
    if (reason) {
      await rejectReceipt(props.receipt.id, {
        reason_code: 'USER_INPUT',
        reason_text: reason
      });
      // 成功時は親コンポーネントに通知
      emit('close');
    }
  } catch (error) {
    console.error('レシート却下エラー:', error);
    // エラーメッセージの表示などはここで処理
  }
};

// 再解析 (Backend API未提供のため、実装保留)
// const reprocessReceiptAction = async () => {
//   try {
//     await reprocessReceipt(props.receipt.id);
//     // 成功時は親コンポーネントに通知
//     emit('close');
//   } catch (error) {
//     console.error('レシート再解析エラー:', error);
//     // エラーメッセージの表示などはここで処理
//   }
// };
</script>

<style scoped>
.receipt-detail-view {
  padding: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.info-item {
  margin-bottom: 10px;
}

.info-item label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.info-item p {
  margin: 0;
  color: #666;
}

.tags-section {
  margin-bottom: 20px;
}

.tags-section label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag-badge {
  background-color: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
}

.description-section {
  margin-bottom: 20px;
}

.description-section label {
  display: block;
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.image-preview {
  margin-bottom: 20px;
}

.ocr-section, .ai-comment-section {
  margin-bottom: 20px;
}

.ocr-content, .comment-content {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
  flex-wrap: wrap;
}
</style>