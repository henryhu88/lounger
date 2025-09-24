import random
import time

from faker import Faker


class UserGenerator:
    """假用户数据生成器"""

    def __init__(self, ):
        """初始化生成器"""
        self._fake = Faker(locale='zh_CN')
        # 支持的邮箱域名
        self._email_domains = ['@channelwill.com', '@channelwill.cn']

    def generate_email(self, ) -> str:
        """生成指定域名的邮箱"""
        # 生成用户名部分
        username = self._fake.first_name().lower() + '.' + self._fake.last_name().lower()
        # 选择域名
        selected_domain = random.choice(self._email_domains)
        return f"test{username}{selected_domain}"

    def generate_name(self) -> str:
        """生成姓名"""
        return self._fake.name()

    def generate_phone(self) -> str:
        """生成联系方式"""
        return self._fake.phone_number()

    def project_name(self):
        """生成项目名称"""
        return f"test_project{round(time.time(), 2)}"


# 创建全局实例
fake_user_generator = UserGenerator()
