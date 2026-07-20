/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Individual score components for duplicate detection.
 */
export type DuplicateScoreComponentsSchema = {
  store_name_score?: (number | null);
  amount_score?: (number | null);
  date_score?: (number | null);
  metadata_score?: (number | null);
  image_hash_score?: (number | null);
  ocr_similarity_score?: (number | null);
  composite_score: number;
  has_sufficient_data: boolean;
};

