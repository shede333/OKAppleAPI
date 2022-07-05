#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from okappleapi.apple_api_agent import APIAgent, TokenManager
from okappleapi.models import *

key_path = Path('~/Desktop/appleAPIKey/api-OKSW/api_key.json').expanduser()
key_path = Path('~/Desktop/appleAPIKey/api-OKHD/api_key.json').expanduser()
# key_path = Path('~/Desktop/appleAPIKey/api-Malta/api_key.json').expanduser()
key_path = Path('~/Desktop/appleAPIKey/api-OKMC/api_key.json').expanduser()
token_manager = TokenManager.from_json(key_path)


def all_account_device_num():
    root_path = Path('~/Desktop/appleAPIKey').expanduser()
    for dir_path in root_path.iterdir():
        tmp_key_path = dir_path.joinpath('api_key.json')
        if not tmp_key_path.is_file():
            continue

        account_name = dir_path.name
        print(account_name)
        tmp_token_manager = TokenManager.from_json(tmp_key_path)
        tmp_agent = APIAgent(tmp_token_manager)
        device_list = tmp_agent.list_devices()
        print(f"{account_name}, device: {len(device_list)}")


def test_req_list():
    agent = APIAgent(token_manager)

    from pprint import pprint
    from datetime import datetime

    # 获取token
    flag_dot = datetime.now()
    token_manager.ensure_valid()  # 此接口仅用于测试
    print(f"token: {datetime.now() - flag_dot}")

    # 获取certificates列表
    flag_dot = datetime.now()
    cer_list = agent.list_certificates()
    pprint(f'cer_list: {cer_list}')
    for tmp_cer in cer_list:
        print(f'{tmp_cer.id}, {tmp_cer.attributes.__dict__}')
    print(f"cer: {datetime.now() - flag_dot}")

    # 获取bundle_id列表
    flag_dot = datetime.now()
    bundle_id_list = agent.list_bundle_id()
    pprint(f'bundle_id_list: {bundle_id_list}')
    for tmp_id in bundle_id_list:
        print(f'{tmp_id.id}, {tmp_id.attributes}')
    print(f"bundleID: {datetime.now() - flag_dot}")

    # 获取device设备列表
    flag_dot = datetime.now()
    device_list = agent.list_devices()
    for tmp_device in device_list:
        print(f'device info: {type(tmp_device)}, {tmp_device.__dict__}')
    print(f"device: {datetime.now() - flag_dot}, {len(device_list)}")

    # 获取profile列表
    flag_dot = datetime.now()
    profile_list = agent.list_profiles()
    pprint(profile_list)
    print(f"profile: {datetime.now() - flag_dot}")

    for index, tmp_profile in enumerate(profile_list, start=1):
        p_name = tmp_profile.attributes.name
        p_app_id = tmp_profile.attributes.mobile_provision.app_id()
        p_uuid = tmp_profile.attributes.uuid
        p_created_date = tmp_profile.attributes.created_date
        print(f"profile: {index}. {tmp_profile.id}, {p_name}, {p_app_id}, {p_uuid}, {p_created_date}")

    # 创建profile
    attrs = ProfileCreateReqAttrs('test_hello')
    result = agent.create_a_profile(attrs, bundle_id=bundle_id_list[0], devices=device_list,
                                    certificates=cer_list)
    print(f'create profile: {result.id}, {result.attributes.name}')

    # 删除刚创建的profile
    test_delete_profile(result.id)


def test_add_device(name, udid):
    """添加device"""
    agent = APIAgent(token_manager)
    result = agent.register_a_device(DeviceCreateReqAttrs(name, udid, BundleIdPlatform.IOS.value))
    print(f'add device result: {result}')


def test_delete_profile(profile_id):
    """删除一个profile"""
    agent = APIAgent(token_manager)
    print(f'delete profile: {profile_id}')
    agent.delete_a_profile(profile_id)


def test_ok_agent(name, bundle_id_str=None, dst_dir=None):
    """更新一个profile"""
    from okappleapi.ok_agent import OKProfileManager
    ok_agent = OKProfileManager.from_token_manager(token_manager)
    profile_obj = ok_agent.update_profile(name, bundle_id_str=bundle_id_str)
    tmp_profile = profile_obj
    print(
        f"profile: {tmp_profile.id}, {tmp_profile.attributes.name}, {tmp_profile.attributes.uuid}, {tmp_profile.attributes.created_date}")

    if dst_dir and profile_obj:
        dst_dir = Path(dst_dir)
        if dst_dir.is_dir():
            tmp_mp_file_path = Path(dst_dir).joinpath(f'{profile_obj.name}.mobileprovision')
            if tmp_mp_file_path.is_file():
                tmp_mp_file_path.unlink()

            profile_obj.attributes.save_content(tmp_mp_file_path)
            print(f'mp save in: {tmp_mp_file_path}')
        else:
            print(f'not exist: {dst_dir}')


def test_data():
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


def test_add_test_user():
    test_add_device(name='xxx', udid='xxx')
    test_ok_agent('Robot-OKExAppstoreFullOKZGJ-mp',
                  'com.okex.OKExAppstoreFullOKZGJ',
                  '/Users/shaowei/Downloads')


def main():
    # test_data()
    # test_req_list()
    test_add_test_user()


if __name__ == '__main__':
    main()
