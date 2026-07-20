/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to check duplicate between two receipts.
 */
export type DuplicateCheckRequest = {
  /**
   * New receipt ID to check
   */
  source_receipt_id: number;
  /**
   * Existing receipt ID to compare against
   */
  target_receipt_id: number;
  /**
   * Whether to save result to database
   */
  save_result?: boolean;
};

