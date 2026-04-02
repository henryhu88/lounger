# Lounger Web AI Example

This scaffold shows how to use Lounger with Playwright and Auto-Wing for AI-assisted web automation.

## Auto-Wing Quick Start

Auto-Wing lets you control and inspect the browser with natural language.

- `ai.ai_action(...)` performs an action on the page
- `ai.ai_query(...)` extracts structured data from the page
- `ai.ai_assert(...)` validates behavior with a natural-language assertion

The sample test in `test_dir/test_sample.py` uses Auto-Wing to search Bing for `playwright`.

## Configure `.env`

The `ai` fixture in `test_dir/conftest.py` loads environment variables with:

```python
load_dotenv()
```

Before running the sample, update the project root `.env` file with your provider and API key.

Example:

```dotenv
AUTOWING_MODEL_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

Reference table for each LLM configuration

| Provider      | Website                             | Environment Variables（`.env`）                                                                                                      | 
|---------------|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **✅OpenAI**   | https://platform.openai.com/        | `AUTOWING_MODEL_PROVIDER=openai`<br>`OPENAI_API_KEY=sk-proj-abdefghijklmnopqrstwvwxyz0123456789`                                   | 
| **✅DeepSeek** | https://platform.deepseek.com/      | `AUTOWING_MODEL_PROVIDER=deepseek`<br>`DEEPSEEK_API_KEY=sk-abdefghijklmnopqrstwvwxyz0123456789`                                    |
| **✅qwen**     | https://bailian.console.aliyun.com/ | `AUTOWING_MODEL_PROVIDER=qwen`<br>`DASHSCOPE_API_KEY=sk-abdefghijklmnopqrstwvwxyz0123456789`                                       |
| **✅doubao**   | https://console.volcengine.com/     | `AUTOWING_MODEL_PROVIDER=doubao`<br>`ARK_API_KEY=f61d2846-xxx-xxx-xxxx-xxxxxxxxxxxxx`<br>`DOUBAO_MODEL_NAME=ep-20250207200649-xxx` |
| **✅Gemini**   | https://aistudio.google.com/        | `AUTOWING_MODEL_PROVIDER=gemini`<br>`GOOGLE_API_KEY=AIabdefghijklmnopqrstwvwxyz0123456789`                                         |

Only the key for the provider you actually use is required.

## Run The Sample

Install a browser first:

```bash
playwright install chromium
```

Then run:

```bash
pytest
```

## Notes

- Do not commit real API keys.
- The default target site is configured by `base_url` in `pytest.ini`.
- If you switch providers, update `AUTOWING_MODEL_PROVIDER` in `.env`.
