/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReceiptResponse } from './ReceiptResponse';
/**
 * Paginated receipt list response.
 */
export type ReceiptListResponse = {
  items: Array<ReceiptResponse>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

