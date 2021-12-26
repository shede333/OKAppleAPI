#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import jwt
import requests
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum

import json

BASE_API = "https://api.appstoreconnect.apple.com"


class TokenManager:
    """token管理器"""

    def __init__(self, issuer_id, key_id, key):
        self.issuer_id = issuer_id
        self.key_id = key_id

        tmp_path = Path(key)
        if tmp_path.is_file():
            self.key = tmp_path.read_text()
        else:
            self.key = key

        self._token_gen_date = None
        self._token_expired_date = None

        self._token = None

    def _generate_token(self):
        """
        生成新的token
        :return:
        """
        self._token_gen_date = datetime.now()
        self._token_expired_date = self._token_gen_date + timedelta(minutes=2)

        payload = {'iss': self.issuer_id,
                   'iat': int(self._token_gen_date.timestamp()),
                   'exp': int(self._token_expired_date.timestamp()),
                   'aud': 'appstoreconnect-v1'}
        self._token = jwt.encode(payload=payload,
                                 key=self.key,
                                 headers={'kid': self.key_id, 'typ': 'JWT'},
                                 algorithm='ES256').decode('ascii')
        return self._token

    def _token_is_valid(self):
        """
        当前的token信息是否有效
        :return:
        """
        if not self._token:
            return False
        tmp_expired_date = self._token_expired_date - timedelta(seconds=30)
        return datetime.now() < tmp_expired_date

    @property
    def token(self):
        """
        获取token
        :return:
        """
        if self._token_is_valid():
            return self._token
        else:
            return self._generate_token()


class HttpMethod(Enum):
    GET = 1
    POST = 2
    PATCH = 3
    DELETE = 4


class APIError(Exception):
    def __init__(self, error_string, status_code=None):
        try:
            self.status_code = int(status_code)
        except (ValueError, TypeError):
            pass
        super().__init__(error_string)


class APIAgent:
    """api客户端"""

    def __init__(self, token_manager: TokenManager, timeout=None):
        self.timeout = timeout
        self.token_manager = token_manager

    def _api_call(self, url, method=HttpMethod.GET, post_data=None):
        headers = {"Authorization": f"Bearer {self.token_manager.token}"}

        try:
            if method == HttpMethod.GET:
                result = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == HttpMethod.POST:
                headers["Content-Type"] = "application/json"
                result = requests.post(url=url, headers=headers, data=json.dumps(post_data),
                                       timeout=self.timeout)
            elif method == HttpMethod.PATCH:
                headers["Content-Type"] = "application/json"
                result = requests.patch(url=url, headers=headers, data=json.dumps(post_data),
                                        timeout=self.timeout)
            elif method == HttpMethod.DELETE:
                result = requests.delete(url=url, headers=headers, timeout=self.timeout)
            else:
                raise APIError("Unknown HTTP method")
        except requests.exceptions.Timeout:
            raise APIError(f"Read timeout after {self.timeout} seconds")

        json_info = result.json()

    def create_a_profile(self):
        pass

    def delete_a_profile(self):
        pass

    def update_a_profile(self):
        pass

    def list_profiles(self):
        pass

    def list_devices(self):
        pass

    def register_a_device(self):
        pass


