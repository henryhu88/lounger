import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Optional

import requests

from lounger.log import log


class DingDingWebhook:
    """DingTalk robot webhook client with signature support."""

    def __init__(self, webhook_url: str, secret: str) -> None:
        """
        Initialize the DingTalk webhook client.

        :param webhook_url: The base webhook URL (without timestamp and sign).
        :param secret: The secret key used for signature calculation.
        """
        self.webhook_url = webhook_url
        self.secret = secret

    def _get_signed_webhook_url(self) -> str:
        """
        Generate a signed webhook URL with current timestamp and signature.

        :return: Full webhook URL including timestamp and sign query parameters.
        """
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    def send_autotest_report(self, result: Any, title: str = None, text: Optional[str] = None) -> None:
        """
        Send an automated test report via DingTalk markdown message.

        :param result: Test result object (e.g., from pytest), expected to have `_numcollected` and `stats`.
        :param title: Message title.
        :param text: Custom markdown text. If not provided, auto-generate from result.
        """
        if title is None:
            title = "接口自动化测试结果"

        if text is None:
            total_cases = getattr(result, "_numcollected", 0)
            stats = getattr(result, "stats", {})
            passed = len(stats.get("passed", []))
            failed = len(stats.get("failed", []))
            error = len(stats.get("error", []))
            skipped = len(stats.get("skipped", []))
            report_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            text = (
                f"#### {title} \n"
                f"  > ###### 用例总数：{total_cases}\n"
                f" > ###### 成功用例数量：{passed}\n"
                f" > ###### 失败用例数量：{failed}\n"
                f" > ###### 报错用例数量：{error}\n"
                f" > ###### 跳过用例数量：{skipped} \n"
                f" > ###### 报告生成时间：{report_time}"
            )

        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"#{title}",
                "text": text
            },
        }

        try:
            signed_url = self._get_signed_webhook_url()
            requests.post(signed_url, json=data, timeout=10)
        except Exception as e:
            log.error(e)

    def send_msg(self, title: str, text: str) -> None:
        """
        Send a custom markdown message to DingTalk.

        :param title: Message title.
        :param text: Markdown-formatted message content.
        """
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text,
            },
        }

        try:
            signed_url = self._get_signed_webhook_url()
            requests.post(signed_url, json=data, timeout=10)
        except Exception as e:
            log.error(e)
