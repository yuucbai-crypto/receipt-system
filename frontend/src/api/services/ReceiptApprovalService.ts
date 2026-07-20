/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReceiptApprovalRequest } from '../models/ReceiptApprovalRequest';
import type { ReceiptApprovalResponse } from '../models/ReceiptApprovalResponse';
import type { ReceiptRejectRequest } from '../models/ReceiptRejectRequest';
import type { RejectionReasonListResponse } from '../models/RejectionReasonListResponse';
import type { RejectionReasonResponse } from '../models/RejectionReasonResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReceiptApprovalService {
  /**
   * レシート承認
   * レシートを承認し、ファイルを承認済みフォルダへ仕分けします。
   * @param requestBody
   * @returns ReceiptApprovalResponse Successful Response
   * @throws ApiError
   */
  public static approveReceiptApiV1ReceiptApprovalApprovePost(
    requestBody: ReceiptApprovalRequest,
  ): CancelablePromise<ReceiptApprovalResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/receipt-approval/approve',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * レシート却下
   * レシートを却下し、却下理由を保存します。
   * @param session
   * @param requestBody
   * @returns ReceiptApprovalResponse Successful Response
   * @throws ApiError
   */
  public static rejectReceiptApiV1ReceiptApprovalRejectPost(
    session: any,
    requestBody: ReceiptRejectRequest,
  ): CancelablePromise<ReceiptApprovalResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/receipt-approval/reject',
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
   * 却下理由取得
   * 指定されたレシートの却下理由を取得します。
   * @param receiptId
   * @param session
   * @returns RejectionReasonResponse Successful Response
   * @throws ApiError
   */
  public static getRejectionReasonApiV1ReceiptApprovalRejectionReasonsReceiptIdGet(
    receiptId: number,
    session: any,
  ): CancelablePromise<RejectionReasonResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/receipt-approval/rejection-reasons/{receipt_id}',
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
   * 却下理由一覧取得
   * 却下理由の一覧を取得します（フィルタ・ページング対応）。
   * @param session
   * @param category
   * @param reasonCode
   * @param isForAiTraining
   * @param page
   * @param pageSize
   * @returns RejectionReasonListResponse Successful Response
   * @throws ApiError
   */
  public static listRejectionReasonsApiV1ReceiptApprovalRejectionReasonsGet(
    session: any,
    category?: (string | null),
    reasonCode?: (string | null),
    isForAiTraining?: (boolean | null),
    page: number = 1,
    pageSize: number = 20,
  ): CancelablePromise<RejectionReasonListResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/receipt-approval/rejection-reasons',
      query: {
        'category': category,
        'reason_code': reasonCode,
        'is_for_ai_training': isForAiTraining,
        'page': page,
        'page_size': pageSize,
        'session': session,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
