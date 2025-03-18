#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

import base64
import tempfile
from collections import namedtuple
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Union

from mobileprovision.parser import MobileProvisionModel


class EnumAutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class DeviceStatus(EnumAutoName):
    """设备的状态"""
    ENABLED = auto()
    DISABLED = auto()
    PROCESSING = auto()
    INELIGIBLE = auto()


class DeviceClass(EnumAutoName):
    """设备的类型"""
    APPLE_WATCH = auto()
    IPAD = auto()
    IPHONE = auto()
    IPOD = auto()
    APPLE_TV = auto()
    MAC = auto()

class ScreenshotDisplayType(EnumAutoName):
    """截图尺寸类型"""
    APP_IPHONE_67 = auto()
    APP_IPHONE_65 = auto()
    APP_IPHONE_61 = auto()
    APP_IPHONE_58 = auto()
    APP_IPHONE_55 = auto()
    APP_IPHONE_47 = auto()
    APP_IPHONE_40 = auto()
    APP_IPHONE_35 = auto()
    APP_IPAD_PRO_3GEN_129 = auto()
    APP_IPAD_PRO_3GEN_11 = auto()
    APP_IPAD_PRO_129 = auto()
    APP_IPAD_105 = auto()
    APP_IPAD_97 = auto()
    APP_WATCH_ULTRA = auto()
    APP_WATCH_SERIES_7 = auto()
    APP_WATCH_SERIES_4 = auto()
    APP_WATCH_SERIES_3 = auto()
    APP_DESKTOP = auto()
    APP_APPLE_TV = auto()
    IMESSAGE_APP_IPHONE_67 = auto()
    IMESSAGE_APP_IPHONE_65 = auto()
    IMESSAGE_APP_IPHONE_61 = auto()
    IMESSAGE_APP_IPHONE_58 = auto()
    IMESSAGE_APP_IPHONE_55 = auto()
    IMESSAGE_APP_IPHONE_47 = auto()
    IMESSAGE_APP_IPHONE_40 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_129 = auto()
    IMESSAGE_APP_IPAD_PRO_3GEN_11 = auto()
    IMESSAGE_APP_IPAD_PRO_129 = auto()
    IMESSAGE_APP_IPAD_105 = auto()
    IMESSAGE_APP_IPAD_97 = auto()
    APP_APPLE_VISION_PRO = auto()

class AppScreenshotState(EnumAutoName):
    """单个截图的上传状态的状态"""
    AWAITING_UPLOAD = auto()
    UPLOAD_COMPLETE = auto()
    COMPLETE = auto()
    FAILED = auto()

class BundleIdPlatform(EnumAutoName):
    """设备系统类型"""
    IOS = auto()
    MAC_OS = auto()
    UNIVERSAL = auto()


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

    @classmethod
    def from_dict(cls, info_dict: Dict):
        """
        从字典中创建对象
        @param info_dict:
        @return:
        """
        _id = info_dict.get('id')
        _type = info_dict.get('type')
        return cls(_id, _type)
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

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict

        attributes = info_dict.get('attributes', {})
        self.attributes = attributes

        self.added_date = datetime.fromisoformat(attributes.get('addedDate'))  # 添加的日期
        self.name = attributes.get('name')
        self.model = attributes.get('model')  # 具体型号，例如："iPhone 13 Pro Max"
        self.udid = attributes.get('udid')

    @property
    def device_class(self) -> DeviceClass:
        """设备硬件类型"""
        return DeviceClass(self.attributes.get('deviceClass'))

    @property
    def platform(self) -> BundleIdPlatform:
        """设备系统类型"""
        return BundleIdPlatform(self.attributes.get('platform'))

    @property
    def status(self) -> DeviceStatus:
        """设备状态"""
        return DeviceStatus(self.attributes.get('status'))

    @property
    def is_enable(self) -> bool:
        """
        当前device是否有效
        :return:
        """
        return DeviceStatus(self.attributes.get('status')) == DeviceStatus.ENABLED


# 创建设备时的请求参数属性
DeviceCreateReqAttrs = namedtuple('DeviceCreateReqAttrs', 'name, udid, platform',
                                  defaults=[BundleIdPlatform.IOS.value])


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

    def __init__(self, attributes: Dict):
        self.info_dict = attributes
        self.attributes = attributes

        self.name = attributes.get('name')
        self.uuid = attributes.get('uuid')
        self.profile_content = attributes.get('profileContent')
        self.created_date = datetime.fromisoformat(attributes.get('createdDate'))
        self.expiration_date = datetime.fromisoformat(attributes.get('expirationDate'))
        self.profile_type = attributes.get('profileType')

        self._mobile_provision = None

    @property
    def mobile_provision(self) -> MobileProvisionModel:
        if not self._mobile_provision:
            with tempfile.TemporaryDirectory() as temp_dir_path:
                tmp_file_path = Path(temp_dir_path).joinpath('tmp.mobileprovision')
                self.save_content(tmp_file_path)
                self._mobile_provision = MobileProvisionModel(tmp_file_path)
        return self._mobile_provision

    @property
    def platform(self) -> BundleIdPlatform:
        """设备系统类型"""
        return BundleIdPlatform(self.attributes.get('platform'))

    @property
    def is_active(self) -> bool:
        """
        当前device是否有效
        :return:
        """
        return ProfileState(self.attributes.get('profileState')) == ProfileState.ACTIVE

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

    def __init__(self, info_dict: Dict):
        self.info_dict = info_dict
        self.id = info_dict['id']
        self.type = info_dict['type']

        self.attributes = ProfileAttributes(info_dict.get('attributes', {}))
        # self.relationships = ProfileRelationships(info_dict.get('relationships', {}))

    @property
    def name(self):
        return self.attributes.name


