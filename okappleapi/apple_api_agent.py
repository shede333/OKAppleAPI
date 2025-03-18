#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import os
import json
import time
import hashlib
from datetime import timedelta
from pprint import pprint
from typing import List, Tuple, Optional
from urllib.parse import urljoin, urlencode

import jwt
import requests

from .models import *

BASE_API = "https://api.appstoreconnect.apple.com"
MAX_LIMIT = 200


def create_full_url(path: str, params: Dict = None, filters: Dict = None,
                    fields: Dict = None) -> str:
    """
    创建完整的url
    """
    url = urljoin(BASE_API, path)
    params = params.copy() if params else {}

    if filters:
        for tmp_key, tmp_value in filters.items():
            params[f'filter[{tmp_key}]'] = tmp_value
    if fields:
        for tmp_key, tmp_value in fields.items():
            params[f'fields[{tmp_key}]'] = tmp_value
    if params:
        return f'{url}?{urlencode(params)}'
    else:
        return url


def is_auth_error(code: str, status: str):
    """
    用于判定是否需要重试（即重新发起请求），目前仅验证信息过期才会重新发起请求
    @param code: 错误码
    @param status: 错误文案
    @return:
    """
    is_retry = (int(status) == 401) and (code == 'NOT_AUTHORIZED')
    return is_retry, 1


class TokenManager:
    """token管理器"""

    def __init__(self, issuer_id: str, key_id: str, key, valid_second: int = 120):
        """
        初始化方法
        @param issuer_id: issuer_id
        @param key_id: key_id
        @param key: key文件内容，或者key文件路径（即*.p8文件路径）
        @param valid_second: 新生成的token的有效时间，单位：秒
        """
        self.issuer_id = issuer_id
        self.key_id = key_id
        self.valid_second = valid_second

        tmp_path = Path(key)
        if (isinstance(key, str) and '-----BEGIN' not in key) and tmp_path.is_file():
            self.key = tmp_path.read_text()
        else:
            self.key = key

        self._token_gen_date = None
        self._token_expired_date = None

        self._token = None

    @classmethod
    def from_json(cls, json_info):
        """
        支持送json文件里读取配置来初始化
        @param json_info: json配置信息内容，或者json文件路径，json参数参考TokenManager初始化方法的参数
        @return:
        """
        tmp_path = Path(json_info)
        if tmp_path.is_file():
            json_info = json.loads(tmp_path.read_text())
        return TokenManager(**json_info)

    def renew_token(self):
        """
        生成新的token
        :return:
        """
        self._token_gen_date = datetime.now()
        self._token_expired_date = self._token_gen_date + timedelta(seconds=self.valid_second)

        payload = {'iss': self.issuer_id,
                   # 'iat': int(self._token_gen_date.timestamp()),
                   'exp': int(self._token_expired_date.timestamp()),
                   'aud': 'appstoreconnect-v1'}
        self._token = jwt.encode(payload=payload,
                                 key=self.key,
                                 headers={'kid': self.key_id, 'typ': 'JWT'},
                                 algorithm='ES256')
        return self._token

    def _token_is_valid(self):
        """
        当前的token信息是否有效
        :return:
        """
        if not self._token:
            return False
        diff_second = 30 if (self.valid_second <= 180) else 60
        tmp_expired_date = self._token_expired_date - timedelta(seconds=diff_second)
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
            return self.renew_token()

    def ensure_valid(self):
        """
        确保token有效
        @return:
        """
        if not self._token_is_valid():
            self.renew_token()


class HttpMethod(Enum):
    GET = 1
    POST = 2
    PATCH = 3
    DELETE = 4
    PUT = 5


class APIError(Exception):
    def __init__(self, error_text, error_list: List = None, status_code=None):
        self.error_list = error_list if error_list else []
        try:
            self.status_code = int(status_code)
        except (ValueError, TypeError):
            pass
        super().__init__(error_text)


