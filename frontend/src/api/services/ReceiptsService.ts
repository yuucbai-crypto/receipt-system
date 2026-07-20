/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReceiptDetailResponse } from '../models/ReceiptDetailResponse';
import type { ReceiptImageResponse } from '../models/ReceiptImageResponse';
import type { ReceiptListResponse } from '../models/ReceiptListResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReceiptsService {
  /**
   * レシート一覧取得
   * レシートの一覧を取得します（フィルタ・ページング対応）。
   * @param status
   * @param categoryId
   * @param dateFrom
   * @param dateTo
   * @param page
   * @param pageSize
   * @returns ReceiptListResponse Successful Response
   * @throws ApiError
   */
  public static listReceiptsApiV1ReceiptsGet(
    status?: (string | null),
    categoryId?: (number | null),
    dateFrom?: (string | null),
    dateTo?: (string | null),
    page: number = 1,
    pageSize: number = 20,
  ): CancelablePromise<ReceiptListResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/receipts',
      query: {
        'status': status,
        'category_id': categoryId,
        'date_from': dateFrom,
        'date_to': dateTo,
        'page': page,
        'page_size': pageSize,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * レシート詳細取得
   * 指定されたレシートの詳細情報を取得します。
   * @param receiptId
   * @returns ReceiptDetailResponse Successful Response
   * @throws ApiError
   */
  public static getReceiptApiV1ReceiptsReceiptIdGet(
    receiptId: number,
  ): CancelablePromise<ReceiptDetailResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/receipts/{receipt_id}',
      path: {
        'receipt_id': receiptId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * レシート画像取得
   * 指定されたレシートの画像URLを取得します。
   * @param receiptId
   * @returns ReceiptImageResponse Successful Response
   * @throws ApiError
   */
  public static getReceiptImageApiV1ReceiptsReceiptIdImageGet(
    receiptId: number,
  ): CancelablePromise<ReceiptImageResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/receipts/{receipt_id}/image',
      path: {
        'receipt_id': receiptId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
