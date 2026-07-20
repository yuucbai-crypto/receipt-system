/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to create a rejection reason.
 */
export type RejectionReasonCreate = {
  /**
   * Reason code (e.g., 'DUPLICATE', 'INVALID_AMOUNT')
   */
  reason_code: string;
  /**
   * Reason category (e.g., 'DUPLICATE', 'DATA_QUALITY', 'NOT_BUSINESS')
   */
  reason_category: string;
  /**
   * Detailed reason text
   */
  reason_text: string;
  /**
   * Optional user note
   */
  user_note?: (string | null);
  /**
   * Whether this can be used for AI training
   */
  is_for_ai_training?: boolean;
};

