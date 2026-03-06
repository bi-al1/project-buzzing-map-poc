# PoC 要件定義書 — Project Buzzing Map

## 目的
本ドキュメントは、Project Buzzing Map の PoC について、2026年3月6日時点の最新方針と検証範囲を整理したものである。

- Instagram 取得: Scrapling の Playwright 系 fetcher を試した上で、PoC では必要に応じて Playwright API を直接利用
- 動画OCR / 画像理解: `Qwen3.5:4b` は VLM ではないが、image API を使って動画フレームの情報を取得
- 音声文字起こし: `faster-whisper` + `kotoba-whisper-v2.0-faster`
- 動画前処理: `ffmpeg`

## 意思決定ログ
### 2026年3月3日
- Scrapling を使った Instagram ログインと取得を調査
- `StealthyFetcher` は Instagram ログイン API で 404 となり、安定したログイン手段としては不適
- `DynamicFetcher` は Playwright ベースで、ログインとページ取得自体はできた
- ただし Scrapling の `fetch()` 抽象では、Instagram 固有の継続操作を組むには制御が不足した
- 安全性の観点では `StealthyFetcher` / `DynamicFetcher` を諦める判断はまだ早く、AI 主導の検証には穴がある可能性が高い
- 結論として、PoC では Scrapling の Fetcher 抽象だけに寄せず、必要に応じて Playwright API を直接使う方針へ変更し、本開発で Scrapling の fetcher を再検証する

### 2026年3月4日
- 実際にInstagramから取得した動画を用いて OCR 検証
- `Qwen3.5:4b` は VLM ではないが、image API を使うことで動画フレーム内の字幕・埋め込みテキストを取得可能と確認
- `faster-whisper` 1.2.1 と `kotoba-whisper-v2.0-faster` の利用前提を整備
- ローカル完結の動画解析パイプラインを PoC の中心に据えることを決定

## 現在の進捗
| Phase | 内容 | 状態 | 備考 |
|---|---|---|---|
| Phase 2 | Instagram 投稿 / Reel 取得 | 調査完了・実装方針変更 | PoC では Playwright API 直接利用で取得確認。本開発では Scrapling の fetcher を再検証する |
| Phase 3 | 動画 OCR / STT / 簡易理解 | 一部実装済み | [`analyze_video.py`](/Users/takumi/Desktop/dev/project-buzzing-map-poc/analyze_video.py) は PoC 用の暫定スクリプトとして統合実行を確認 |
| Phase 4 | 店舗特定 / 地図表示 | 未着手 | 方針のみ維持 |

## Phase 2: Instagram スクレイピング

### 目的
Instagram の公開投稿または Reel から、PoC 用の動画ファイルを安定取得できるかを検証する。

### 採用方針
- Scrapling の `StealthyFetcher` / `DynamicFetcher` を試した上で、PoC では Instagram 固有の操作に Playwright API を直接使用する
- 本開発では安全性の観点から Scrapling の fetcher 群も再度試行する
- 認証情報は環境変数で注入する
- まずはブラウザ操作の安定性を優先し、抽象化は後回しにする

### 必須タスク
1. Instagram へログインし、セッションを維持できること
2. 公開投稿または Reel ページへ遷移できること
3. 投稿内の動画 URL もしくは動画ファイル本体を取得できること
4. 同一セッションで複数ページを処理した際の失敗条件を把握できること

### 出力
- 入力 URL ごとの取得結果
- 動画ファイルの保存パス、または動画 URL
- ログイン失敗 / ブロック / CAPTCHA などの失敗要因メモ

### 成功条件
- 少なくとも1件の Reel または動画投稿から、後続処理に使える mp4 を取得できること
- 手動介入なしで再実行可能な最小フローが定義できること

## Phase 3: 動画解析

### 目的
取得した動画から、店名候補や場所の手がかりになり得る情報をローカル環境で抽出できるかを検証する。

### 採用方針
- API 依存を減らし、ローカルで再現しやすい構成を優先する
- OCR と STT を別々に抽出し、最終的に店舗特定へ渡せる形にまとめる
- まずは高精度な完全解析よりも、店名や地名の手がかり抽出を優先する
- Reel は動画単体ではなく、OCR / STT / キャプション / ジオタグを束ねた投稿データとして扱う案を仮採用する

