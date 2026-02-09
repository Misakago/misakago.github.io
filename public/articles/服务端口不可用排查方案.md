# 服务端口不可用排查方案

## 核心认知

Docker 容器能公网访问不等于宿主机进程能公网访问，因为 Docker 绕过 UFW，而宿主机服务受 UFW 和 iptables INPUT 链控制。

## 排查 checklist

### 1. 服务是否监听正确地址？

```bash
ss -tuln | grep :8001
```

必须是 `0.0.0.0:8001` 或绑定公网 IP。

### 2. UFW 是否放行端口？

```bash
ufw status verbose
```

若 UFW 启用，必须显式放行：

```bash
ufw allow 8001/tcp
```

### 3. iptables 是否拦截？

```bash
iptables -L INPUT -n
```

若策略为 DROP，需确保有 ACCEPT 规则（UFW 管理时通常无需手动添加）。

### 4. 云平台安全组 / 网络 ACL

登录云服务商控制台，确认入方向规则允许相应端口的 TCP 连接。

### 5. 公网 IP 是否直连本机？

```bash
ip addr show
```

检查服务器是否直接绑定公网 IP。若无公网 IP，说明公网 IP 由上游 NAT 设备管理，需在该设备上配置端口转发到内网 IP。

## 经验教训

- 不要假设"容器通 = 宿主机通"——两者网络路径和防火墙处理机制不同。
- UFW 是常见隐形拦截点：默认策略 DROP 且未放行端口会导致外部无法连接。
- 排查顺序应为：监听状态 → 本地防火墙（UFW/iptables）→ 云安全组 → 网络拓扑（NAT/路由）。

## 关键原则

**网络可达性 = 监听 + 防火墙放行 + 路由可达，三者缺一不可。**

## 网络分层排查流程图

![网络排查流程](/images/img_22_Y2E0NDU2ZjRmYzM.jpg)

## 参考资源

- [Docker and UFW best practices - StackOverflow](https://stackoverflow.com/questions/30383845/what-is-the-best-practice-of-docker-ufw-under-ubuntu)
