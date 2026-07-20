/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Individual search result.
 */
export type SearchResultItem = {
  receipt_id: number;
  /**
   * Relevance score
   */
  score: number;
  store_name: (string | null);
  total_amount: (number | null);
  receipt_date: (string | null);
  category: (string | null);
  tags: Array<string>;
  snippet: string;
};

