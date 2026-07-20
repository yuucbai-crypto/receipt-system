/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ApprovedFileListRequest } from '../models/ApprovedFileListRequest';
import type { ApprovedFileListResponse } from '../models/ApprovedFileListResponse';
import type { FileSortRequest } from '../models/FileSortRequest';
import type { FileSortResponse } from '../models/FileSortResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FileManagementService {
  /**
   * 承認済みレシートのファイル仕分け実行
   * 承認済みレシートのファイルをリネームし、勘定科目・年月フォルダに仕分けします。
   * @param requestBody
   * @returns FileSortResponse Successful Response
   * @throws ApiError
   */
  public static sortApprovedReceiptApiV1FileManagementSortApprovedPost(
    requestBody: FileSortRequest,
  ): CancelablePromise<FileSortResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/file-management/sort-approved',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 承認済みファイル一覧取得
   * 承認済みフォルダ内のファイル一覧を取得します（カテゴリ・年月でフィルタ可）。
   * @param requestBody
   * @returns ApprovedFileListResponse Successful Response
   * @throws ApiError
   */
  public static listApprovedFilesApiV1FileManagementListApprovedPost(
    requestBody: ApprovedFileListRequest,
  ): CancelablePromise<ApprovedFileListResponse> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/file-management/list-approved',
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * 承認済みファイルの期待パス取得
   * 承認済みレシートの期待されるファイルパスを取得します（ファイル存在確認用）。
   * @param receiptId
   * @returns FileSortResponse Successful Response
   * @throws ApiError
   */
  public static getApprovedFilePathApiV1FileManagementApprovedPathReceiptIdGet(
    receiptId: number,
  ): CancelablePromise<FileSortResponse> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/file-management/approved-path/{receipt_id}',
      path: {
        'receipt_id': receiptId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
