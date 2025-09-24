import base64
import datetime
import logging
from typing import Any

import yaml

from lounger.utils.fake_user_generator import UserGenerator
from lounger.utils.get_configs import ConfigUtils

from lounger.log import log

config_utils = ConfigUtils("config/config.yaml")
base_config = config_utils.get_config('base_test_config')


class DebugTalk:
    """热加载工具类"""

    def env(self, key: str) -> Any:
        """
        获取项目环境地址
        :param key: 环境地址类型
        :return: 环境地址
        """
        try:
            return base_config.get(key)
        except Exception as e:
            log.error(f"获取项目环境地址时发生错误: {e}")
            return None

    def read_extract(self, var_name: str) -> Any:
        """
        读取Extract文件保存的变量值
        :param var_name: 变量名称
        :return: 变量值
        """
        try:
            with open("extract.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f)[var_name]
        except Exception as e:
            log.error(f"Extract文件未读取到{var_name}需要的结果: {e}")
            return None

    def read_token(self, token_name):
        """
        获取鉴权码
        :param token_name: Token名称
        :return: 返回Token值
        """
        try:
            with open("extract.yaml", "r", encoding="utf-8") as f:
                token_data = yaml.safe_load(f)[token_name]
                return f'Bearer {token_data}'
        except Exception as e:
            log.error(f"{token_name}未读取到Token值: {e}")
            return None

    def base64_encode(self, text: str):
        """
        base64加密
        :param text: 待加密的文本
        :return: base64编码后的字符串
        """
        try:
            if isinstance(text, str):
                text = text.encode("utf-8")
            return base64.b64encode(text).decode("utf-8")
        except Exception as e:
            log.error(f"base64加密时发生错误: {e}")
            return None

    def base64_decode(self, text: str):
        """
        base64解密
        :param text: 待解密的文本
        :return: 解密后的字符串
        """
        try:
            if isinstance(text, str):
                text = text.encode("utf-8")
            return base64.b64decode(text).decode("utf-8")
        except Exception as e:
            log.error(f"base64解密时发生错误: {e}")
            return None

    def user_info(self, key: str):
        """
        动态生成用户信息
        :param key: 用户信息类型
        :return: 用户信息
        """
        user_type = {
            "name": "generate_name",
            "phone": "generate_phone",
            "email": "generate_email",
            "project": "project_name",  # 项目名称 test_project+时间戳
        }
        try:
            return getattr(UserGenerator(), user_type.get(key))()
        except Exception as e:
            log.error(f"生成用户信息时发生错误: {e}")
            return None

    def get_random_time(self):
        """
        获取随机时间
        :return: 随机时间
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
