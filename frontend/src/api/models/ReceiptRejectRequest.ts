/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to reject a receipt with reason.
 */
export type ReceiptRejectRequest = {
  /**
   * レシートID
   */
  receipt_id: number;
  /**
   * 却下理由コード
   */
  reason_code: string;
  /**
   * 却下理由テキスト
   */
  reason_text: string;
  /**
   * ユーザーメモ
   */
  user_note?: (string | null);
  /**
   * AI学習用データとして使用
   */
  is_for_ai_training?: boolean;
};

