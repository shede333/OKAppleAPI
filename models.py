#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import base64
from collections import namedtuple
from datetime import datetime
from enum import Enum, auto
from pathlib import Path


class EnumAutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class DeviceStatus(EnumAutoName):
    """设备的状态"""
    ENABLED = auto()
    DISABLED = auto()


class DeviceClass(EnumAutoName):
    """设备的类型"""
    APPLE_WATCH = auto()
    IPAD = auto()
    IPHONE = auto()
    IPOD = auto()
    APPLE_TV = auto()
    MAC = auto()


class BundleIdPlatform(EnumAutoName):
    """设备系统类型"""
    IOS = auto()
    MAC_OS = auto()


class DataType(EnumAutoName):
    """data类型"""
    bundleIds = auto()
    devices = auto()
    certificates = auto()


class DataModel:
    """通用的数据对象"""

    def __init__(self, _id: str, _type: DataType):
        self.id = _id
        self.type = _type

    def req_params(self):
        """
        生成 用于请求的参数信息
        @return:
        """
        return {
            'id': self.id,
            'type': self.type
        }


class Device(DataModel):
    """
    设备信息
    https://developer.apple.com/documentation/appstoreconnectapi/device
    """

    def __init__(self, info_dict: dict):
        super().__init__(info_dict['id'], info_dict['type'])

        attributes = info_dict.get('attributes', {})
        self._attributes = attributes

        self.added_date = datetime.fromisoformat(attributes.get('addedDate'))  # 添加的日期
        self.name = attributes.get('name')
        self.model = attributes.get('model')  # 具体型号，例如："iPhone 13 Pro Max"
        self.udid = attributes.get('udid')

    @property
    def device_class(self) -> DeviceClass:
        """设备硬件类型"""
        return self._attributes.get('deviceClass')

    @property
    def platform(self) -> BundleIdPlatform:
        """设备系统类型"""
        return self._attributes.get('platform')

    @property
    def is_enable(self) -> bool:
        """
        当前device是否有效
        :return:
        """
        return self._attributes.get('status') == DeviceStatus.ENABLED


# 创建设备时的请求参数属性
DeviceCreateReqAttrs = namedtuple('DeviceCreateReqAttrs', 'name, udid, platform',
                                  defaults=[BundleIdPlatform.IOS])


class ProfileState(EnumAutoName):
    """profile的状态"""
    ACTIVE = auto()
    INVALID = auto()


class ProfileType(EnumAutoName):
    """profile类型"""
    IOS_APP_DEVELOPMENT = auto()
    IOS_APP_STORE = auto()
    IOS_APP_ADHOC = auto()
    IOS_APP_INHOUSE = auto()
    MAC_APP_DEVELOPMENT = auto()
    MAC_APP_STORE = auto()
    MAC_APP_DIRECT = auto()
    TVOS_APP_DEVELOPMENT = auto()
    TVOS_APP_STORE = auto()
    TVOS_APP_ADHOC = auto()
    TVOS_APP_INHOUSE = auto()
    MAC_CATALYST_APP_DEVELOPMENT = auto()
    MAC_CATALYST_APP_STORE = auto()
    MAC_CATALYST_APP_DIRECT = auto()


class ProfileAttributes:
    """
    profile的Attributes
    https://developer.apple.com/documentation/appstoreconnectapi/profile
    """

    def __init__(self, attributes: dict):
        self._attributes = attributes

        self.name = attributes.get('name')
        self.uuid = attributes.get('uuid')
        self.profile_content = attributes.get('profileContent')
        self.created_date = datetime.fromisoformat(attributes.get('createdDate'))
        self.expiration_date = datetime.fromisoformat(attributes.get('expirationDate'))
        self.profile_type = attributes.get('profileType')

    @property
    def platform(self) -> BundleIdPlatform:
        """设备系统类型"""
        return self._attributes.get('platform')

    @property
    def is_active(self) -> bool:
        """
        当前device是否有效
        :return:
        """
        return self._attributes.get('profileState') == ProfileState.ACTIVE

    def save_content(self, file_path: Path) -> Path:
        """
        将profile_content保存为mobileprovision文件
        :param file_path: 目录/文件路径，当为目录是，会自动生成文件名
        :return: 文件路径
        """
        if file_path.is_dir():
            file_name = f'{self.name}-{self.uuid}.mobileprovision'
            file_path = file_path.joinpath(file_name)
        content = base64.b64decode(self.profile_content)
        file_path.write_bytes(content)
        return file_path


class Profile:
    """
    profile信息
    https://developer.apple.com/documentation/appstoreconnectapi/profile
    """

    def __init__(self, info_dict: dict):
        self.id = info_dict['id']
        self.type = info_dict['type']

        self.attributes = ProfileAttributes(info_dict.get('attributes', {}))
        # self.relationships = ProfileRelationships(info_dict.get('relationships', {}))


BundleIdAttributes = namedtuple('BundleIdAttributes', 'identifier, name, platform, seedId')


class BundleId(DataModel):
    """BundleId信息"""

    def __init__(self, info_dict: dict):
        super().__init__(info_dict['id'], info_dict['type'])

        attributes = info_dict.get('attributes', {})
        self.attributes = BundleIdAttributes(**attributes) if attributes else None


class CertificateType(EnumAutoName):
    """cer证书的类型"""
    IOS_DEVELOPMENT = auto()
    IOS_DISTRIBUTION = auto()
    MAC_APP_DISTRIBUTION = auto()
    MAC_INSTALLER_DISTRIBUTION = auto()
    MAC_APP_DEVELOPMENT = auto()
    DEVELOPER_ID_KEXT = auto()
    DEVELOPER_ID_APPLICATION = auto()
    DEVELOPMENT = auto()
    DISTRIBUTION = auto()
    PASS_TYPE_ID = auto()
    PASS_TYPE_ID_WITH_NFC = auto()


class CertificateAttributes:
    """cer Attributes"""

    def __init__(self, attributes: dict):
        self.name = attributes['name']
        self.displayName = attributes['displayName']
        self.platform = attributes['platform']
        self.certificateType = attributes['certificateType']


class Certificate(DataModel):
    """cer证书信息"""

    def __init__(self, info_dict: dict):
        super().__init__(info_dict['id'], info_dict['type'])

        attributes = info_dict.get('attributes', {})
        self.attributes = CertificateAttributes(attributes) if attributes else None


# class ProfileCreateReqAttrs:
#     """创建profile时，请求参数里的Attributes"""
#
#     def __init__(self, name, profile_type: ProfileType):
#         self.name = name
#         self.profile_type = profile_type
#
#     def gen_req_params(self) -> dict:
#         """
#         生成用于请求的参数字典
#         @return:
#         """
#         return {
#             'name': self.name,
#             'profileType': self.profile_type
#         }

# 创建profile时，请求参数里的Attributes
ProfileCreateReqAttrs = namedtuple('ProfileCreateReqAttrs', 'name, profileType',
                                   defaults=[ProfileType.IOS_APP_DEVELOPMENT.value])


class ProfileCreateReqRelationships:
    """创建profile时，请求参数里的Relationships"""

    def __init__(self, relationships: dict):
        bundle_id_data = relationships['bundleId'].get('data', {})
        certificates_datas = relationships['certificates'].get('data', [])
        devices_datas = relationships['devices'].get('data', [])

        self.bundleId = DataModel(**bundle_id_data) if bundle_id_data else None
        self.certificates = [DataModel(**tmp_data) for tmp_data in certificates_datas]
        self.devicesType = [DataModel(**tmp_data) for tmp_data in devices_datas]
