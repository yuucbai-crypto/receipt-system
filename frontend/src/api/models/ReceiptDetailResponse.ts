/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Detailed receipt response (extends list response with more details).
 */
export type ReceiptDetailResponse = {
  id: number;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  image_hash: string;
  ocr_text?: (string | null);
  ocr_confidence?: (number | null);
  ocr_language: string;
  receipt_date?: (string | null);
  store_name?: (string | null);
  total_amount?: (number | null);
  tax_amount?: (number | null);
  currency: string;
  category_id?: (number | null);
  category_name?: (string | null);
  category_confidence?: (number | null);
  ai_comment?: (string | null);
  ai_model?: (string | null);
  ai_confidence?: (number | null);
  status: string;
  status_message?: (string | null);
  processing_started_at?: (string | null);
  processing_completed_at?: (string | null);
  retry_count: number;
  tags?: Array<string>;
  created_at: string;
  updated_at: string;
};

