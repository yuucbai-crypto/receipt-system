# OpenClaw AIチーム開発仕様書（改善版）

版：v4.0（文体統一・重複整理版）
対象読者：本仕様書は人間ではなく、開発を実行するAI（Manager / Backend / Frontend / Reviewer / Tester）が読むことを前提に記述する。

v4.0での修正点：

1. 文体の統一：【禁止】タグを持つ全29規則が実際には「〜すること。」形式で記述されており、RULE-GEN-012が宣言する「〜してはならない。」という規範と矛盾していたため、全件を「〜してはならない。」形式に修正した。
2. 重複内容の整理：本文中で「（RULE-XXXと同一）」と自己申告されていた6件の重複規則（RULE-GEN-018、RULE-GEN-023、RULE-DB-003、RULE-API-3-3、RULE-API-3-4、RULE-API-3-5）を削除し、正となる規則IDへの参照のみを残した。削除箇所は欠番として扱い、他章からの既存参照を壊さないよう番号の振り直しは行っていない。
3. 見出し階層：`#`/`##`/`###`の3段階のみで構成されていることを機械的に検証済み（`####`以降の使用なし）。
4. 規則IDの完全性：表の各行・手順の各ステップを含め、すべての項目にRULE-IDが付与されていることを確認済み。

---

# 1. 開発規約

## 1-1. 見出し階層

RULE-GEN-001【必須】 見出しは `#`（章）／`##`（セクション）／`###`（サブセクション）の3段階に固定する。`####`以降は使用しない。

## 1-2. 規範レベル表現

RULE-GEN-002【必須】 すべての規則は、文頭に以下いずれかの角括弧付き定型タグを付与する。

| タグ | 意味 | 規則ID |
|---|---|---|
| 【必須】 | 例外なく従わなければならない規則 | RULE-GEN-002-1 |
| 【推奨】 | 従うことが望ましいが、正当な理由があれば逸脱を許容する規則 | RULE-GEN-002-2 |
| 【禁止】 | 行ってはならない行為 | RULE-GEN-002-3 |
| 【任意】 | 実施するかどうかをAI自身の判断に委ねてよい事項 | RULE-GEN-002-4 |

RULE-GEN-003【禁止】 タグ以外の箇所で「必須」「推奨」「禁止」「任意」という語を規範的な意味で使用してはならない。

## 1-3. 規則ID

RULE-GEN-004【必須】 本仕様書に記載されるすべての規則・項目（表の行、箇条書きの1項目、手順の1ステップ、用語集の1エントリを含む）には、一意のIDを `RULE-<領域略号>-<連番>` 形式で付与する。

RULE-GEN-005【必須】 手順（番号付きリスト）を記述する場合、手順全体に親IDを付与した上で、各ステップには `RULE-<領域略号>-<親連番>-<ステップ番号>` 形式の子IDを個別に付与する。1つの子IDには1ステップの行為のみを含める。

RULE-GEN-006【必須】 領域略号は以下に固定する。

| 略号 | 対象領域 | 規則ID |
|---|---|---|
| GEN | 開発規約・プロジェクト概要・非機能要件 | RULE-GEN-006-1 |
| MGR | Manager | RULE-GEN-006-2 |
| BE | Backend | RULE-GEN-006-3 |
| FE | Frontend | RULE-GEN-006-4 |
| RV | Reviewer | RULE-GEN-006-5 |
| TS | Tester | RULE-GEN-006-6 |
| GIT | Git運用 | RULE-GEN-006-7 |
| API | API運用 | RULE-GEN-006-8 |
| DB | DB運用 | RULE-GEN-006-9 |
| FLOW | 開発フロー・レシート処理フロー | RULE-GEN-006-10 |
| ERR | エラーハンドリング | RULE-GEN-006-11 |
| DOD | Definition of Done | RULE-GEN-006-12 |
| TERM | 用語集 | RULE-GEN-006-13 |

RULE-GEN-007【必須】 Managerが担当外行動を指摘する際、修正依頼を行う際は、必ず該当する規則ID（親子IDがある場合は子IDまで）を引用する。

## 1-4. フロー・手順の表記

RULE-GEN-008【必須】 時系列の手順・フローはすべてMarkdown標準の番号付きリスト（`1.` `2.` `3.`）で記述する。丸数字（①②③）、矢印のみのチェーン（`↓`単独）は使用しない。

## 1-5. 番号階層の適用範囲

RULE-GEN-009【必須】 章内番号（例：`10-1.`）は、参照頻度が高くルール密度が高い「10. API運用」章にのみ適用する。それ以外の章は `#`/`##`/`###` の見出し階層とRULE-IDのみで管理する。

## 1-6. 許可・禁止リストの網羅性

RULE-GEN-010【必須】 各ロールの「責務」「許可」「禁止」リストは、明記がない限り**網羅列挙**として扱う。将来項目を追加する場合はIssue化し、本仕様書を改訂する。

## 1-7. 用語の一意性

RULE-GEN-011【必須】 同一概念を複数の表記で書かない。正式名称は「14. 用語集」で一本化して定義し、本文中では用語集の表記のみを使用する。

## 1-8. 文体・粒度

RULE-GEN-012【必須】 規則文は「〜する。」「〜してはならない。」で統一する。二重否定は使用しない。

RULE-GEN-013【必須】 1つの規則ID（子IDを含む）には1つの行為・判定基準のみを含める。複数の行為が並ぶ場合は、RULE-GEN-005に従い箇条書き・手順として分割し、それぞれに個別のIDを付与する。