### 現在の実装
[`analyze_video.py`](/Users/takumi/Desktop/dev/project-buzzing-map-poc/analyze_video.py) は以下の流れで処理を行う。これは PoC のために一時的に用意したスクリプトであり、本番投入は想定していない。

1. `ffmpeg` で音声を抽出する
2. `ffmpeg` でフレーム画像を抽出する
3. `faster-whisper` で日本語音声を書き起こす
4. `qwen3.5:4b` で代表フレームを解析し、字幕 / 埋め込み文字と場面説明を生成する
5. 結果をテキストファイルへ保存する

### 検証済み事項
- `Qwen3.5:4b` は動画フレーム上の字幕・埋め込み文字の抽出に使える
- `Qwen3.5:4b` は VLM ではないが、image API 経由で画像入力を扱うことで動画フレームの情報抽出に使える
- `faster-whisper` と `kotoba-whisper-v2.0-faster` を組み合わせる前提で処理を組める
- `analyze_video.py` は PoC として分析成功を確認する役割は果たした

### 仮確定しているデータ方針
- 現時点では、Reel の解析単位を「動画ファイル」ではなく「投稿全体」とみなす
- 具体的には、少なくとも以下を1セットで保持する案を有力としている
  - 動画本体
  - OCR 結果
  - STT 結果
  - キャプション
  - ジオタグ
  - 投稿 URL、投稿者、ハッシュタグなどの周辺メタデータ
- その上で AI が各情報を突き合わせ、再利用しやすい構造化データに落とす
- ただしこの方針はまだ仮確定であり、本開発に向けてさらに煮詰める

### 仮に想定している構造化の単位
- 投稿単位データ
  - 1件の Reel / 投稿から取得した OCR、STT、キャプション、ジオタグなどを束ねた元データ
- 店舗候補単位データ
  - 投稿単位データをもとに AI が抽出した店名候補、住所候補、地名候補、根拠、信頼度を保持する派生データ
- これにより、1店舗紹介動画だけでなく「おすすめ喫茶店3選」のような複数店舗動画にも対応しやすくする

### 仮のJSONスキーマ案
以下は保存形式を固めるための仮案であり、実装時に多少変わる前提とする。

#### 1. 投稿単位データ
```json
{
  "reel_id": "string",
  "platform": "instagram",
  "source_url": "string",
  "author": {
    "username": "string",
    "display_name": "string | null"
  },
  "posted_at": "ISO-8601 string | null",
  "caption_text": "string",
  "hashtags": ["string"],
  "geotag": {
    "name": "string | null",
    "address": "string | null",
    "latitude": 0.0,
    "longitude": 0.0,
    "source_text": "string | null"
  },
  "media": {
    "video_url": "string | null",
    "local_video_path": "string | null",
    "duration_sec": 0.0
  },
  "ocr_segments": [
    {
      "segment_id": "string",
      "start_sec": 0.0,
      "end_sec": 1.5,
      "frame_ref": "string | null",
      "text": "string",
      "raw_response": "string | null"
    }
  ],
  "stt_segments": [
    {
      "segment_id": "string",
      "start_sec": 0.0,
      "end_sec": 2.3,
      "speaker": "string | null",
      "text": "string",
      "raw_response": "string | null"
    }
  ],
  "analysis_meta": {
    "ocr_model": "string",
    "stt_model": "string",
    "processed_at": "ISO-8601 string",
    "notes": "string | null"
  }
}
```

想定用途:
- 投稿そのものから取得できた一次情報をなるべく失わずに保存する
- OCR / STT / キャプション / ジオタグを後で何度でも再解釈できる形で保持する
- 将来的にローカル保存なしで分析する場合でも、保存する論理構造は大きく変えない

