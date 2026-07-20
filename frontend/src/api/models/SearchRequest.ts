/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Search request parameters.
 */
export type SearchRequest = {
  /**
   * Search query (supports FTS5 syntax)
   */
  query: string;
  /**
   * Maximum results
   */
  limit?: number;
  /**
   * Pagination offset
   */
  offset?: number;
  /**
   * Filter by category
   */
  category?: (string | null);
  /**
   * Filter by date from
   */
  date_from?: (string | null);
  /**
   * Filter by date to
   */
  date_to?: (string | null);
  /**
   * Minimum amount
   */
  amount_min?: (number | null);
  /**
   * Maximum amount
   */
  amount_max?: (number | null);
};