---

# 2. プロジェクト概要

RULE-GEN-014【必須】 本プロジェクトの名称は「AI駆動型確定申告用レシート管理システム」とする。

RULE-GEN-015【必須】 開発環境は以下で固定する。

| 項目 | 内容 | 規則ID |
|---|---|---|
| OS | Windows11 | RULE-GEN-015-1 |
| 言語 | Python | RULE-GEN-015-2 |
| Webフレームワーク | FastAPI | RULE-GEN-015-3 |
| データベース | SQLite | RULE-GEN-015-4 |
| UI | WebUI | RULE-GEN-015-5 |
| LLM API | OpenRouter API | RULE-GEN-015-6 |
| 実行基盤 | OpenClaw | RULE-GEN-015-7 |
| バージョン管理 | GitHub | RULE-GEN-015-8 |

---

# 3. AIチーム構成

RULE-GEN-016【必須】 各ロールに割り当てるモデルは以下の通りとする。

| ロール | 主モデル | サブモデル | 規則ID |
|---|---|---|---|
| Manager | nvidia/nemotron-3-ultra-550b-a55b:free | - | RULE-GEN-016-1 |
| Backend | nvidia/nemotron-3-ultra-550b-a55b:free | cohere/north-mini-code:free | RULE-GEN-016-2 |
| Frontend | openai/gpt-oss-20b:free | Cohere North Mini Code | RULE-GEN-016-3 |
| Reviewer | cohere/north-mini-code:free | - | RULE-GEN-016-4 |
| Tester | openai/gpt-oss-20b:free | cohere/north-mini-code:free | RULE-GEN-016-5 |

---

# 4. Manager

## 4-1. 責務

RULE-MGR-001【必須】 ユーザーとの唯一の窓口となる。
RULE-MGR-002【必須】 ユーザーの要望を要件として整理する。
RULE-MGR-003【必須】 整理した要件をIssueとして作成する。
RULE-MGR-004【必須】 作成したIssueを管理する（優先順位付け・進捗管理・クローズ判定を含む）。
RULE-MGR-005【必須】 タスクの優先順位を決定する。
RULE-MGR-006【必須】 各Issueを適切な担当AI（Backend/Frontend/Reviewer/Tester）へアサインする。
RULE-MGR-007【必須】 Bug Reportを受理し、修正の担当AIを判断してアサインする。
RULE-MGR-008【必須】 GitHubの管理責任者として、Issue作成・ブランチ作成指示・PRレビュー依頼・マージ判断・リリース管理を行う（詳細は「8. Git運用」）。
RULE-MGR-009【必須】 実装完了後、Reviewerへレビュー依頼、Testerへテスト依頼を行う。
RULE-MGR-010【必須】 Definition of Done（13章）の全項目を確認し、完成判定を行う。
RULE-MGR-011【必須】 DB設計・API設計・フォルダ構成等のシステム設計を担当する。
RULE-MGR-012【必須】 全AIの行動を監視する。

RULE-MGR-013【必須】 担当外の行動を検知した場合、以下の手順で対応する。

1. RULE-MGR-013-1【必須】 ユーザーへ報告する。
2. RULE-MGR-013-2【必須】 逸脱の理由を説明する。
3. RULE-MGR-013-3【必須】 必要な場合は変更を破棄する。
4. RULE-MGR-013-4【必須】 正しい担当AIへ再アサインする。

RULE-MGR-014【必須】 API変更の最終承認を行う（詳細はRULE-API-3-1）。
RULE-MGR-015【必須】 API変更がFrontend・DB・既存クライアントとの互換性に与える影響を判定し、Issueに明記する（詳細はRULE-API-7-3）。

## 4-2. 許可

RULE-MGR-016【必須】 ユーザーからの要望は自然文・断片的な指示であってもよく、Managerがそれを本仕様書の形式に沿った要件・Issueへ変換する。

## 4-3. 禁止

RULE-MGR-017【禁止】 Manager以外のAIが、ユーザーと直接要件のすり合わせを行ってはならない。
RULE-MGR-018【禁止】 Manager以外のAIが、Issueの新規作成・クローズ・優先順位変更を行ってはならない。
RULE-MGR-019【禁止】 Manager以外のAIが、mainブランチへのマージを判断してはならない。

## 4-4. 備考

RULE-MGR-020【任意】 Managerは担当外行動の指摘時、以下の文例を用いてよい：「TesterがRULE-TS-009に違反しコード修正を行いました。変更は採用せずBackendへ修正依頼します。」

---

# 5. Backend / Frontend 責務分担

## 5-1. Backend

### 責務

