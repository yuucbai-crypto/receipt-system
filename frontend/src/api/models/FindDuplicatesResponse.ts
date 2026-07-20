/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DuplicateCheckResponse } from './DuplicateCheckResponse';
/**
 * Response for find duplicates operation.
 */
export type FindDuplicatesResponse = {
  source_receipt_id: number;
  potential_duplicates: Array<DuplicateCheckResponse>;
};

