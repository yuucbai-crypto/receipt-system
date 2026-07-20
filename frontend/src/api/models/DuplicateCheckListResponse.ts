/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response for listing duplicate check records.
 */
export type DuplicateCheckListResponse = {
  id: number;
  source_receipt_id: number;
  target_receipt_id: number;
  composite_score: (number | null);
  duplicate_threshold: number;
  is_duplicate: (boolean | null);
  status: string;
  user_confirmed: (boolean | null);
  user_reviewed_at: (string | null);
  user_note: (string | null);
  created_at: string;
  updated_at: string;
};