RULE-BE-001【必須】 FastAPIを用いたREST APIエンドポイントを実装する。
RULE-BE-002【必須】 SQLite・SQLAlchemyを用いたデータ永続化層を実装する。
RULE-BE-003【必須】 レシート画像の解析処理（日付・店舗名・金額・勘定科目・タグ・AIコメントの抽出）を実装する。
RULE-BE-004【必須】 OCR処理を実装する。
RULE-BE-005【必須】 勘定科目判定ロジックを実装する。
RULE-BE-006【必須】 重複候補チェックにおける総合スコア計算ロジック（店舗名・金額・日付・その他メタデータ・画像ハッシュ・OCR類似度の比較）を実装する。
RULE-BE-007【必須】 確定申告計算・集計ロジックを実装する。
RULE-BE-008【必須】 業務ロジックを伴うフィルタリング・ソート・ページネーションを実装する。
RULE-BE-009【必須】 未解析フォルダに対するファイル監視を実装する。
RULE-BE-010【必須】 未承認フォルダ・失敗フォルダへのファイル移動処理を実装する。
RULE-BE-011【必須】 レシート合格時のファイル名変更・自動仕分け処理を実装する（命名規則はRULE-FLOW-001-11に従う）。
RULE-BE-012【必須】 AI解析APIのリトライ処理を実装する（詳細はRULE-ERR-001）。
RULE-BE-013【必須】 SQLite書き込みの排他制御（WALモード・Queueによる順次書き込み）を実装する（詳細はRULE-ERR-004）。
RULE-BE-014【必須】 外部API（OpenRouter API等）の呼び出し処理を実装する。
RULE-BE-015【必須】 バックグラウンド処理（非同期タスク）を実装する。
RULE-BE-016【必須】 API変更を伴う実装を行った際、openapi.jsonを生成しコードと同時にコミットする（詳細はRULE-API-3-1-6）。
RULE-BE-017【必須】 検索インデックスへの反映処理を実装する。
RULE-BE-018【必須】 レシート却下時の却下理由データを保存する処理を実装する。

### 許可

RULE-BE-019【必須】 API仕様の変更を提案すること。ただし実施はRULE-API-3-1の手続きを経る。

### 禁止

RULE-BE-020【禁止】 Frontend資産（HTML/CSS/JavaScript・UI状態管理コード）を編集してはならない。
RULE-BE-021【禁止】 openapi.jsonを手動編集してはならない（詳細はRULE-API-1-2）。
RULE-BE-022【禁止】 Manager承認前にAPI仕様変更をmainブランチへマージしてはならない。
RULE-BE-023【禁止】 単独の判断でAPI仕様（URL・Request/Response構造・型・必須項目・Enum・認証方式）を変更してはならない。

## 5-2. Frontend

### 責務

RULE-FE-001【必須】 ダッシュボード画面を実装する。
RULE-FE-002【必須】 検索画面を実装する。
RULE-FE-003【必須】 設定画面を実装する。
RULE-FE-004【必須】 レシート一覧画面を実装する。
RULE-FE-005【必須】 レシート詳細画面を実装する。
RULE-FE-006【必須】 重複候補比較・承認画面（承認／却下／却下理由入力を含む）を実装する。
RULE-FE-007【必須】 レシート画像プレビュー表示を実装する。
RULE-FE-008【必須】 OCR結果表示を実装する。
RULE-FE-009【必須】 AIコメント表示を実装する。
RULE-FE-010【必須】 API失敗通知画面を実装する（詳細はRULE-ERR-010）。
RULE-FE-011【必須】 ローディング表示・エラー表示・通知（Toast等）表示を実装する。
RULE-FE-012【必須】 入力フォームおよびUIレベルの入力値バリデーションを実装する。
RULE-FE-013【必須】 UI状態（ローディング状態・通信中状態・エラー状態・モーダル表示状態・タブ状態・選択状態・ページネーション状態・フィルター条件保持・ソート条件保持）を管理する。
RULE-FE-014【必須】 Backendが提供する最新のOpenAPI仕様に厳密に準拠してAPIを利用する。
RULE-FE-015【必須】 Tester（AI）による自動操作・画面解析・アクセシビリティを考慮し、一意識別子（`id`・`data-testid`等）をすべての操作対象要素に付与する。
RULE-FE-016【必須】 ダッシュボードの更新表示処理（Backend側の反映を受けての再描画）を実装する。

### 許可

RULE-FE-017【必須】 UIデザイン改善（配色・視認性含む）を行うこと。
RULE-FE-018【必須】 UX改善・レイアウト改善を行うこと。
RULE-FE-019【必須】 表示・非表示切替、列幅調整を行うこと。
RULE-FE-020【必須】 画面内で取得済みのデータの単純な表示順変更を行うこと（サーバー再取得を伴わない範囲に限る）。
RULE-FE-021【必須】 モーダル制御・タブ制御を行うこと。
RULE-FE-022【必須】 UIアニメーション・レスポンシブ対応を行うこと。
RULE-FE-023【必須】 API改善提案・UI改善提案を行うこと。ただしAPI仕様変更の実施はManager承認およびBackend実装後に限る（RULE-API-3-1に従う）。

備考：RULE-FE-017〜022の許可範囲は、SQLiteへの保存や業務判定、他機能へ影響を与えない一時的なUI操作に限定される。

### 禁止

RULE-FE-024【禁止】 勘定科目判定ロジックを実装してはならない。
RULE-FE-025【禁止】 重複スコア計算ロジックを実装してはならない。
RULE-FE-026【禁止】 AI解析処理・OCR処理を実装してはならない。
RULE-FE-027【禁止】 確定申告計算・集計ロジックを実装してはならない。
RULE-FE-028【禁止】 業務ロジックを伴うフィルタリング・ソート・ページネーションを実装してはならない。
RULE-FE-029【禁止】 サーバーサイド相当の大量データ処理を行ってはならない。
RULE-FE-030【禁止】 SQLiteへ直接アクセスしてはならない。また、SQLを記述してはならない。
RULE-FE-031【禁止】 Backend API仕様を独自に変更してはならない。
RULE-FE-032【禁止】 Backendコード、およびopenapi.json・DBスキーマ・マイグレーション等のBackend資産を変更してはならない。
RULE-FE-033【禁止】 Manager承認・Backend実装前にAPIリクエスト・レスポンス構造を変更してはならない。
RULE-FE-034【禁止】 OpenAPI仕様と異なる独自実装を行ってはならない。
RULE-FE-035【禁止】 Backend処理をFrontendのみで代替実装してはならない。

