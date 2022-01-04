#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from apple_api_agent import APIAgent, TokenManager
from models import *
from pathlib import Path

key_path = Path('~/Desktop/appleAPIKey/api-sw/api_key.json').expanduser()
token_manager = TokenManager.from_json(key_path)


def test_req_list():
    agent = APIAgent(token_manager)

    from pprint import pprint
    from datetime import datetime

    flag_dot = datetime.now()
    token_manager.ensure_valid()
    print(f"token: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    cer_list = agent.list_certificates()
    pprint(f'cer_list: {cer_list}')
    for tmp_cer in cer_list:
        print(f'{tmp_cer.id}, {tmp_cer.attributes.__dict__}')
    print(f"cer: {datetime.now() - flag_dot}")
    return

    flag_dot = datetime.now()
    bundle_id_list = agent.list_bundle_id()
    pprint(f'bundle_id_list: {bundle_id_list}')
    for tmp_id in bundle_id_list:
        print(f'{tmp_id.id}, {tmp_id.attributes}')

    print(f"bundleID: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    device_list = agent.list_devices()
    # pprint(f'device_list: {device_list}')
    for tmp_device in device_list:
        print(tmp_device.__dict__)
    print(f"device: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    profile_list = agent.list_profiles()
    pprint(profile_list)
    print(f"profile: {datetime.now() - flag_dot}")

    for index, tmp_profile in enumerate(profile_list, start=1):
        print(f"profile: {index}. {tmp_profile.id}, {tmp_profile.attributes.name}")

    # 创建profile
    attrs = ProfileCreateReqAttrs('test_hello')
    result = agent.create_a_profile(attrs, bundle_id=bundle_id_list[0], devices=device_list,
                                    certificates=cer_list)
    print(f'create profile: {result.id}, {result.attributes.name}')

    # 删除刚创建的
    test_delete_profile(result.id)


def test_add_device():
    agent = APIAgent(token_manager)

    name = ''
    udid = ''
    result = agent.register_a_device(DeviceCreateReqAttrs(name, udid, BundleIdPlatform.IOS.value))
    print(result)


def test_delete_profile(profile_id):
    agent = APIAgent(token_manager)
    print(f'delete profile: {profile_id}')
    agent.delete_a_profile(profile_id)


def test_ok_agent():
    from ok_agent import OKProfileManager
    ok_agent = OKProfileManager(token_manager)
    ok_agent.update_profile('test_hello', 'com.okex.OKExAppstoreFullOKSW')
    # ok_agent.update_profile('OKCoinAppstoreOKSW-mp', 'com.okcoin.OKCoinAppstoreOKSW')
    # ok_agent.update_profile('OKExAppstoreFullOKSW-mp', 'com.okex.OKExAppstoreFullOKSW')


def main():
    print(DeviceStatus.ENABLED.value == 'ENABLED')
    print(DeviceStatus.ENABLED == DeviceStatus('ENABLED'))
    print(DeviceStatus.ENABLED, type(DeviceStatus.ENABLED))
    print(DeviceStatus('ENABLED'), type(DeviceStatus('ENABLED')))
    # print(DeviceStatus.ENABLED == DeviceStatus('ENABLED--'))
    model = DataModel('tt-id', DataType.devices.value)
    print(model.req_params())

    supported_types = [CertificateType.DEVELOPMENT, CertificateType.IOS_DEVELOPMENT]
    print(CertificateType.DEVELOPMENT in supported_types)
    print(CertificateType.IOS_DEVELOPMENT in supported_types)
    print(CertificateType.PASS_TYPE_ID in supported_types)

    # test_req_list()
    # test_add_device()
    test_ok_agent()


if __name__ == '__main__':
    main()
