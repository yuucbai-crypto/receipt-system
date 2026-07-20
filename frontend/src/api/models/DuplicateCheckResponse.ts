/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DuplicateScoreComponentsSchema } from './DuplicateScoreComponentsSchema';
/**
 * Response for duplicate check operation.
 */
export type DuplicateCheckResponse = {
  /**
   * Whether duplicate was detected
   */
  is_duplicate: boolean;
  /**
   * Composite similarity score
   */
  composite_score: number;
  /**
   * Individual score components
   */
  score_components: DuplicateScoreComponentsSchema;
  /**
   * ID of saved DuplicateCheck record
   */
  duplicate_check_id?: (number | null);
  /**
   * Error message if check failed
   */
  error?: (string | null);
};