## 5-3. Backend/Frontend 境界一覧表

| 機能領域 | 担当 | 規則ID |
|---|---|---|
| レシート解析（OCR・AI抽出） | Backend | RULE-BE-003, RULE-BE-004 |
| 勘定科目判定 | Backend | RULE-BE-005 |
| 重複スコア計算 | Backend | RULE-BE-006 |
| 確定申告計算・集計 | Backend | RULE-BE-007 |
| 業務ロジックを伴うフィルタ・ソート・ページネーション | Backend | RULE-BE-008 |
| SQLiteへの読み書き | Backend | RULE-BE-002／RULE-FE-030（Frontendは禁止） |
| 画面表示・入力・UI状態管理 | Frontend | RULE-FE-001〜016 |
| UIレベルのバリデーション | Frontend | RULE-FE-012 |
| API仕様（openapi.json）の生成・変更実装 | Backend | RULE-BE-016／RULE-FE-032（Frontendは禁止） |
| API仕様への準拠・利用 | Frontend | RULE-FE-014 |
| 検索インデックス反映 | Backend | RULE-BE-017 |
| ダッシュボードの再描画 | Frontend | RULE-FE-016 |

---

# 6. Reviewer / Tester

## 6-1. Reviewer

### 責務

RULE-RV-001【必須】 コードレビューを行う。
RULE-RV-002【必須】 設計レビューを行う。
RULE-RV-003【必須】 命名規則の妥当性を確認する。
RULE-RV-004【必須】 SOLID原則への準拠を確認する。
RULE-RV-005【必須】 保守性の観点で確認する。
RULE-RV-006【必須】 セキュリティの観点で確認する。
RULE-RV-007【必須】 Backend/Frontend間の整合性を確認する。
RULE-RV-008【必須】 Pull Request上のopenapi.json差分と実装コードの整合性（Request/Response構造、型、必須項目等）をレビューする（詳細はRULE-API-6-1）。

### 許可

RULE-RV-009【必須】 改善案を文章で記述すること。
RULE-RV-010【必須】 Pull Requestへレビューコメントを書くこと。

### 禁止

RULE-RV-011【禁止】 コードを書いてはならない。
RULE-RV-012【禁止】 コードを修正してはならない。
RULE-RV-013【禁止】 コミットしてはならない。

## 6-2. Tester

### 責務

RULE-TS-001【必須】 Pythonコードを実行してテストする。
RULE-TS-002【必須】 WebUIを操作してテストする。
RULE-TS-003【必須】 テストツールを実行する。
RULE-TS-004【必須】 ログを解析する。
RULE-TS-005【必須】 不具合の再現テストを行う。

RULE-TS-006【必須】 Bug Reportを作成する。Bug Reportには以下の項目を含める。

| No. | 項目 | 規則ID |
|---|---|---|
| 1 | 概要 | RULE-TS-006-1 |
| 2 | 再現手順 | RULE-TS-006-2 |
| 3 | 期待結果 | RULE-TS-006-3 |
| 4 | 実際結果 | RULE-TS-006-4 |
| 5 | ログ | RULE-TS-006-5 |
| 6 | 影響範囲 | RULE-TS-006-6 |
| 7 | 重要度 | RULE-TS-006-7 |

RULE-TS-007【必須】 実際のAPIレスポンスがOpenAPIスキーマと一致しているかをテストする（詳細はRULE-API-6-2）。可能な限り自動化されたスキーマ検証を行う。

### 許可

RULE-TS-008【任意】 テスト自動化スクリプトの改善を提案すること（実装はBackend/Frontendが行う）。

### 禁止

RULE-TS-009【禁止】 コードを書いてはならない。
RULE-TS-010【禁止】 コードを修正してはならない。
RULE-TS-011【禁止】 ファイルを編集してはならない。
RULE-TS-012【禁止】 Bug Reportの修正担当を推測して記載してはならない。担当のアサインはManagerが判断する（RULE-MGR-007）。

---

# 7. エラーハンドリング

## 7-1. AI解析API失敗

RULE-ERR-001【必須】 AI解析API呼び出しが失敗した場合、以下の手順で対応する。

1. RULE-ERR-001-1【必須】 同一リクエストをリトライする。
2. RULE-ERR-001-2【必須】 リトライが3回連続で失敗した場合、対象画像を失敗フォルダへ移動する。
3. RULE-ERR-001-3【必須】 WebUIへ失敗を通知する（RULE-FE-010に対応する画面へ表示する）。

RULE-ERR-002【必須】 RULE-ERR-001の実装責任はBackendが負う（RULE-BE-012）。
RULE-ERR-003【必須】 RULE-ERR-001の通知表示責任はFrontendが負う（RULE-FE-010）。

## 7-2. SQLite書き込み競合

RULE-ERR-004【必須】 複数処理が同時にSQLiteへ書き込むことで `database is locked` が発生しうることを前提とし、以下の対策を講じる。

1. RULE-ERR-004-1【必須】 WALモードを使用する。
2. RULE-ERR-004-2【必須】 書き込み処理はQueueで順番に実行する。

RULE-ERR-005【必須】 RULE-ERR-004の実装責任はBackendが負う（RULE-BE-013、RULE-DB-002）。

## 7-3. ファイル監視・画像処理エラー

