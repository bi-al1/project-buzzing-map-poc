import argparse
import subprocess
import os
import sys

def extract_audio(video_path, audio_path):
    print(f"[{video_path}] から音声を抽出しています...")
    # ffmpegを用いて動画から16kHzのwavを抽出 (Whisper向け)
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path, "-y",
        "-loglevel", "error"
    ]
    subprocess.run(cmd, check=True)

def extract_frames(video_path, frames_dir, fps=1):
    print(f"[{video_path}] から {fps}fps でフレーム画像を抽出しています...")
    os.makedirs(frames_dir, exist_ok=True)
    # ffmpegを用いて静止画を抽出
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        f"{frames_dir}/frame_%04d.jpg", "-y",
        "-loglevel", "error"
    ]
    subprocess.run(cmd, check=True)

def transcribe_audio(audio_path):
    print("Kotoba-Whisperで音声を文字起こし中...")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("エラー: faster-whisper がインストールされていません。'pip install faster-whisper' を実行してください。")
        sys.exit(1)

    # Kotoba-Whisperモデルのロード (C++ベースでMac Mシリーズに最適化)
    # 実際の運用時は "kotoba-tech/kotoba-whisper-v2.0" などを指定
    model_size = "kotoba-tech/kotoba-whisper-v2.0" # HuggingFaceのモデル名
    # 初回はダウンロードが走ります
    model = WhisperModel(model_size, device="cpu", compute_type="int8") # Mac環境(CPU/Accelerate)向け設定

    segments, info = model.transcribe(audio_path, beam_size=5, language="ja")
    
    transcript = ""
    for segment in segments:
        transcript += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
    return transcript

def analyze_frames_with_qwen(frames_dir):
    print("Qwen3.5 (Ollama) でフレーム画像を解析中 (OCR & 状況説明)...")
    results = []
    
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith(".jpg")])
    if not frames:
        return "フレーム画像が見つかりませんでした。"

    # 今回は最初のフレーム、中間、最後の数枚をピックアップ（全フレームやると重いため）
    sample_frames = [frames[0], frames[len(frames)//2], frames[-1]]
    
    for frame_name in sample_frames:
        frame_path = os.path.join(frames_dir, frame_name)
        prompt = "この画像に書かれているテキスト(テロップ/看板など)をすべて抽出し、同時に画像で何が起きているか簡潔に説明してください。"
        
        # Ollama CLIを使ってQwen3.5のVLMモデルを呼び出す
        # ※VLM対応のQwen (例: qwen-vl 等) を事前に `ollama pull qwen2.5-vl` 等で入れておく前提
        # ここではユーザの環境に合わせて qwen3.5 系(もしくはVLMモデル)を直接叩くコマンドを想定
        # (qwen3.5という名前でローカルにVLMモデルが登録されている前提)
        cmd = [
            "ollama", "run", "qwen3.5",
            prompt
        ]
        
        # 本来はollama run の標準入力に画像を渡すか、API経由が良いが、
        # ここではシンプルに概念を示す。実際のOllama API (http://localhost:11434/api/generate) に
        # base64で画像を投げるのが確実です。以下はそのAPIを利用した擬似コードに近しい実装です。
        
        import base64
        import json
        import urllib.request
        
        with open(frame_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        data = {
            "model": "qwen3.5", # ローカルに入っているVLMモデル名に合わせて変更
            "prompt": prompt,
            "images": [base64_image],
            "stream": False
        }
        
        req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps(data).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        try:
            response = urllib.request.urlopen(req)
            result_json = json.loads(response.read())
            description = result_json.get("response", "")
            results.append(f"【{frame_name} の解析】\n{description}\n")
        except Exception as e:
            results.append(f"【{frame_name} の解析エラー】: {e}")

    return "\n".join(results)

def main():
    parser = argparse.ArgumentParser(description="Kotoba-WhisperとQwen3.5を用いた動画ローカル解析スクリプト")
    parser.add_argument("video_path", help="解析する動画ファイルへのパス")
    args = parser.parse_args()

    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"エラー: {video_path} が見つかりません。")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(video_path))
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.join(base_dir, f"{video_name}_analysis")
    os.makedirs(out_dir, exist_ok=True)

    audio_path = os.path.join(out_dir, "audio.wav")
    frames_dir = os.path.join(out_dir, "frames")

    # 1. 音声と映像の分離
    extract_audio(video_path, audio_path)
    extract_frames(video_path, frames_dir, fps=1)

    # 2. 音声解析 (Kotoba-Whisper)
    transcript = transcribe_audio(audio_path)
    
    # 3. 映像解析 (Qwen 3.5 via Ollama)
    vision_analysis = analyze_frames_with_qwen(frames_dir)

    # 4. 結果の結合と出力
    final_output = f"""=================================
【動画解析結果】
ファイル: {video_path}
=================================

■ 1. 映像/OCR解析 (Qwen 3.5)
{vision_analysis}

■ 2. 音声文字起こし (Kotoba-Whisper)
{transcript}
=================================
"""
    
    out_txt = os.path.join(out_dir, "analysis_result.txt")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"\n解析完了！結果を {out_txt} に保存しました。")
    print("これをLLM(Asahi)に渡して最終的なサマリを作成させてください。")

if __name__ == "__main__":
    main()
