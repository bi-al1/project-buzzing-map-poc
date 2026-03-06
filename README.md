# Project Buzzing Map PoC

## 概要
本リポジトリは、Project Buzzing Map のコア機能「Video-to-Map」の技術検証用 PoC をまとめるための作業リポジトリである。

本開発リポジトリ https://github.com/bi-al1/project-buzzing-map

2026年3月6日時点で、当初想定していた構成から一部方針を変更している。特に Instagram 取得部分は、Scrapling の `StealthyFetcher` / `DynamicFetcher` を試した上で、PoC では Playwright API 直接利用で取得確認を優先している。なお、`DynamicFetcher` 自体は Playwright ベースであり、完全に別物というわけではない。動画解析部分は Gemini API 前提からローカル実行の `Qwen3.5` と `faster-whisper` 前提へ移行した。

## 現在の進捗
| 項目 | 状態 | 補足 |
|---|---|---|
| Instagram スクレイピング調査 | 方針変更済み | 2026年3月3日に Scrapling の Playwright 系 fetcher を検証し、PoC では Playwright API 直接利用での取得確認を採用した。本開発では Scrapling の fetcher も再検証する |
| 動画OCR | 検証済み | 2026年3月4日に `Qwen3.5:4b` の image API で動画フレーム中の字幕・埋め込み文字を取得できることを確認 |
| 音声文字起こし | 環境整備済み | `faster-whisper` 1.2.1 と `kotoba-whisper-v2.0-faster` を利用する前提ができている |
| 統合動画解析 | 実装あり | [`analyze_video.py`](/Users/takumi/Desktop/dev/project-buzzing-map-poc/analyze_video.py) で音声抽出・文字起こし・OCRをまとめて実行できる |
| 店舗特定 / 地図化 | 未着手 | PoC の次段階として残っている |

## 方針転換の要点
### 1. スクレイピング
- 当初案では Scrapling の `StealthyFetcher` / `StealthySession` を使う想定だった
- 2026年3月3日の検証で、`StealthyFetcher` は Instagram ログイン API で 404 となり安定しなかった
- `DynamicFetcher` は Playwright ベースで、ログインと投稿・ストーリー取得自体はできた
- ただし `fetch()` は最終的に Scrapling の `Response` を返すため、Instagram 固有の継続的なブラウザ操作を主軸にするには制御が足りなかった
- 安全性の観点では `StealthyFetcher` / `DynamicFetcher` を完全に諦める判断はまだ早い。今回の検証は AI 主導で穴が残っている可能性が高いため、本開発では再度試行する
- 現時点では Instagram 取得は Scrapling の Fetcher 抽象を主軸にせず、PoC では必要な箇所を Playwright API で直接扱い、取得できることの確認を優先している

### 2. 動画解析
- 当初案では Gemini Vision API / 外部 STT を使う想定だった
- 現時点ではローカル環境で完結する構成を優先している
- `Qwen3.5:4b` は VLM ではなくローカル LLM だが、image API を通して画像入力を与えることで動画フレーム中のテロップや場面情報を取得できた
- OCR / 画像理解: `Ollama` 上の `qwen3.5:4b`
- 音声文字起こし: `faster-whisper` + `kotoba-whisper-v2.0-faster`
- 前処理: `ffmpeg`

## 現在の技術スタック
| 項目 | 技術 |
|---|---|
| スクレイピング | Scrapling 調査済み。`DynamicFetcher` は Playwright ベースで、実装方針は必要に応じた Playwright API 直接利用寄り |
| 動画処理 | ffmpeg |
| OCR / 画像理解 | Ollama, `qwen3.5:4b` |
| 音声文字起こし | `faster-whisper`, `kotoba-whisper-v2.0-faster` |
| 実装言語 | Python 3.11+ |

## 実装済みスクリプト
### [`analyze_video.py`](/Users/takumi/Desktop/dev/project-buzzing-map-poc/analyze_video.py)
1本の動画に対して以下を順に実行する。これは PoC のために一時的に用意したスクリプトであり、そのまま本番で使う予定はないが、分析が成功した成果物として参考にする。

1. `ffmpeg` で音声を 16kHz mono wav として抽出
2. `ffmpeg` でフレーム画像を抽出
3. `faster-whisper` で日本語音声を文字起こし
4. `qwen3.5:4b` にフレーム画像を送り、字幕/OCRと簡易状況説明を生成
5. 結果を `*_analysis/analysis_result.txt` に保存

実行例:

```bash
python analyze_video.py path/to/video.mp4
```

前提:
- `ffmpeg` が使えること
- `ollama` が起動しており `qwen3.5:4b` を利用できること
- `faster-whisper` と `kotoba-whisper-v2.0-faster` が利用可能であること

## リポジトリ構成
```text
project-buzzing-map-poc/
├── README.md
├── analyze_video.py
└── docs/
    └── poc-requirements.md
```

## 次に詰めるべき点
- Playwright API を直接使う形で Instagram 投稿 / Reel を安定取得する実装をこのリポジトリに取り込む
- Reel を動画単体ではなく、`OCR + STT + キャプション + ジオタグ` を束ねた投稿データとして扱い、再利用しやすい構造化データへ落とす方針を煮詰める
- 動画を一度ローカル保存してから分析する現行フローではなく、スクレイピング中に動画を開いたタイミングで分析できないか検討する
- 店舗特定と地図描画の PoC を追加し、Video-to-Map の全体導線を確認する

## 仮方針メモ
- 現時点では、Reel の解析対象を「動画」ではなく「投稿全体」として扱う方針を仮置きしている
- 具体的には、OCR / STT / キャプション / ジオタグをセットで取得し、AI がそれらを根拠付きで構造化する流れを有力案としている
- 1投稿が1店舗とは限らず、「おすすめ喫茶店3選」のように複数店舗を含む形式を前提に、`1投稿 -> 複数店舗候補` のデータモデルを想定している
- この方針はまだ仮確定であり、本開発に向けてさらに煮詰める

### 仮のJSONスキーマ案
```json
{
  "post_data": {
    "reel_id": "string",
    "source_url": "string",
    "caption_text": "string",
    "hashtags": ["string"],
    "geotag": {
      "name": "string | null",
      "address": "string | null",
      "source_text": "string | null"
    },
    "ocr_segments": [
      {
        "start_sec": 0.0,
        "end_sec": 1.5,
        "text": "string"
      }
    ],
    "stt_segments": [
      {
        "start_sec": 0.0,
        "end_sec": 2.3,
        "text": "string"
      }
    ]
  },
  "spot_candidates": [
    {
      "spot_name": "string",
      "address_candidate": "string | null",
      "area_candidate": "string | null",
      "confidence": 0.0,
      "evidence": [
        {
          "source_type": "caption | geotag | ocr | stt",
          "text": "string"
        }
      ]
    }
  ]
}
```