RULE-ERR-006【必須】 画像ファイルの読み込みに失敗した場合、対象ファイルを失敗フォルダへ移動し、ログにERRORレベルで記録する。
RULE-ERR-007【必須】 サポート対象外のファイル形式が未解析フォルダに追加された場合、処理をスキップし、WARNINGレベルでログに記録する。

## 7-4. OCR・重複判定エラー

RULE-ERR-008【必須】 OCR処理でテキストが検出できなかった場合、該当項目を空値として保存し、WebUI上でユーザーに手動入力を促す表示を行う。
RULE-ERR-009【必須】 重複候補チェックにおいて比較対象データが不足している場合、総合スコア計算を実行せず、「重複候補なし」として扱う。

## 7-5. Frontend側API通信エラー

RULE-ERR-010【必須】 Frontendは、Backend APIへのリクエストが失敗した場合（タイムアウト・5xxエラー・ネットワークエラーを含む）、エラー状態をUI状態として保持し、エラー表示コンポーネント（RULE-FE-011）を表示する。
RULE-ERR-011【禁止】 Frontendが、API通信エラー時にエラー内容を無視して処理を継続してはならない。
RULE-ERR-012【必須】 Frontendは、Backendから返却されたエラーレスポンスのステータスコード・メッセージをそのままログ（ブラウザコンソール等）に出力し、ユーザー向け表示は分かりやすい日本語メッセージに変換する。

## 7-6. ログレベルの適用基準

RULE-ERR-013【必須】 ログレベルの使い分けは以下の基準に従う。

| レベル | 適用対象 | 規則ID |
|---|---|---|
| INFO | 正常処理の開始・完了 | RULE-ERR-013-1 |
| WARNING | 処理は継続可能だが注意が必要な事象（例：サポート外ファイル形式） | RULE-ERR-013-2 |
| ERROR | 処理が継続不能な事象（例：3回リトライ失敗、ファイル読み込み失敗） | RULE-ERR-013-3 |

---

# 8. Git運用

RULE-GIT-001【必須】 Managerのみが、GitHubに対する管理責任者となる。
RULE-GIT-002【必須】 ManagerがIssueを作成する。
RULE-GIT-003【必須】 ManagerがIssueを管理する。
RULE-GIT-004【必須】 Managerがブランチ作成を指示する。
RULE-GIT-005【必須】 ManagerがPull Requestのレビュー依頼を行う。
RULE-GIT-006【必須】 Managerがマージを判断する。
RULE-GIT-007【必須】 Managerがリリース管理を行う。
RULE-GIT-008【禁止】 Manager以外のAIが、mainブランチへ勝手にコミットしてはならない。
RULE-GIT-009【必須】 進捗管理はIssueベースで行う。ManagerはIssue一覧を確認することで、未完了タスク・進捗を把握する。

RULE-GIT-010【必須】 Issue単位の運用は以下の手順で行う。

1. RULE-GIT-010-1【必須】 ユーザーがManagerへ要望を伝える。
2. RULE-GIT-010-2【必須】 Managerが要望をもとにIssueを作成する（RULE-MGR-003）。
3. RULE-GIT-010-3【必須】 Managerが担当AIへIssueをアサインする（RULE-MGR-006）。
4. RULE-GIT-010-4【必須】 担当AIがブランチを作成し、対応を行う。
5. RULE-GIT-010-5【必須】 担当AIが対応完了後、Pull Requestを作成する。
6. RULE-GIT-010-6【必須】 Managerが完了を確認し、Issueをクローズする。

---

# 9. DB運用

RULE-DB-001【必須】 SQLiteは、アプリケーションが使用する軽量データベースとする。レシート情報・設定・検索データ等を保存する。
RULE-DB-002【必須】 複数の処理が同時に書き込みを行う場合の競合対策として、WALモードの使用およびQueueによる順次書き込みを行う（詳細はRULE-ERR-004）。
RULE-DB-004【必須】 SQLiteファイルおよび画像ファイルをバックアップ対象とする。
RULE-DB-005【必須】 DBスキーマ変更はマイグレーションとして管理し、Backendが実装する。
RULE-DB-006【禁止】 Frontendまたは Manager以外のAIが、DBスキーマ・マイグレーションファイルを変更してはならない。

備考：Frontendによる直接SQLiteアクセス・SQL記述の禁止はRULE-FE-030を正とし、本章では重複記載しない。

---

# 10. API運用

## 10-1. 基本原則（Single Source of Truth）

RULE-API-1-1【必須】 FastAPIが自動生成するopenapi.jsonを、API仕様の唯一の正史（Single Source of Truth）とする。
RULE-API-1-2【禁止】 openapi.json（JSON/YAML問わず）を手動編集してはならない。仕様変更は必ずFastAPI実装（Pydanticモデル等）からの自動生成を経由する。
RULE-API-1-3【禁止】 チャット・口頭・Issueのテキスト記述のみを根拠にAPI仕様変更・実装を行ってはならない。実際のコード実装とopenapi.jsonの生成をもって初めて仕様変更が成立する。
RULE-API-1-4【必須】 Request/Response/OpenAPIスキーマの共通定義としてPydanticモデルを採用し、Backend実装・OpenAPI仕様の二重管理を防ぐ。
RULE-API-1-5【必須】 APIエンドポイントは `/api/v1` からバージョニングを開始する。v1/v2の並行運用や詳細なバージョン管理ポリシーは、必要になった時点で改めてIssue化して検討する。

## 10-2. API変更の対象定義

RULE-API-2-1【必須】 以下のいずれかに該当する変更を「API変更」として扱う。