class APIAgent:
    """api客户端"""

    def __init__(self, token_manager: TokenManager, timeout=None):
        self.timeout = timeout
        self.token_manager = token_manager

    def _api_call(self, url, method=HttpMethod.GET, headers=None, post_data=None, verbose=False,
                  retry_num=2, retry_judge_func=None) -> Dict:
        """
        发起请求
        @param url: 完整的url
        @param method: http方法类型
        @param post_data: post类型时，传递的body参数
        @param verbose: 是否打印详细信息，默认False
        @param retry_num: 请求失败后，如果需要重试，重试的次数，默认重试2次
        @param retry_judge_func: 判断是否需要重试方法，该方法需要有2个参数，2个返回值，默认为空代表返回YES
        @return:
        """
        if verbose:
            print(url)
        headers = headers if headers else {}
        headers["Authorization"] = f"Bearer {self.token_manager.token}"

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
            elif method == HttpMethod.PUT:
                result = requests.put(url=url, headers=headers, data=post_data, timeout=self.timeout)
            else:
                raise APIError("Unknown HTTP method")
        except requests.exceptions.Timeout:
            raise APIError(f"Read timeout after {self.timeout} seconds")

        try:
            json_info = result.json()
        except Exception:
            json_info = {}

        if not json_info:
            result.raise_for_status()

        if verbose:
            pprint(json_info)
        if 'errors' in json_info:
            errors = list(json_info['errors'])
            for error_dict in errors:
                if retry_num <= 0:
                    continue
                status = error_dict.get('status', '0')
                code = error_dict.get('code')
                is_retry = True  # 默认会重试
                sleep_time = 1  # 默认重试前，需要等待1秒
                if retry_judge_func:
                    is_retry, sleep_time = retry_judge_func(code=code, status=status)
                if not is_retry:
                    continue
                pprint(error_dict)
                print(f'retry_num: {retry_num}, will sleep {sleep_time}s, retry url: {url}')
                if sleep_time > 0:
                    time.sleep(sleep_time)
                return self._api_call(url=url, method=method, post_data=post_data,
                                      verbose=verbose, retry_num=(retry_num - 1))

            raise APIError(str(errors), error_list=errors, status_code=result.status_code)

        return json_info

    def list_certificates(self, filters: Dict = None, verbose=False) -> List[Certificate]:
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

    def download_certificate(self, cer_id: str, filters: Dict = None, verbose=False) \
            -> Optional[Certificate]:
        """
        下载签名证书，扩展名一般为 .cer
        @param cer_id: 证书id
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return: Certificate证书对象
        """
        endpoint = f'/v1/certificates/{cer_id}'
        url = create_full_url(endpoint, filters=filters)
        result_dict = self._api_call(url, verbose=verbose)
        tmp_dict = result_dict.get('data', {})
        return Certificate(tmp_dict) if tmp_dict else None

    def create_certificates(self, csr_content: str, certificate_type: str,
                            verbose=False) -> Optional[Certificate]:
        """
        请求创建签名证书
        https://developer.apple.com/documentation/appstoreconnectapi/create_a_certificate
        @param csr_content: csr内容字符串（即certSigningRequest文件里 begin和end之间的内容，同时去除换行）
        @param certificate_type: 证书类型，CertificateType枚举类型对应的字符串
        @param verbose: 是否打印详细信息，默认False
        @return: Certificate证书对象
        """
        endpoint = 'v1/certificates'
        url = create_full_url(endpoint)
        if isinstance(certificate_type, CertificateType):
            certificate_type = certificate_type.value  # 兼容老接口的参数
        post_data = {
            'data': {
                'attributes': {
                    'csrContent': csr_content,
                    'certificateType': certificate_type
                },
                'type': 'certificates'
            }
        }
        result_dict = self._api_call(url, method=HttpMethod.POST, post_data=post_data,
                                     verbose=verbose)
        tmp_dict = result_dict.get('data', {})
        return Certificate(tmp_dict) if tmp_dict else None

    def list_bundle_id(self, filters: Dict = None, verbose=False) -> List[BundleId]:
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
        tmp_url = create_full_url(endpoint, params, filters)

        model_list = []
        def _req_bundle_id_list(full_url: str):
            result_dict = self._api_call(full_url, verbose=verbose)
            for tmp_dict in result_dict.get('data', []):
                model_list.append(BundleId(tmp_dict))

            links = result_dict.get('links', {})
            next_link = links.get('next')
            if next_link:
                if verbose:
                    print('\n\nnext:', next_link)
                _req_bundle_id_list(next_link)

        _req_bundle_id_list(tmp_url)

        return model_list

    def register_bundle_id(self, bundle_id: str, name, platform=BundleIdPlatform.IOS.value) -> Dict:
        """
        注册一个新的bundle_id
        https://developer.apple.com/documentation/appstoreconnectapi/register_a_new_bundle_id
        @param bundle_id: 新的bundle_id
        @param name: 新bundle_id的名字
        @param platform: 平台类型，默认为iOS
        @return:
        """
        endpoint = 'v1/bundleIds'
        url = create_full_url(endpoint)
        post_data = {
            'data': {
                'attributes': {
                    'identifier': bundle_id,
                    'name': name,
                    'platform': platform
                },
                'type': 'bundleIds'
            }
        }
        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data)
        return result

    def list_profiles(self, filters: Dict = None, verbose=False) -> List[Profile]:
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
                         devices: List[DataModel], certificates: List[DataModel]) -> Profile:
        """
        创建一个新profile
        https://developer.apple.com/documentation/appstoreconnectapi/create_a_profile
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
        https://developer.apple.com/documentation/appstoreconnectapi/delete_a_profile
        @param profile_id: 证书ID
        @return:
        """
        endpoint = f'/v1/profiles/{profile_id}'
        url = create_full_url(endpoint)
        self._api_call(url, method=HttpMethod.DELETE)

    def list_devices(self, filters: Dict = None, verbose=False) -> List[Device]:
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

    def register_a_device(self, device_info: DeviceCreateReqAttrs) -> \
            Tuple[Dict, Optional[Device]]:
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

        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data)
        if isinstance(result, dict) and result['data']:
            return result, Device(result['data'])
        else:
            return result, None

    def modify_a_device(self, device_id: str, device_name: Optional[str] = None,
                        device_status=DeviceStatus.ENABLED):
        """
        修改设备信息：name, status
        https://developer.apple.com/documentation/appstoreconnectapi/modify_a_registered_device
        @param device_id: 设备id
        @param device_name: 设备名称，不传此值代表 不修改此值
        @param device_status: 设备的状态值，仅支持"ENABLED, DISABLED"，默认为ENABLE
        @return:
        """
        device_info = {'status': device_status.value}
        if device_name:
            device_info['name'] = device_name

        endpoint = f'/v1/devices/{device_id}'
        url = create_full_url(endpoint)
        post_data = {
            'data': {
                'attributes': device_info,
                'id': device_id,
                'type': 'devices'
            }
        }

        result = self._api_call(url, method=HttpMethod.PATCH, post_data=post_data)
        if isinstance(result, dict) and result['data']:
            return result, Device(result['data'])
        else:
            return result, None

    def bundle_id_capabilities(self, inner_bundle_id: str, filters: Dict = None,
                               verbose=False) -> List[BundleIdCapability]:
        """
        设备列表，仅包含有效状态的设备
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_capabilities_for_a_bundle_id
        @param inner_bundle_id: BundleId的内部id
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/bundleIds/{inner_bundle_id}/bundleIdCapabilities'
        url = create_full_url(endpoint, filters=filters)
        result_dict = self._api_call(url, verbose=verbose)
        model_list = []
        for tmp_dict in result_dict.get('data', []):
            model_list.append(BundleIdCapability(tmp_dict))
        return model_list

    def enable_a_capabilities(self, inner_bundle_id: str, capability_type: str,
                              settings: Optional[List] = None, verbose=False) -> \
            Tuple[Dict, Optional[BundleIdCapability]]:
        """
        开始 bundleID 对应的一个能力
        https://developer.apple.com/documentation/appstoreconnectapi/enable_a_capability
        @param inner_bundle_id: BundleId的内部id
        @param capability_type: CapabilityType类型对应的字符串
        @param settings: （可选）设置信息列表，见：https://developer.apple.com/documentation/appstoreconnectapi/capabilitysetting
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/bundleIdCapabilities'
        url = create_full_url(endpoint)

        attributes = {'capabilityType': capability_type}
        if settings:
            attributes['settings'] = settings
        post_data = {
            'data': {
                'attributes': attributes,
                'relationships': {
                    'bundleId': {
                        'data': {
                            'id': inner_bundle_id,
                            'type': 'bundleIds'
                        }
                    }
                },
                'type': 'bundleIdCapabilities'
            }
        }

        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data, verbose=verbose)
        if isinstance(result, dict) and result['data']:
            return result, BundleIdCapability(result['data'])
        else:
            return result, None

    def disable_a_capabilities(self, capability_id: str):
        """
        删除bundleId的一个 capability/能力
        https://developer.apple.com/documentation/appstoreconnectapi/disable_a_capability
        @param capability_id: 代表capability的id
        @return:
        """
        endpoint = f'/v1/bundleIdCapabilities/{capability_id}'
        url = create_full_url(endpoint)
        self._api_call(url, method=HttpMethod.DELETE)

    def list_apps(self, filters: Dict = None, verbose=False) -> List[DataModel]:
        """
        App列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_apps
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/apps'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        app_list = []
        for tmp_dict in result_dict['data']:
            app_list.append(DataModel.from_dict(tmp_dict))
        return app_list
    
    def list_app_info_for_app(self, id: str, filters: Dict = None, verbose=False) -> List[DataModel]:
        """
        App信息列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_app_infos_for_an_app
        @param id: App的内部id(例如：list_apps接口中获取到的id)
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/apps/{id}/appInfos'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        app_list = []
        for tmp_dict in result_dict['data']:
            app_list.append(DataModel.from_dict(tmp_dict))
        return app_list
    
    def list_appstore_version(self, id: str, filters: Dict = None, verbose=False) -> List[DataModel]:
        """
        App提审版本列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_app_store_version_localizations_for_an_app_store_version
        @param id: App信息id(例如：list_app_info_for_app接口中获取到的id)
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/apps/{id}/appStoreVersions'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        list = []
        for tmp_dict in result_dict['data']:
            list.append(DataModel.from_dict(tmp_dict))
        return list
    
    def list_localization(self, id: str, filters: Dict = None, verbose=False) -> List[AppInfoLocalization]:
        """
        App提审版本的本地化信息列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_app_store_version_localizations_for_an_app_store_version
        @param id: App提审版本id(例如：list_appstore_version接口中获取到的id)
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/appStoreVersions/{id}/appStoreVersionLocalizations'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params, filters)
        result_dict = self._api_call(url, verbose=verbose)
        list = []
        for tmp_dict in result_dict['data']:
            list.append(AppInfoLocalization(tmp_dict))
        return list
    
    def create_localization(self, id: str, locale: str, verbose=False) -> AppInfoLocalization:
        """
        创建App提审版本的本地化信息
        https://developer.apple.com/documentation/appstoreconnectapi/create_an_app_store_version_localization
        @param id: App提审版本id(例如：list_appstore_version接口中获取到的id)
        @param locale: 语言代码（例如：zh-Hans， en-US）
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/appStoreVersionLocalizations'
        post_data = {
            'data': {
                'type': 'appInfoLocalizations',
                'attributes': {
                    'locale': locale
                },
                'relationships': {
                    'appStoreVersion': {
                        'data': {
                            'id': id,
                            'type': 'appStoreVersions'
                        }
                    }
                }
            }
        }
        url = create_full_url(endpoint)
        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data, verbose=verbose)
        data = result.get('data', {})
        if data:
            return AppInfoLocalization(data)
        
    def list_app_screenshot_set(self, id: str, filters: Dict = None, verbose=False) -> List[AppScreenshotSet]:
        """
        App提审版本的本地化信息中的截图集列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_app_screenshot_sets_for_an_app_store_version_localization
        @param id: 本地化信息id(例如：list_localization接口中获取到的id)
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/appStoreVersionLocalizations/{id}/appScreenshotSets'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params=params, filters=filters)
        result_dict = self._api_call(url, verbose=verbose)
        list = []
        for tmp_dict in result_dict['data']:
            list.append(AppScreenshotSet(tmp_dict))
        return list
    
    def create_app_screenshot_set(self, id: str, screenshotType: ScreenshotDisplayType, verbose=False) -> AppScreenshotSet:
        """创建App截图集"""
        """
        App提审版本的本地化信息中的截图集列表
        https://developer.apple.com/documentation/appstoreconnectapi/create_an_app_screenshot_set
        @param id: 本地化信息id(例如：list_localization接口中获取到的id)
        @param screenshotType: 截图集标识（枚举值。具体：https://developer.apple.com/documentation/appstoreconnectapi/screenshotdisplaytype）
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = '/v1/appScreenshotSets'
        post_data = {
            'data': {
                'type': 'appScreenshotSets',
                'attributes': {
                    'screenshotDisplayType': screenshotType.name
                },
                'relationships': {
                    'appStoreVersionLocalization': {
                        'data': {
                            'id': id,
                            'type': 'appStoreVersionLocalizations'
                        }
                    }
                }
            }
        }
        url = create_full_url(endpoint)
        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data, verbose=verbose)
        data = result.get('data', {})
        if data:
            return AppScreenshotSet(data)
        
    def list_app_screenshot(self, id: str, filters: Dict = None, verbose=False) -> List[AppScreenshot]:
        """
        截图集中所有截图列表
        https://developer.apple.com/documentation/appstoreconnectapi/list_all_app_screenshots_for_an_app_screenshot_set
        @param id: 截图集id(例如：list_app_screenshot_set接口中获取到的id)
        @param filters: 筛选器
        @param verbose: 是否打印详细信息，默认False
        @return:
        """
        endpoint = f'/v1/appScreenshotSets/{id}/appScreenshots'
        params = {
            'limit': MAX_LIMIT
        }
        url = create_full_url(endpoint, params=params, filters=filters)
        result_dict = self._api_call(url, verbose=verbose)
        list = []
        for tmp_dict in result_dict['data']:
            list.append(AppScreenshot(tmp_dict))
        return list
    
    def delete_app_screenshot(self, id: str, verbose=False):
        """
        删除App截图集中的某个截图
        https://developer.apple.com/documentation/appstoreconnectapi/delete_an_app_screenshot
        @param id: 截图id(例如：list_app_screenshott接口中获取到的id)
        @param verbose: 是否打印详细信息，默认False
        @return: 
        """
        if not id:
            return 
        endpoint = f'/v1/appScreenshots/{id}'
        url = create_full_url(endpoint)
        self._api_call(url, method=HttpMethod.DELETE, verbose=verbose)

    def create_app_screenshot(self, id: str, file_path: str, verbose=False) -> AppScreenshot:
        """
        在截图集中创建一个App截图
        https://developer.apple.com/documentation/appstoreconnectapi/create_an_app_screenshot
        @param id: 截图集id(例如：list_app_screenshot_set接口中获取到的id)
        @param verbose: 是否打印详细信息，默认False
        @return: 
        """
        endpoint = f'/v1/appScreenshots'
        post_data = {
            'data': {
                'type': 'appScreenshots',
                'attributes': {
                    'fileName': os.path.basename(file_path),
                    'fileSize': os.path.getsize(file_path)
                },
                'relationships': {
                    'appScreenshotSet': {
                        'data': {
                            'id': id,
                            'type': 'appScreenshotSets'
                        }
                    }
                }
            }
        }
        url = create_full_url(endpoint)
        result = self._api_call(url, method=HttpMethod.POST, post_data=post_data, verbose=verbose)
        data = result.get('data', {})
        if data:
            return AppScreenshot(data)
    
    def upload_app_screenshot(self, screenshot: AppScreenshot, file_path: str, verbose=False):
        """
        上传一个App截图
        https://developer.apple.com/documentation/appstoreconnectapi/uploading_assets_to_app_store_connect
        @param id: 截图集id(例如：list_app_screenshot_set接口中获取到的id)
        @param verbose: 是否打印详细信息，默认False)
        @return:
        """
        # 获取上传URL
        upload_operations = screenshot.attributes['uploadOperations']
        if not upload_operations:
            raise ValueError(f'获取截图上传URL失败')
        for upload_operation in upload_operations:
            # 分片上传
            with open(file_path, mode='rb') as file:
                file.seek(upload_operation['offset'])
                data = file.read(upload_operation['length'])

            url = upload_operation['url']
            method = HttpMethod[upload_operation['method']]
            headers={h['name']: h['value'] for h in upload_operation['requestHeaders']}
            self._api_call(url, method=method, headers=headers, post_data=data, verbose=verbose)
    
    def verify_app_screenshot(self, id: str, file_path: str, verbose=False) -> AppScreenshotState:
        """
        验证App截图集
        https://developer.apple.com/documentation/appstoreconnectapi/verify_an_app_screenshot_set
        @param id: 截图id(例如：create_app_screenshot接口中获取到的id)
        @param verbose: 是否打印详细信息，默认False
        @return: AWAITING_UPLOAD, UPLOAD_COMPLETE, COMPLETE, FAILED
        """
        endpoint = f'/v1/appScreenshots/{id}'
        post_data = {
            "data": {
                "type": "appScreenshots",
                "id": id,
                "attributes": {
                    "uploaded": True,
                    "sourceFileChecksum": hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                }
            }
        }
        url = create_full_url(endpoint)
        result_dict = self._api_call(url, method=HttpMethod.PATCH, post_data=post_data, verbose=verbose)
        data = result_dict.get('data', {})
        if data:
            return AppScreenshot(data).updateState