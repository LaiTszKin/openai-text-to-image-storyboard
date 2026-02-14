# OpenAI Text to Image Storyboard

以 OpenAI 相容格式的 Image Generation API，批次產生故事分鏡圖片。

此專案的流程是：由 agent 先決定要生成哪些提示詞，再用本工具把提示詞送到 `/images/generations`，輸出到 `pictures/<content_name>/`。

## Agent 執行規則

- 一旦取得文章/章節內容，應立即依內容拆分場景並執行腳本生成圖片。
- 除非缺少必要參數（例如輸出專案路徑、content name），否則不要停在純建議模式。

## 功能

- 預設讀取 skill 資料夾下的 `.env`（可用 `--env-file` 覆蓋）
- 支援 `--prompt` 多次輸入，或用 `--prompts-file` 一次讀取 JSON
- 圖片按順序輸出為 `01_*.png`, `02_*.png`, ...
- 產生 `storyboard.json` 保存輸入與輸出紀錄
- 已有同名檔案時自動加上 `_2`, `_3` 避免覆寫

## 安裝與需求

- Python 3.9+
- 可連線到 OpenAI 相容 API

## 快速開始

1. 在 skill 資料夾複製環境變數範本

```bash
cp .env.example .env
```

2. 編輯 `.env`

```dotenv
OPENAI_API_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key_here
OPENAI_IMAGE_MODEL=gpt-image-1
# Optional
# OPENAI_IMAGE_RATIO=16:9
# OPENAI_IMAGE_ASPECT_RATIO=16:9
# OPENAI_IMAGE_QUALITY=medium
# OPENAI_IMAGE_STYLE=vivid
```

> `OPENAI_IMAGE_RATIO` 與 `OPENAI_IMAGE_ASPECT_RATIO` 都可用，前者為推薦欄位。  
> 腳本預設會讀取 `/Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env`。

3. 執行（直接傳入多個 prompt）

```bash
python scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --env-file /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env \
  --content-name "1_小說章節名稱" \
  --prompt "cinematic rain-soaked alley, tense running pose, blue neon reflections, dramatic rim light" \
  --prompt "ancient underground library, floating dust in warm volumetric light, mysterious atmosphere"
```

4. 或使用 JSON prompt 檔

```bash
python scripts/generate_storyboard_images.py \
  --project-dir /path/to/project \
  --env-file /Users/tszkinlai/.codex/skills/openai-text-to-image-storyboard/.env \
  --content-name "1_小說章節名稱" \
  --prompts-file /path/to/prompts.json
```

`prompts.json` 範例：

```json
[
  {
    "title": "雨夜追逐",
    "prompt": "cinematic rain-soaked alley, tense running pose, blue neon reflections, dramatic rim light"
  },
  {
    "title": "地下書庫",
    "prompt": "ancient underground library, floating dust in warm volumetric light, mysterious atmosphere"
  }
]
```

## 參數重點

- `--aspect-ratio`：可覆蓋 `.env` 的比例設定（例如 `16:9`、`4:3`）
- 若未提供比例，會使用模型/服務端預設尺寸

## 輸出

輸出路徑：

- `pictures/<content_name>/01_<title>.png`
- `pictures/<content_name>/02_<title>.png`
- `pictures/<content_name>/storyboard.json`

## License

MIT，詳見 [LICENSE](LICENSE)。
