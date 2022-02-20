# OK App Store Connect API

仅支持 >=Python3.9

Apple官方API文档：<https://developer.apple.com/documentation/appstoreconnectapi>

同时，也借鉴了 [appstoreconnect库](https://pypi.org/project/appstoreconnect/) 的设计；

## 安装

```shell
pip3 install OKAppleAPI
```

## 功能

profile，即mobileprovision文件；  
device，即设备（iPhone、iPad等），包括设备的name、UDID信息；

* 获取profile列表；
* 删除一个profile；
* 创建一个profile；
* 获取bundleId列表；
* 获取Certificate证书信息列表；
* 获取device列表；
* 注册一个新device

## 使用

```python

from okappleapi.apple_api_agent import APIAgent, TokenManager
from okappleapi.models import *
from pathlib import Path

# key参数 支持key文件内容，或者key文件路径（即*.p8文件路径）
token_manager = TokenManager(issuer_id='xxx', key_id='xxx', key='xxx')
# TokenManager.from_json(key_path)  # 读取配置文件来创建对象

agent = APIAgent(token_manager)

# 获取certificates列表
cer_list = agent.list_certificates()
for tmp_cer in cer_list:
    print(f'{tmp_cer.id}, {tmp_cer.attributes.__dict__}')

# 获取bundle_id列表
bundle_id_list = agent.list_bundle_id()
for tmp_id in bundle_id_list:
    print(f'{tmp_id.id}, {tmp_id.attributes}')

# 获取device设备列表
device_list = agent.list_devices()
for tmp_device in device_list:
    print(tmp_device.__dict__)

# 获取profile列表
profile_list = agent.list_profiles()
for index, tmp_profile in enumerate(profile_list, start=1):
    print(f"profile: {index}. {tmp_profile.id}, {tmp_profile.attributes.name}")

# 创建profile
attrs = ProfileCreateReqAttrs('test_hello')
result = agent.create_a_profile(attrs, bundle_id=bundle_id_list[0], devices=device_list, certificates=cer_list)
print(f'create profile: {result.id}, {result.attributes.name}')

# 删除刚创建的profile
agent.delete_a_profile(result.id)

# 添加一个iOS新设备
device_name = 'xxx'
device_udid = 'xxx'
result = agent.register_a_device(DeviceCreateReqAttrs(device_name, device_udid))
print(result)


# 更新一个profile
from okappleapi.ok_agent import OKProfileManager

profile_name = 'test_hello'
bundle_id_str = 'com.oksw.hellotest'
ok_agent = OKProfileManager.from_token_manager(token_manager)
ok_agent.update_profile(profile_name, bundle_id_str=bundle_id_str)


```

## 待完成

1. 处理所有时间的时区问题；