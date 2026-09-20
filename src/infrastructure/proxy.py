"""代理环境变量应用：控制 TqSdk（websockets）与 httpx 的代理行为。

websockets 每次建立连接（含重连）时通过 urllib.request.getproxies() 解析代理：
环境变量优先，无环境变量时回退读取 macOS/Windows 系统代理（SOCKS 系统代理会
导致 TqSdk 连接失败，除非安装 python-socks）。三种模式：

- 直连（proxy_url 为空，默认）：NO_PROXY='*' 强制全部直连，同时屏蔽系统代理；
- 系统代理（proxy_url == SYSTEM_PROXY）：清除我们的干预，让库回退读取系统代理
  配置（含系统自带的排除列表）；
- 自定义代理：WSS_PROXY 指向代理地址（websockets 对 wss:// 的最高优先级键），
  NO_PROXY 排除 iTrader 服务器 host，避免内网 httpx 请求被代理劫持。
"""
import os
from urllib.parse import urlparse

# proxy_url 的特殊值：跟随系统代理设置
SYSTEM_PROXY = "system"


def server_host(server_url: str) -> str:
    """从服务器地址提取 host（兼容无 scheme 的写法）。"""
    url = server_url.strip()
    if "://" not in url:
        url = "http://" + url
    return urlparse(url).hostname or ""


def apply_proxy_environment(proxy_url: str, bypass_hosts: list[str] = []) -> None:
    """按配置写入代理相关环境变量，对后续新建的连接生效。"""
    proxy_url = (proxy_url or "").strip()
    if proxy_url == SYSTEM_PROXY:
        # 清掉全部干预，getproxies() 回退读取系统代理配置
        for key in ("NO_PROXY", "no_proxy", "WSS_PROXY", "wss_proxy"):
            os.environ.pop(key, None)
        return
    if not proxy_url:
        # '*' 是 stdlib/websockets 明确支持的「全部绕过」语义
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"
        os.environ.pop("WSS_PROXY", None)
        os.environ.pop("wss_proxy", None)
        return
    os.environ["WSS_PROXY"] = proxy_url
    os.environ["wss_proxy"] = proxy_url
    hosts = [h for h in bypass_hosts if h]
    joined = ",".join(hosts)
    os.environ["NO_PROXY"] = joined
    os.environ["no_proxy"] = joined
