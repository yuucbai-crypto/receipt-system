/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RebuildIndexRequest } from '../models/RebuildIndexRequest';
import type { RebuildIndexResponse } from '../models/RebuildIndexResponse';
import type { SearchIndexStatsResponse } from '../models/SearchIndexStatsResponse';
import type { SearchRequest } from '../models/SearchRequest';
import type { SearchResponse } from '../models/SearchResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SearchService {
  /**
   * レシート全文検索
   * 承認済みレシートを全文検索します（店舗名・OCRテキスト・AIコメント・タグ・カテゴリ対象）。
   * @param session
   * @param requestBody
   * @returns SearchResponse Successful Response
   * @throws ApiError
   */
  public static searchReceiptsApiV1SearchPost(
    session: any,
    requestBody: SearchRequest,
  ): CancelablePromise<SearchResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/search/',
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
   * 検索インデックス統計取得
   * 検索インデックスの統計情報を取得します。
   * @param session
   * @returns SearchIndexStatsResponse Successful Response
   * @throws ApiError
   */
  public static getSearchIndexStatsApiV1SearchStatsGet(
    session: any,
  ): CancelablePromise<SearchIndexStatsResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/search/stats',
      query: {
        'session': session,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 検索インデックス再構築
   * 全レシートから検索インデックスを再構築します。
   * @param session
   * @param requestBody
   * @returns RebuildIndexResponse Successful Response
   * @throws ApiError
   */
  public static rebuildSearchIndexApiV1SearchRebuildPost(
    session: any,
    requestBody: RebuildIndexRequest,
  ): CancelablePromise<RebuildIndexResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/search/rebuild',
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
   * 単一レシートのインデックス更新
   * 指定されたレシートの検索インデックスを更新/登録します。
   * @param receiptId
   * @param session
   * @returns RebuildIndexResponse Successful Response
   * @throws ApiError
   */
  public static indexSingleReceiptApiV1SearchIndexReceiptIdPost(
    receiptId: number,
    session: any,
  ): CancelablePromise<RebuildIndexResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/search/index/{receipt_id}',
      path: {
        'receipt_id': receiptId,
      },
      query: {
        'session': session,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 単一レシートのインデックス削除
   * 指定されたレシートを検索インデックスから削除します。
   * @param receiptId
   * @param session
   * @returns RebuildIndexResponse Successful Response
   * @throws ApiError
   */
  public static removeFromSearchIndexApiV1SearchIndexReceiptIdDelete(
    receiptId: number,
    session: any,
  ): CancelablePromise<RebuildIndexResponse> {
    return __request(OpenAPI, {
      method: 'DELETE',
      url: '/api/v1/search/index/{receipt_id}',
      path: {
        'receipt_id': receiptId,
      },
      query: {
        'session': session,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
