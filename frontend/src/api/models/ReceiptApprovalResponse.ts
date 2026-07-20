/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response for receipt approval/rejection.
 */
export type ReceiptApprovalResponse = {
  receipt_id: number;
  status: string;
  status_message: (string | null);
  rejection_reason_id?: (number | null);
  updated_at: string;
};

