#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import json
from datetime import timedelta
from urllib.parse import urljoin, urlencode

import jwt
import requests

from models import *

BASE_API = "https://api.appstoreconnect.apple.com"


def create_full_url(path: str, params: dict = None) -> str:
    """
    创建完整的url
    """
    url = urljoin(BASE_API, path)
    if params:
        return urljoin(url, urlencode(params))
    else:
        return url


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

        result.raise_for_status()
        json_info = result.json()
        if 'errors' in json_info:
            error_info = json_info['errors'][0]
            raise APIError(str(error_info))

        return json_info

    def create_a_profile(self):
        pass

    def delete_a_profile(self):
        pass

    def update_a_profile(self):
        pass

    def list_profiles(self) -> list[ProfileModel]:
        """
        mobileprovision列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_profiles
        """
        endpoint = '/v1/profiles'
        params = {
            'limit': 200
        }
        url = create_full_url(endpoint, params)
        result_dict = self._api_call(url)
        model_list = []
        for tmp_dict in result_dict['data']:
            model_list.append(ProfileModel(tmp_dict))
        return model_list

    def list_devices(self) -> list[DeviceModel]:
        """
        设备列表，仅包含有效状态的设备
        https://developer.apple.com/documentation/appstoreconnectapi/list_devices
        """
        endpoint = '/v1/devices'
        params = {
            'limit': 200,
            'filter[status]': DeviceStatus.ENABLED,
            'filter[platform]': BundleIdPlatform.IOS
        }
        url = create_full_url(endpoint, params)
        result_dict = self._api_call(url)
        model_list = []
        for tmp_dict in result_dict['data']:
            model_list.append(DeviceModel(tmp_dict))
        return model_list

    def register_a_device(self, device_info: DeviceCreateReqAttrs):
        """
        注册一个设备
        https://developer.apple.com/documentation/appstoreconnectapi/register_a_new_device
        """
        endpoint = '/v1/devices'
        url = create_full_url(endpoint)
        post_data = {
            'data': {
                'attributes': device_info._asdict(),
                'type': 'devices'
            }
        }
        self._api_call(url, method=HttpMethod.POST, post_data=post_data)
