/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RejectionReasonResponse } from './RejectionReasonResponse';
/**
 * Paginated list of rejection reasons.
 */
export type RejectionReasonListResponse = {
  items: Array<RejectionReasonResponse>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

