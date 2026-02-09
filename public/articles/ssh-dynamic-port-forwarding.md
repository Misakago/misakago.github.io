# SSH 动态端口转发实践

## SSH端口转发模式

```bash
# 1. 动态转发（SOCKS 代理）
ssh -D [本地端口] user@host

# 2. 本地转发（本地 → 远程 → 目标）
ssh -L [本地端口]:[目标主机]:[目标端口] user@跳板机

# 3. 远程转发（远程 ← 本地 ← 目标）
ssh -R [远程端口]:[目标主机]:[目标端口] user@跳板机
```

## 动态端口转发-D的典型场景

客户方对接口对IP有限制，非白名单的IP无法访问接口

解决思路：通过设置SSH动态端口转发实现IP代理，从而本地实现接口调试

## SOCKS5和SOCKS5H的区别

- **SOCKS5**：使用本机的DNS解析再通过代理服务器
- **SOCKS5H**：使用代理服务器的DNS解析

如果发现SOCKS5无法实现代理，请直接尝试SOCKS5H，基本上就能解决，如无特殊需求，推荐默认使用SOCKS5H，避免DNS问题。

相关命令：

```bash
# 使用 SOCKS5H 代理（强制远程 DNS 解析）返回代理服务器 IP
curl --socks5-hostname 127.0.0.1:1080 http://httpbin.org/ip
```

> **注意：** ApiFox和Bruno目前不支持配置SOCKS5H代理，Postman支持。推荐使用Postman进行SOCKS5H代理测试。

![Postman SOCKS5H配置](/images/img_9_MzgyN2QwZDcxZjU.png)

![验证代理IP](/images/img_29_YWZkOWNhYzE5NDk.png)

如果经常要用SSH端口转发，推荐使用termius

![Termius配置](/images/img_31_ZDBiZmUwMDc4MzY.png)

## 万物皆可over ssh

前提是放开TCP转发等SSH配置，启用完整SSH功能。

为保障公网服务器安全，应遵循最小开放原则：

- 仅对外暴露必要端口：**SSH（如 22）** 和 **网站服务端口（如 80/443）**。
- **数据库、缓存等内部服务禁止直接监听公网**，可通过 **SSH 隧道（端口转发）** 安全访问，例如：
  - `ssh -L 5432:localhost:5432 user@server`



- **禁用 SSH 密码登录**，强制使用 **密钥认证**（`PasswordAuthentication no` in `sshd_config`）。
- 为私钥添加 **强密码加密**，并配合 **SSH Agent** 缓存解密后的密钥，兼顾安全与便利：
  - `ssh-keygen -t ed25519 -C "comment"  # 生成带密码的密钥`
  - `eval $(ssh-agent)`
  - `ssh-add ~/.ssh/id_ed25519`

此方案确保：攻击面最小、传输全程加密、身份验证强健。
