#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import json
from datetime import timedelta
from pprint import pprint
from urllib.parse import urljoin, urlencode

import jwt
import requests

from models import *

BASE_API = "https://api.appstoreconnect.apple.com"
MAX_LIMIT = 200


def create_full_url(path: str, params: dict = None, filters: dict = None) -> str:
    """
    创建完整的url
    """
    url = urljoin(BASE_API, path)
    params = params.copy() if params else {}

    if filters:
        for tmp_key, tmp_value in filters.items():
            params[f'filter[{tmp_key}]'] = tmp_value
    if params:
        return f'{url}?{urlencode(params)}'
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

    def ensure_valid(self):
        """
        确保token有效
        @return:
        """
        if not self._token_is_valid():
            self._generate_token()


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

    def _api_call(self, url, method=HttpMethod.GET, post_data=None, verbose=False):
        """
        发起请求
        @param url: 完整的url
        @param method: http方法类型
        @param post_data: post类型时，传递的body参数
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        if verbose:
            print(url)
        headers = {"Authorization": f"Bearer {self.token_manager.token}"}

        try:
            if method == HttpMethod.GET:
                result = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == HttpMethod.POST:
                if verbose and post_data:
                    print(f'post-body: {post_data}')
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
        if verbose:
            pprint(json_info)
        if 'errors' in json_info:
            error_info = json_info['errors'][0]
            raise APIError(str(error_info))

        return json_info

    def list_bundle_id(self, filters: dict = None, verbose=False) -> list[BundleId]:
        """
        bundle id 列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_bundle_ids
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/bundleIds'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        model_list = []
        for tmp_dict in result_dict.get('data', []):
            model_list.append(BundleId(tmp_dict))
        return model_list

    def list_certificates(self, filters: dict = None, verbose=False) -> list[Certificate]:
        """
        certificate列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_certificates
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/certificates'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        model_list = []
        for tmp_dict in result_dict.get('data', []):
            model_list.append(Certificate(tmp_dict))
        return model_list

    def list_profiles(self, filters: dict = None, verbose=False) -> list[Profile]:
        """
        profile(mobileprovision)列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_and_download_profiles
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/profiles'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        model_list = []
        for tmp_dict in result_dict.get('data', []):
            model_list.append(Profile(tmp_dict))
        return model_list

    def create_a_profile(self, attrs: ProfileCreateReqAttrs, bundle_id: DataModel,
                         devices: list[DataModel], certificates: list[DataModel]) -> Profile:
        """
        创建一个新profile
        @param attrs: profile属性信息，保留name, profileType
        @param bundle_id: app的bundle_id
        @param devices: 设备信息列表
        @param certificates: cer证书信息列表
        @return:
        """
        endpoint = '/v1/profiles'
        url = create_full_url(endpoint)
        post_data = {
            'data': {
                'type': 'profiles',
                'attributes': attrs._asdict(),
                'relationships': {
                    'bundleId': {
                        'data': bundle_id.req_params()
                    },
                    'devices': {
                        'data': [tmp_model.req_params() for tmp_model in devices]
                    },
                    'certificates': {
                        'data': [tmp_model.req_params() for tmp_model in certificates]
                    }
                },
            }
        }
        result_dict = self._api_call(url, method=HttpMethod.POST, post_data=post_data)
        data_dict = result_dict.get('data', {})
        if data_dict:
            return Profile(data_dict)

    def delete_a_profile(self, profile_id: str):
        """
        删除一个profile证书
        @param profile_id: 证书ID
        @return:
        """
        endpoint = f'/v1/profiles/{profile_id}'
        url = create_full_url(endpoint)
        self._api_call(url, method=HttpMethod.DELETE)

    def list_devices(self, filters: dict = None, verbose=False) -> list[Device]:
        """
        设备列表，仅包含有效状态的设备
        https://developer.apple.com/documentation/appstoreconnectapi/list_devices
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/devices'
        params = {
            'limit': MAX_LIMIT
        }

        # filters = {
        #     'status': DeviceStatus.ENABLED.value,
        #     'platform': BundleIdPlatform.IOS.value
        # }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        model_list = []
        for tmp_dict in result_dict['data']:
            model_list.append(Device(tmp_dict))
        return model_list

    def register_a_device(self, device_info: DeviceCreateReqAttrs):
        """
        注册一个新设备
        https://developer.apple.com/documentation/appstoreconnectapi/register_a_new_device
        @param device_info: 设备信息model
        @return:
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
