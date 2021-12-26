#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from enum import Enum, auto
import base64
from pathlib import Path
from datetime import datetime


class EnumAutoName(Enum):
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
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


class DeviceModel:
    """
    设备信息
    https://developer.apple.com/documentation/appstoreconnectapi/device
    """

    def __init__(self, info_dict: dict):
        self.id = info_dict['id']

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


class ProfileState(EnumAutoName):
    """profile的状态"""
    ACTIVE = auto()
    INVALID = auto()


class ProfileModel:
    """
    mobileprovision信息
    https://developer.apple.com/documentation/appstoreconnectapi/profile
    """

    def __init__(self, info_dict: dict):
        self.id = info_dict['id']

        attributes = info_dict.get('attributes', {})
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