BundleIdAttributes = namedtuple('BundleIdAttributes', 'identifier, name, platform, seedId')


class BundleId(DataModel):
    """BundleId信息"""

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict

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

    def __init__(self, attributes: Dict):
        self.info_dict = attributes

        self.name = attributes['name']
        self.display_name = attributes['displayName']
        tmp_platform = attributes.get('platform')  # 可能为None
        self.platform = BundleIdPlatform(tmp_platform) if tmp_platform else None
        self.certificate_type = CertificateType(attributes['certificateType'])
        self.expiration_date = datetime.fromisoformat(attributes.get('expirationDate'))
        self.serial_number = attributes.get('serialNumber', '')
        self.certificate_content = attributes.get('certificateContent', '')


class Certificate(DataModel):
    """cer证书信息"""

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict

        attributes = info_dict.get('attributes', {})
        self.attributes = CertificateAttributes(attributes) if attributes else None

    # def is_valid(self):
    #     """是否有效，即是否在有效期内"""
    #     return self.attributes.expiration_date < datetime.now()

    def save_cer(self, cer_path: Union[Path, str]) -> bool:
        """
        将attributes.certificate_content内容保存为cer文件
        @param cer_path: 保存的cer文件的路径，一般使用.cer做为扩展名
        @return: 是否成功
        """
        if self.attributes.certificate_content:
            tmp_content = base64.b64decode(self.attributes.certificate_content)
            Path(cer_path).write_bytes(tmp_content)
            return True
        else:
            return False


# 创建profile时，请求参数里的Attributes
ProfileCreateReqAttrs = namedtuple('ProfileCreateReqAttrs', 'name, profileType',
                                   defaults=[ProfileType.IOS_APP_DEVELOPMENT.value])


class ProfileCreateReqRelationships:
    """创建profile时，请求参数里的Relationships"""

    def __init__(self, relationships: Dict):
        self.info_dict = relationships
        bundle_id_data = relationships['bundleId'].get('data', {})
        certificates_datas = relationships['certificates'].get('data', [])
        devices_datas = relationships['devices'].get('data', [])

        self.bundleId = DataModel(**bundle_id_data) if bundle_id_data else None
        self.certificates = [DataModel(**tmp_data) for tmp_data in certificates_datas]
        self.devicesType = [DataModel(**tmp_data) for tmp_data in devices_datas]


class CapabilityType(EnumAutoName):
    """bundleId的能力的类型, https://developer.apple.com/documentation/appstoreconnectapi/capabilitytype"""
    ICLOUD = auto()
    IN_APP_PURCHASE = auto()
    GAME_CENTER = auto()
    PUSH_NOTIFICATIONS = auto()
    WALLET = auto()
    INTER_APP_AUDIO = auto()
    MAPS = auto()
    ASSOCIATED_DOMAINS = auto()
    PERSONAL_VPN = auto()
    APP_GROUPS = auto()
    HEALTHKIT = auto()
    HOMEKIT = auto()
    WIRELESS_ACCESSORY_CONFIGURATION = auto()
    APPLE_PAY = auto()
    DATA_PROTECTION = auto()
    SIRIKIT = auto()
    NETWORK_EXTENSIONS = auto()
    MULTIPATH = auto()
    HOT_SPOT = auto()
    NFC_TAG_READING = auto()
    CLASSKIT = auto()
    AUTOFILL_CREDENTIAL_PROVIDER = auto()
    ACCESS_WIFI_INFORMATION = auto()
    NETWORK_CUSTOM_PROTOCOL = auto()
    COREMEDIA_HLS_LOW_LATENCY = auto()
    SYSTEM_EXTENSION_INSTALL = auto()
    USER_MANAGEMENT = auto()
    APPLE_ID_AUTH = auto()


BundleIdCapabilityAttributes = namedtuple('BundleIdCapabilityAttributes',
                                          'capabilityType, settings')


# BundleIdCapabilityAttrSettingItem = namedtuple('BundleIdCapabilityAttrSettingItem',
#                                                'key, options')


class BundleIdCapability(DataModel):
    """BundleId Capability信息"""

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict

        attributes = info_dict.get('attributes', {})
        self.attributes = BundleIdCapabilityAttributes(**attributes) if attributes else None

class AppInfoLocalization(DataModel):
    """
    AppInfoLocalization信息
    https://developer.apple.com/documentation/appstoreconnectapi/appinfolocalization
    """

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict
        self.locale = info_dict.get('attributes', {}).get('locale')

class AppScreenshotSet(DataModel):
    """
    AppScreenshotSet信息
    https://developer.apple.com/documentation/appstoreconnectapi/appscreenshotset
    """

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict
        self.screenshotTypeString = info_dict.get('attributes', {}).get('screenshotDisplayType', '')

class AppScreenshot(DataModel):
    """
    AppScreenshot信息
    https://developer.apple.com/documentation/appstoreconnectapi/appscreenshot
    """

    def __init__(self, info_dict: Dict):
        super().__init__(info_dict['id'], info_dict['type'])
        self.info_dict = info_dict
        self.attributes = info_dict.get('attributes', {})
        state = self.attributes.get('assetDeliveryState', {}).get('state', '')
        self.updateState = AppScreenshotState[state] if state else AppScreenshotState.FAILED