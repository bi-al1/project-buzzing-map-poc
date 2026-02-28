# Project Buzzing Map — PoC (Proof of Concept)

## 概要
本リポジトリは、[Project Buzzing Map](https://github.com/bi-al1/project-buzzing-map) の技術的実現性を検証するための PoC（実現性確認）プロジェクトである。

**ゴール:** コア機能「Video-to-Map」の実現に必要な技術要素を一つずつ検証し、本番開発に進めるかどうかを判断する。

## 開発方針
- **Phase 1（基盤セットアップ）のみ人間が実施**し、それ以降の Phase 2〜4 は **OpenClaw（AIエージェント）が自律的に検証**を行う
- PoC は「技術的実現性」と同時に「OpenClaw が自律的に開発タスクを遂行できるか」という開発プロセスの実現性検証も兼ねる
- PoC のコードは本番には持ち込まない「使い捨て」前提

## 技術スタック
| 項目 | 技術 |
|---|---|
| AIエージェント | OpenClaw |
| LLM（開発段階） | Gemini API |
| LLM（本番想定） | MiniMax M2.5 |
| スクレイピング | [Scrapling](https://github.com/D4Vinci/Scrapling) |

## PoC フェーズ

### Phase 1: 基盤セットアップ（人間が実施）
OpenClaw と Scrapling の環境構築・動作確認。

### Phase 2: Instagram スクレイピング（OpenClaw が実施）
Scrapling を使って Instagram から画像・動画投稿を取得できるか検証。

### Phase 3: 動画解析（OpenClaw が実施）
取得した動画からテロップ抽出（OCR）、音声文字起こし（STT）、雰囲気分析（Vision API）を検証。

### Phase 4: 店舗特定 → 地図マッピング（OpenClaw が実施）
抽出したテキストから店舗名を特定し、Google Places API 等で位置情報を取得して地図にプロットする検証。

## ディレクトリ構成
```
project-buzzing-map-poc/
├── README.md                    ← 本ファイル
├── docs/
│   └── poc-requirements.md      ← PoC 要件定義書（OpenClaw への指示書）
├── phase2-scraping/             ← Phase 2 検証コード
├── phase3-video-analysis/       ← Phase 3 検証コード
└── phase4-mapping/              ← Phase 4 検証コード
```

## 関連リポジトリ
- [Project Buzzing Map（本体）](https://github.com/bi-al1/project-buzzing-map) — プロジェクト全体の構想・設計
