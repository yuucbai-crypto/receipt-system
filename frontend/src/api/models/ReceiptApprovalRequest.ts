/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RejectionReasonCreate } from './RejectionReasonCreate';
/**
 * Request to approve a receipt.
 */
export type ReceiptApprovalRequest = {
  /**
   * Receipt ID to approve/reject
   */
  receipt_id: number;
  /**
   * True to approve, False to reject
   */
  approve: boolean;
  /**
   * Required if approve=False
   */
  rejection_reason?: (RejectionReasonCreate | null);
  /**
   * Optional user note
   */
  user_note?: (string | null);
};

