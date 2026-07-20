/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApprovedFileInfo } from './ApprovedFileInfo';
/**
 * Response for approved file list.
 */
export type ApprovedFileListResponse = {
  items: Array<ApprovedFileInfo>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

