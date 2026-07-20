/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response for file sorting operation.
 */
export type FileSortResponse = {
  success: boolean;
  receipt_id: number;
  source_path: string;
  destination_path?: (string | null);
  new_filename?: (string | null);
  category_folder?: (string | null);
  year_month_folder?: (string | null);
  error?: (string | null);
};

