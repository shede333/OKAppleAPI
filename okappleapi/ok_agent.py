#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from typing import List

from mobileprovision.util import import_mobileprovision

from .apple_api_agent import APIAgent, TokenManager
from .models import *


class OKProfileError(Exception):
    def __init__(self, error_text):
        super().__init__(error_text)


class OKProfileManager:
    """profile管理器，仅针对iOS系统的设备"""

    def __init__(self, agent: APIAgent):
        if isinstance(agent, TokenManager):
            # 兼容老版本的接口
            agent = APIAgent(agent)
        self.agent = agent

        self._profile_list = []
        self._bundle_id_list = []
        self._device_list = []
        self._cer_list = []

    @classmethod
    def from_token_manager(cls, token_manager: TokenManager):
        agent = APIAgent(token_manager)
        return OKProfileManager(agent)

    @property
    def profile_list(self) -> List[Profile]:
        """
        Profile信息列表
        @return:
        """
        if not self._profile_list:
            self._profile_list = self.agent.list_profiles()
        return self._profile_list.copy()

    def get_profile(self, name: str) -> Profile:
        """
        获取name对的Profile
        @param name: Profile的name
        @return:
        """
        for tmp_profile in self.profile_list:
            if tmp_profile.name == name:
                return tmp_profile

    @property
    def bundle_id_list(self) -> List[BundleId]:
        """
        BundleId信息列表
        @return:
        """
        if not self._bundle_id_list:
            self._bundle_id_list = self.agent.list_bundle_id()

        return self._bundle_id_list.copy()

    def get_bundle_id(self, identifier: str) -> BundleId:
        """
        获取id_str对应的BundleId
        @param identifier: BundleId的identifier, 例如：com.hello.world
        @return:
        """
        for tmp_bundle_id in self.bundle_id_list:
            if tmp_bundle_id.attributes.identifier == identifier:
                return tmp_bundle_id

    @property
    def valid_device_list(self) -> List[Device]:
        """
        有效的iOS设备列表
        @return:
        """
        if not self._device_list:
            self._device_list = self.agent.list_devices()

        result = filter(lambda x: x.is_enable and x.platform == BundleIdPlatform.IOS,
                        self._device_list)
        return list(result)

    def get_cer_list(self, is_dev=True):
        """
        获取cer列表
        @param is_dev: 是否为iOS的dev证书，反之则为iOS的release类型，默认True
        @return:
        """
        if not self._cer_list:
            self._cer_list = self.agent.list_certificates()

        if is_dev:
            supported_types = [CertificateType.DEVELOPMENT, CertificateType.IOS_DEVELOPMENT]
        else:
            supported_types = [CertificateType.DISTRIBUTION, CertificateType.IOS_DISTRIBUTION]
        cer_list = []
        for tmp_cer in self._cer_list:
            platform = tmp_cer.attributes.platform
            is_ios = (not platform) or (platform == BundleIdPlatform.IOS)
            if is_ios and (tmp_cer.attributes.certificate_type in supported_types):
                # 支持iOS设备，且为支持类型
                cer_list.append(tmp_cer)
        return cer_list

    def update_profile(self, name, bundle_id_str=None, is_dev=True, is_save=False) -> Profile:
        """
        更新名为name的Profile，新Profile使用所有的device+cer信息
        @param name: Profile的name
        @param bundle_id_str: 如果Profile不存在，则使用此bundle_id创建一个新的Profile
        @param is_dev: 是否将dev类型的证书，反之则为release类型，默认True
        @param is_save: 是否将新的Profile，保存到系统默认的目录下
        @return:
        """
        print(f'\nupdate profile: {name}')
        tmp_profile = self.get_profile(name)
        if tmp_profile:
            print(f'delete profile: {tmp_profile.name}')
            self.agent.delete_a_profile(tmp_profile.id)
            if not bundle_id_str:
                bundle_id_str = tmp_profile.attributes.mobile_provision.app_id()
        if not bundle_id_str:
            exp_info = f'{name} profile not exist, need bundle_id_str params to create new profile'
            raise OKProfileError(exp_info)

        print(f'create profile: {name}')
        attrs = ProfileCreateReqAttrs(name)
        bundle_id = self.get_bundle_id(bundle_id_str)
        print(f'profile bundle_id: {bundle_id.attributes.identifier}')
        device_list = self.valid_device_list
        print(f'valid devices: {len(device_list)}')
        cer_list = self.get_cer_list(is_dev=is_dev)
        print(f'cer: {len(cer_list)}, is_dev: {is_dev}')
        # 创建新的Profile
        result_profile = self.agent.create_a_profile(attrs=attrs, bundle_id=bundle_id,
                                                     devices=device_list, certificates=cer_list)
        if result_profile:
            if is_save:
                self.save_mobile_provision(result_profile)
            tmp_list = filter(lambda x: x.name != name, self.profile_list)
            tmp_list = list(tmp_list).append(result_profile)
            self._profile_list = tmp_list
        print(f'update profile success: {name}')
        return result_profile

    @staticmethod
    def save_mobile_provision(profile: Profile):
        """
        将profile保存到系统的默认目录下，同时删除name的mobile_provision
        @param profile: Profile对象
        @return:
        """
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir_path:
            tmp_file_path = Path(temp_dir_path).joinpath('tmp.mobileprovision')
            profile.attributes.save_content(tmp_file_path)

            import_mobileprovision(tmp_file_path)


def main():
    pass


if __name__ == '__main__':
    main()
