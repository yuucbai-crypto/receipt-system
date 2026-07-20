/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to find potential duplicates for a receipt.
 */
export type FindDuplicatesRequest = {
  /**
   * Receipt ID to check for duplicates
   */
  receipt_id: number;
  /**
   * Maximum number of results
   */
  limit?: number;
  /**
   * Minimum composite score
   */
  min_score?: number;
};