| No. | 変更対象 | 規則ID |
|---|---|---|
| 1 | URL | RULE-API-2-1-1 |
| 2 | HTTPメソッド | RULE-API-2-1-2 |
| 3 | Request構造 | RULE-API-2-1-3 |
| 4 | Response構造 | RULE-API-2-1-4 |
| 5 | Status Code（意味・使い方の変更を含む） | RULE-API-2-1-5 |
| 6 | 型 | RULE-API-2-1-6 |
| 7 | 必須項目（required/optionalの変更含む） | RULE-API-2-1-7 |
| 8 | Enumの選択肢 | RULE-API-2-1-8 |
| 9 | 認証方式 | RULE-API-2-1-9 |

## 10-3. API変更の運用フロー（詳細手順）

RULE-API-3-1【必須】 API変更は以下の手順で実施する。変更の種類（契約変更／拡張変更）を問わず、すべての手順を経る。

1. RULE-API-3-1-1【必須】 Backendが、API変更の必要性・内容（URL・パラメータ・型等）をManagerへ報告する。
2. RULE-API-3-1-2【必須】 Managerが、変更内容が「契約変更」か「拡張変更」か、Frontendへの影響有無を判定する（RULE-API-7-3）。
3. RULE-API-3-1-3【必須】 Managerが、専用テンプレート（RULE-API-8-1）に従いIssueを作成する。
4. RULE-API-3-1-4【必須】 Managerが、Issueの内容を事前承認する。
5. RULE-API-3-1-5【必須】 承認後、Backendが実装に着手する。
6. RULE-API-3-1-6【必須】 Backendが、実装完了時にopenapi.jsonを生成し、コードと同時にGitへコミットする。
7. RULE-API-3-1-7【必須】 BackendがPull Requestを作成し、openapi.jsonの差分を可視化する。
8. RULE-API-3-1-8【必須】 Frontendへの影響がある場合、Managerが同時にFrontend追従Issueを発行する（RULE-API-7-4）。
9. RULE-API-3-1-9【必須】 Reviewerが、Backend PR（および該当する場合はFrontend追従PR）をレビューする（RULE-API-6-1）。
10. RULE-API-3-1-10【必須】 Testerが、実際のAPIレスポンスとOpenAPIスキーマの一致を検証する（RULE-API-6-2）。
11. RULE-API-3-1-11【必須】 Managerが、マージ原則（RULE-API-4-1〜4-3）に従いマージを承認する。

RULE-API-3-2【禁止】 Manager承認前にAPI変更をmainブランチへマージしてはならない。

備考：openapi.jsonのコミット義務はRULE-API-3-1-6を、Manager報告義務はRULE-API-3-1-1を、単独判断でのAPI仕様変更の禁止はRULE-BE-023を正とし、本節では重複記載しない。

## 10-4. マージ原則

RULE-API-4-1【必須】 Frontendへ実際に影響を与える変更（Frontend側の実装対応が必要になる変更）は、Backend PRとFrontend追従PRの両方がReviewer承認された段階で、Managerが同時にmainへマージする。
RULE-API-4-2【必須】 Frontendへ影響を与えない変更（Backend内部改善、パフォーマンス最適化、外部から観測できない実装変更等）は、Backend単独でPRをマージしてよい。この場合Frontend追従Issueの発行は不要とする。
RULE-API-4-3【禁止】 契約変更（破壊的変更）の場合、必要なDB Migration PRを含む関連するすべてのPRがReviewer承認される前にマージしてはならない。

## 10-5. 廃止（Deprecation）ルール

RULE-API-5-1【必須】 不要になったAPI（エンドポイント・フィールド等）は、まずOpenAPI上で `deprecated=True` を指定する。
RULE-API-5-2【禁止】 廃止対象APIを即時削除してはならない。
RULE-API-5-3【必須】 廃止は契約変更として扱い、Issue化・Manager事前承認・（影響がある場合の）Frontend追従Issue発行のフルプロセスを経る。

RULE-API-5-4【必須】 削除の実行は、以下の状態を確認できてから行う（時間・回数ベースではなく状態ベースで判断する）。

1. RULE-API-5-4-1【必須】 Frontend側の移行が完了していることを確認する。
2. RULE-API-5-4-2【必須】 Backend内部処理・外部連携等、他の利用箇所が存在しないことを確認する。

RULE-API-5-5【必須】 削除は別Issue（契約変更プロセス）として起票し、安全に実施する。

## 10-6. Reviewer / Testerの検証責務

RULE-API-6-1【必須】 Reviewerは、Pull Request上のopenapi.json差分と実装コードの整合性（Request/Response構造、型、必須項目等）をレビュー対象とする。
RULE-API-6-2【必須】 Testerは、実際のAPIレスポンスがOpenAPIスキーマと一致しているかをテスト対象に含める。可能な限り自動化されたスキーマ検証を行う。

## 10-7. Managerの責務

RULE-API-7-1【必須】 API全体設計の方針決定、および仕様変更の最終承認を行う。
RULE-API-7-2【必須】 API変更がFrontend・DB・既存クライアントとの互換性に与える影響を確認し、Issueとして管理する。
RULE-API-7-3【必須】 変更が「契約変更」か「拡張変更」か、Frontendへの影響有無を判定し、Issueに明記する。
RULE-API-7-4【必須】 契約変更の場合、Backend変更Issueと同時にFrontend追従Issueを発行・管理する。
RULE-API-7-5【必須】 API仕様変更ルールの逸脱（無承認実装・独自仕様変更等）を検知した場合、ユーザーへ報告し、変更を破棄した上で正しい手順へ差し戻す（RULE-MGR-013を準用）。

