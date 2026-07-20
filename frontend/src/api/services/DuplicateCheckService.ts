/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DuplicateCheckListResponse } from '../models/DuplicateCheckListResponse';
import type { DuplicateCheckRequest } from '../models/DuplicateCheckRequest';
import type { DuplicateCheckResponse } from '../models/DuplicateCheckResponse';
import type { DuplicateCheckReviewRequest } from '../models/DuplicateCheckReviewRequest';
import type { DuplicateCheckReviewResponse } from '../models/DuplicateCheckReviewResponse';
import type { FindDuplicatesRequest } from '../models/FindDuplicatesRequest';
import type { FindDuplicatesResponse } from '../models/FindDuplicatesResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DuplicateCheckService {
  /**
   * 重複チェック実行
   * 2つのレシート間で重複チェックを実行し、総合スコアを計算します。
   * @param session
   * @param requestBody
   * @returns DuplicateCheckResponse Successful Response
   * @throws ApiError
   */
  public static checkDuplicateApiV1DuplicateCheckCheckPost(
    session: any,
    requestBody: DuplicateCheckRequest,
  ): CancelablePromise<DuplicateCheckResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/duplicate-check/check',
      query: {
        'session': session,
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 重複候補検索
   * 指定されたレシートの重複候補を検索します。
   * @param session
   * @param requestBody
   * @returns FindDuplicatesResponse Successful Response
   * @throws ApiError
   */
  public static findDuplicatesApiV1DuplicateCheckFindPost(
    session: any,
    requestBody: FindDuplicatesRequest,
  ): CancelablePromise<FindDuplicatesResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/duplicate-check/find',
      query: {
        'session': session,
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 重複チェック結果取得
   * 重複チェック結果の詳細を取得します。
   * @param duplicateCheckId
   * @returns DuplicateCheckListResponse Successful Response
   * @throws ApiError
   */
  public static getDuplicateCheckApiV1DuplicateCheckDuplicateCheckIdGet(
    duplicateCheckId: number,
  ): CancelablePromise<DuplicateCheckListResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/duplicate-check/{duplicate_check_id}',
      path: {
        'duplicate_check_id': duplicateCheckId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 重複チェック結果レビュー
   * ユーザーによる重複判定結果を記録します。
   * @param duplicateCheckId
   * @param requestBody
   * @returns DuplicateCheckReviewResponse Successful Response
   * @throws ApiError
   */
  public static reviewDuplicateCheckApiV1DuplicateCheckDuplicateCheckIdReviewPost(
    duplicateCheckId: number,
    requestBody: DuplicateCheckReviewRequest,
  ): CancelablePromise<DuplicateCheckReviewResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/duplicate-check/{duplicate_check_id}/review',
      path: {
        'duplicate_check_id': duplicateCheckId,
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * レシートの重複チェック履歴取得
   * 指定されたレシートに関連する重複チェック履歴を取得します。
   * @param receiptId
   * @returns DuplicateCheckListResponse Successful Response
   * @throws ApiError
   */
  public static getReceiptDuplicateChecksApiV1DuplicateCheckReceiptReceiptIdChecksGet(
    receiptId: number,
  ): CancelablePromise<Array<DuplicateCheckListResponse>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/duplicate-check/receipt/{receipt_id}/checks',
      path: {
        'receipt_id': receiptId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
