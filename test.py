#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from apple_api_agent import APIAgent, TokenManager
from models import *

token_manager = TokenManager(issuer_id='a6c36ebd-c946-47c0-88cb-1ed1ce336fc4',
                             key_id='5DHQAH5MZ5',
                             key='/Users/shaowei/Desktop/fastlane/5DHQAH5MZ5/AuthKey_5DHQAH5MZ5.p8')


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
    print(f"cer: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    bundle_id_list = agent.list_bundle_id()
    pprint(f'bundle_id_list: {bundle_id_list}')
    print(f"bundleID: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    device_list = agent.list_devices()
    pprint(f'device_list: {device_list}')
    print(f"device: {datetime.now() - flag_dot}")

    flag_dot = datetime.now()
    pprint(agent.list_profiles())
    print(f"profile: {datetime.now() - flag_dot}")

    # 创建profile
    attrs = ProfileCreateReqAttrs('test_hello')

    result = agent.create_a_profile(attrs, bundle_id=bundle_id_list[0], devices=device_list,
                                    certificates=cer_list)
    print(f'create profile: {result}')


def main():
    print(DeviceStatus.ENABLED.value == 'ENABLED')
    model = DataModel('tt-id', DataType.devices.value)
    print(model.req_params())

    test_req_list()


if __name__ == '__main__':
    main()
