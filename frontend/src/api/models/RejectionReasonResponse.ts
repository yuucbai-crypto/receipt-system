/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response for rejection reason.
 */
export type RejectionReasonResponse = {
  id: number;
  receipt_id: number;
  reason_code: string;
  reason_category: string;
  reason_text: string;
  user_note: (string | null);
  ai_feedback: (string | null);
  is_for_ai_training: boolean;
  created_at: string;
  updated_at: string;
};

