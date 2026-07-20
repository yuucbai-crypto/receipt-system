/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response for duplicate check review.
 */
export type DuplicateCheckReviewResponse = {
  success: boolean;
  duplicate_check_id: number;
  user_confirmed: boolean;
  message: string;
  error?: (string | null);
};

