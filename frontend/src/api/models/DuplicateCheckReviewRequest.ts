/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to review a duplicate check result.
 */
export type DuplicateCheckReviewRequest = {
  /**
   * True if user confirms duplicate, False if not duplicate
   */
  user_confirmed: boolean;
  /**
   * Optional user note
   */
  user_note?: (string | null);
};