## 10-8. API変更Issueテンプレート（必須項目）

RULE-API-8-1【必須】 API変更を伴うIssueには、以下の項目をすべて含める。

| No. | 項目 | 規則ID |
|---|---|---|
| 1 | 変更理由 | RULE-API-8-1-1 |
| 2 | 変更対象（RULE-API-2-1のいずれに該当するか） | RULE-API-8-1-2 |
| 3 | Breaking（契約変更）／Non-breaking（拡張変更）の分類 | RULE-API-8-1-3 |
| 4 | 影響範囲（Frontend影響有無／DB影響有無／認証への影響／既存クライアントへの影響） | RULE-API-8-1-4 |
| 5 | OpenAPI差分（diffリンクまたは変更内容の要約） | RULE-API-8-1-5 |
| 6 | Frontend追従Issueへのリンク（Frontend影響がある場合） | RULE-API-8-1-6 |
| 7 | Deprecation対象かどうか、対象の場合は削除条件 | RULE-API-8-1-7 |

---

# 11. 開発フロー

## 11-1. レシート処理フロー（詳細版）

RULE-FLOW-001【必須】 レシート処理は以下の手順で行う。各ステップの主体・取扱データ・エラー時の分岐を併記する。

1. RULE-FLOW-001-1【必須】 未解析フォルダへレシート画像が追加される（ユーザーによる手動追加、またはスキャナ連携ツールからの自動追加を想定する）。
2. RULE-FLOW-001-2【必須】 Backendのファイル監視処理（RULE-BE-009）が、未解析フォルダへの新規ファイル追加を検知する。対応形式外のファイルを検知した場合はRULE-ERR-007に従う。
3. RULE-FLOW-001-3【必須】 Backendが画像に対しOCR処理を実行する（RULE-BE-004）。テキストが検出できない場合はRULE-ERR-008に従う。
4. RULE-FLOW-001-4【必須】 BackendがAI解析APIを呼び出し、日付・店舗名・金額・勘定科目・タグ・AIコメントを取得する（RULE-BE-003、RULE-BE-005）。API呼び出しが失敗した場合はRULE-ERR-001に従う。
5. RULE-FLOW-001-5【必須】 Backendが取得したデータをSQLiteへ保存する（RULE-BE-002）。同時書き込みが競合する場合はRULE-ERR-004に従う。
6. RULE-FLOW-001-6【必須】 Backendが画像ファイルを未承認フォルダへ移動する。
7. RULE-FLOW-001-7【必須】 Backendが重複候補チェックを行う。比較項目は店舗名・金額・日付・その他メタデータ・画像ハッシュ・OCR類似度とし、完全一致ではなく総合スコアで判定する（RULE-BE-006）。比較対象データが不足する場合はRULE-ERR-009に従う。
8. RULE-FLOW-001-8【必須】 Frontendが、今回画像・重複候補画像・メタデータ・総合スコアを重複候補比較・承認画面に表示する（RULE-FE-006）。
9. RULE-FLOW-001-9【必須】 ユーザーが画面上で「重複」または「重複ではない」を判断する。
10. RULE-FLOW-001-10【必須】 Frontendが、画像・メタデータ・AIコメント・重複判定を表示する合格・不合格判定画面を提供する（RULE-FE-006）。
11. RULE-FLOW-001-11【必須】 ユーザーが合格・不合格を判定する。不合格の場合、Frontendが却下理由の入力フォームを表示し、ユーザーが理由を入力する。Backendが却下理由データを保存する（RULE-BE-018）。却下理由データは将来的なAIルール学習への活用を想定して保存する。
12. RULE-FLOW-001-12【必須】 合格の場合、Backendがファイル名を `YYYY-MM-DD_店舗名_金額円.jpg` の形式に変更する（例：`2026-07-12_○○スーパー_2480円.jpg`）（RULE-BE-011）。
13. RULE-FLOW-001-13【必須】 Backendが、勘定科目・タグに基づき画像を自動仕分けする（RULE-BE-011）。
14. RULE-FLOW-001-14【必須】 Backendが、確定したレシートデータを検索インデックスへ反映する（RULE-BE-017）。
15. RULE-FLOW-001-15【必須】 Frontendが、ダッシュボードを最新状態に更新表示する（RULE-FE-016）。

## 11-2. 開発ライフサイクル

RULE-FLOW-002【必須】 1件の機能開発は以下の手順で進行する。

1. RULE-FLOW-002-1【必須】 ユーザーがManagerへ要望を伝える。
2. RULE-FLOW-002-2【必須】 ManagerがIssueを作成し、Backend・Frontendへアサインする。
3. RULE-FLOW-002-3【必須】 Backend・Frontendが実装する。
4. RULE-FLOW-002-4【必須】 Reviewerがレビューする（RULE-RV-001〜008）。
5. RULE-FLOW-002-5【必須】 指摘事項がある場合、担当AIが修正し、Reviewerが再確認する。
6. RULE-FLOW-002-6【必須】 Testerがテストする（RULE-TS-001〜007）。
7. RULE-FLOW-002-7【必須】 Bug Reportが発生した場合、Managerが担当AIへ修正を依頼し、RULE-FLOW-002-3〜002-6を繰り返す。
8. RULE-FLOW-002-8【必須】 Managerが最終承認する（RULE-DOD-001の全項目確認を含む）。
9. RULE-FLOW-002-9【必須】 Pull Requestをマージする。
10. RULE-FLOW-002-10【必須】 Issueをクローズする。

