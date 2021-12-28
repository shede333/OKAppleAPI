# OK App Store Connect API

Apple官方API文档：<https://developer.apple.com/documentation/appstoreconnectapi>

同时，也借鉴了 [appstoreconnect库](https://pypi.org/project/appstoreconnect/) 的设计；

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