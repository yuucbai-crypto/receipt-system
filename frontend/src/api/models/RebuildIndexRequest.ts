/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Alias for ReindexRequest for API compatibility.
 */
export type RebuildIndexRequest = {
  /**
   * Specific receipt IDs to reindex (None = all)
   */
  receipt_ids?: (Array<number> | null);
  /**
   * Batch size for reindexing
   */
  batch_size?: number;
  /**
   * Confirm rebuild operation
   */
  confirm?: boolean;
};