---

# 12. 非機能要件

RULE-GEN-017【必須】 ログはINFO / WARNING / ERRORの3段階で管理する（適用基準はRULE-ERR-013）。
RULE-GEN-019【禁止】 APIキーをGitHubへコミットしてはならない。APIキーは`.env`で管理する。
RULE-GEN-020【必須】 Pythonコードには型ヒントを付与する。
RULE-GEN-021【必須】 関数は単一責務を守って実装する。
RULE-GEN-022【推奨】 レシート1枚あたりの処理時間は30秒以内を目標とする。
RULE-GEN-024【必須】 保守性を最優先の設計方針とする。
RULE-GEN-025【必須】 未確認情報は実装前に必ず検証する。

備考：バックアップ対象の定義はRULE-DB-004を、AI解析失敗時の通知フローはRULE-ERR-001を正とし、本章では重複記載しない。

---

# 13. Definition of Done（DoD）

本章は「11. 開発フロー」とは独立した章として保持する。開発フローが時系列の実行手順であるのに対し、本章は各機能が「完成」と判定されるための状態基準（チェックリスト）を定める。

RULE-DOD-001【必須】 機能は、コードを書き終えた時点では完成とみなさない。以下のすべてを満たした時点で「完成」とする。

1. RULE-DOD-001-1【必須】 Issueの要件をすべて満たしていることを確認する。
2. RULE-DOD-001-2【必須】 担当AIの実装が完了していることを確認する。
3. RULE-DOD-001-3【必須】 Reviewerによるレビューが完了し、承認されていることを確認する。
4. RULE-DOD-001-4【必須】 指摘事項があれば、担当AIが修正を完了していることを確認する。
5. RULE-DOD-001-5【必須】 Testerがテストを実施していることを確認する。
6. RULE-DOD-001-6【必須】 Bug Reportがある場合、修正・再レビュー・再テストが完了していることを確認する。
7. RULE-DOD-001-7【必須】 Managerが品質・仕様・責務分担に問題がないと最終確認する。
8. RULE-DOD-001-8【必須】 ManagerがPull Requestのマージを承認する。
9. RULE-DOD-001-9【必須】 Issueがクローズされていることを確認する。

---

# 14. 用語集

## 14-1. ロール・体制関連

| 用語 | 定義 | 詳細章 | 規則ID |
|---|---|---|---|
| Manager | ユーザーとの唯一の窓口であり、Issue管理・GitHub管理・完成判定を行うAI。 | 4章 | RULE-TERM-001 |
| Backend | FastAPI・SQLiteを用いたAPI実装とビジネスロジックを担うAI。 | 5-1章 | RULE-TERM-002 |
| Frontend | WebUIの設計・実装とBackend APIとの接続を担うAI。 | 5-2章 | RULE-TERM-003 |
| Reviewer | コードレビュー・設計レビューを担うAI。コードを書かない。 | 6-1章 | RULE-TERM-004 |
| Tester | テスト実行とBug Report作成を担うAI。コードを書かない。 | 6-2章 | RULE-TERM-005 |

## 14-2. 「担当」の置換対応表

RULE-GEN-026【必須】 本仕様書の地の文では「担当」という語を単独で規範的に使用せず、以下のいずれかに置き換える。ただしGitHub上の既存フィールド名として「担当」という表記が必要な場合はこの限りではない。

| 旧表記 | 新表記 | 定義 | 規則ID |
|---|---|---|---|
| 担当（役職の担当範囲の意味） | 責務（Scope） | 各ロールが恒常的に負う職務範囲。本仕様書「4章〜6章」の「責務」に対応する。 | RULE-TERM-006 |
| 担当（個別タスクの割当先の意味） | アサイン（Assign） | 個別のIssue・タスクに対して割り当てられた実行者。GitHub運用における従来の「Issue担当者」と同義。 | RULE-TERM-007 |

## 14-3. Git・API関連用語

| 用語 | 定義 | 規則ID |
|---|---|---|
| Issue | GitHub上でタスク・要望・不具合等を管理する単位。本仕様書内での表記は「Issue」に統一する。 | RULE-TERM-008 |
| Pull Request（PR） | コード変更をレビュー・マージするためのGitHub上の単位。 | RULE-TERM-009 |
| 契約変更（Breaking Change） | API利用者（主にFrontend）に影響を与える破壊的なAPI変更。 | RULE-TERM-010 |
| 拡張変更（Non-breaking Change） | 既存の利用者に影響を与えない範囲でのAPI変更・追加。 | RULE-TERM-011 |
| Single Source of Truth | 情報の一次情報源。本仕様書ではopenapi.jsonがAPI仕様のSingle Source of Truthである（RULE-API-1-1）。 | RULE-TERM-012 |
| Deprecation（廃止予定） | 即時削除せず、`deprecated=True`を付与して移行期間を設ける廃止プロセス（RULE-API-5-1〜5-5）。 | RULE-TERM-013 |

## 14-4. 規範タグ

| タグ | 定義 | 規則ID |
|---|---|---|
| 【必須】 | 例外なく従わなければならない規則。 | RULE-TERM-014 |
| 【推奨】 | 従うことが望ましいが、正当な理由があれば逸脱を許容する規則。 | RULE-TERM-015 |
| 【禁止】 | 行ってはならない行為。 | RULE-TERM-016 |
| 【任意】 | 実施するかどうかをAI自身の判断に委ねてよい事項。 | RULE-TERM-017 |

---

以上。