/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to list approved files.
 */
export type ApprovedFileListRequest = {
  /**
   * Filter by category folder
   */
  category?: (string | null);
  /**
   * Filter by year-month (YYYY-MM)
   */
  year_month?: (string | null);
  /**
   * Page number
   */
  page?: number;
  /**
   * Page size
   */
  page_size?: number;
};