#### 2. 店舗候補単位データ
```json
{
  "candidate_id": "string",
  "source_reel_id": "string",
  "spot_name": "string",
  "address_candidate": "string | null",
  "area_candidate": "string | null",
  "geotag_match": {
    "is_same_as_post_geotag": true,
    "reason": "string | null"
  },
  "confidence": 0.0,
  "evidence": [
    {
      "source_type": "caption | geotag | ocr | stt",
      "source_ref": "string",
      "text": "string",
      "start_sec": 0.0,
      "end_sec": 1.5
    }
  ],
  "resolver_notes": "string | null",
  "place_search": {
    "query": "string | null",
    "matched_name": "string | null",
    "matched_address": "string | null",
    "latitude": 0.0,
    "longitude": 0.0,
    "place_id": "string | null"
  }
}
```

想定用途:
- 1投稿から複数店舗候補をぶら下げられるようにする
- 候補ごとに「どの証拠からそう判断したか」を残す
- Places API など外部検索をかけた結果も同じ単位で保持する

#### 3. AI に期待する出力の最小形
AI には自由文の要約だけでなく、少なくとも以下を返させる想定にする。

```json
{
  "source_reel_id": "string",
  "spot_candidates": [
    {
      "spot_name": "string",
      "address_candidate": "string | null",
      "area_candidate": "string | null",
      "confidence": 0.0,
      "evidence": [
        {
          "source_type": "caption | geotag | ocr | stt",
          "source_ref": "string",
          "text": "string"
        }
      ]
    }
  ]
}
```

この最小形を先に決めておくことで、複数店舗動画でも後段の店舗特定処理につなぎやすくする。

### 未解決事項
- OCR 対象フレーム数が少なく、情報の取りこぼしが起こり得る
- 出力が自由文中心で、後段の店舗特定にそのままは渡しにくい
- STT と OCR を統合した店名候補抽出ロジックは未実装
- 現状は動画をローカル保存してから分析しており、スクレイピング中に動画を開いたタイミングで分析する形は未検証
- キャプション、ジオタグ、OCR、STT のどこまでを一次データとして保存し、どこからを AI の解釈結果として分離するかは今後詰める必要がある

### 成功条件
- 動画1本から、字幕・音声のどちらかで店名候補または地名候補を抽出できること
- 同じ手順を別動画にも再利用できること

## Phase 4: 店舗特定 → 地図マッピング

### 目的
Phase 2・3 で得たテキストから店舗を特定し、地図上に可視化できるかを検証する。

### 現時点の方針
- 店名候補、地名候補、動画内コンテキストを統合して店舗を特定する
- 店舗特定では OCR / STT だけでなく、キャプションとジオタグも重要な根拠として扱う
- Places API 系の外部サービス利用は依然として有力候補
- まずは単一動画から1店舗を正しく特定できることを目標にしつつ、複数店舗動画へ拡張できる形を崩さない

### 想定タスク
1. OCR / STT / キャプション / ジオタグをまとめた投稿単位データを作る
2. そこから店名候補と地名候補を抽出し、必要なら複数店舗へ分離する
3. 候補を外部検索 API に投げて店舗候補を取得する
4. 信頼度が高い候補だけを地図に描画する
5. 元の証拠データとの対応を確認できるようにする

### 成功条件
- 1本の動画から、少なくとも1件の正しい店舗候補を位置情報付きで返せること
- なぜその店舗を選んだか説明可能な根拠を保持できること

## 全体の成功基準
| # | 基準 | 重要度 |
|---|---|---|
| 1 | Playwright API を直接使う形で Instagram 動画を取得できる | 必須 |
| 2 | ローカル OCR で字幕や埋め込み文字を抽出できる | 必須 |
| 3 | ローカル STT で日本語音声を書き起こせる | 必須 |
| 4 | OCR / STT / キャプション / ジオタグを束ねた投稿単位データを作れる | 必須 |
| 5 | 店舗候補を地図上に可視化できる | 推奨 |
| 6 | 全手順を再実行可能な形で整理できる | 必須 |
| 7 | 将来的に保存前提ではない動画分析フローへ拡張可能な見通しが立つ | 推奨 |

## このリポジトリで今後追加したいもの
- Playwright API を直接使う Instagram 取得スクリプト
- Scrapling の `StealthyFetcher` / `DynamicFetcher` 再検証
- 投稿単位データと店舗候補単位データを分けて保存する処理
- スクレイピング中に動画を開いたタイミングで分析する方式の検討
- 店舗特定の試作コード
- 地図描画の最小実装
