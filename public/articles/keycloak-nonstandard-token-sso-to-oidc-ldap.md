# Keycloak 非标准 Token SSO 向 OIDC/LDAP 登录实验

## 实验准备

### [Keycloak](https://github.com/keycloak/keycloak)（IdP）

Keycloak 可作为支持 SAML 和 OIDC 的身份提供商（IdP）。若客户方可以提供标准的OIDC SSO则可以不用Keycloak，直接对接即可。

参考教程：

1. [Setup OpenID Connect with Keycloak: A Step-by-Step Guide](https://mydeveloperplanet.com/2025/05/28/setup-openid-connect-with-keycloak-a-step-by-step-guide/)
2. [Using LDAP User Federation](https://www.olvid.io/keycloak/ldap-federation/)
3. [Create a Custom Authentication Provider in Keycloak](https://medium.com/the-experts-tech-talks/create-a-custom-authentication-provider-in-keycloak-0554d1f7136b)
4. https://www.keycloak.org/docs/latest/

### [LLDAP](https://github.com/lldap/lldap)（LDAP）

非必选，主要看客户方是否启用了LDAP并是否愿意授权给keycloak，如果能启用LDAP，则省去用户创建和用户和组织架构管理相关逻辑。本实验中使用lldap模拟客户方LDAP。LDAP也是老古董了，但是不妨碍其通用性强，标准统一。这里推荐用LLDAP，配置都封装好了，用来简单实验很合适。

参考教程：

1. [我花了一个五一终于搞懂了OpenLDAP](https://segmentfault.com/a/1190000014683418)

### [Postman](https://www.postman.com/) (OIDC Client)

作为OIDC Client使用，模拟登录行为。

### Token SSO Generator（模拟客户方Token SSO生成）

> ⚠️ **安全说明：** 此部分涉及客户方内部 Token 生成逻辑，包含敏感的加密算法和密钥生成方式，已省略。

在实际部署时，需要与客户方确认以下信息：
- Token 加密算法（如 AES-128-CBC）
- 密钥生成规则
- Token 格式和参数
- 验证端点 URL

以下是 Keycloak SPI 端的解密和验证逻辑（需根据客户方实际规则调整）：### docker-compose.yml

```yaml
version: "3.9"

volumes:
  lldap_data:
    driver: local

services:
  lldap:
    image: lldap/lldap:stable
    container_name: lldap
    ports:
      - "3890:3890"
      - "17170:17170"
    volumes:
      - lldap_data:/data
    environment:
      - UID=501
      - GID=20
      - TZ=Asia/Shanghai
      # 生产环境请使用强密码并使用密钥管理工具
      - LLDAP_JWT_SECRET=your-jwt-secret-here-change-in-production
      - LLDAP_KEY_SEED=your-key-seed-here-change-in-production
      - LLDAP_LDAP_BASE_DN=dc=example,dc=com
      - LLDAP_LDAP_USER_PASS=your-secure-password-here
    labels:
      - dev.orbstack.domains=lldap.orb.local
    restart: unless-stopped

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: keycloak
    ports:
      - "8080:8080"
    environment:
      - KC_BOOTSTRAP_ADMIN_USERNAME=admin
      # 生产环境请使用强密码
      - KC_BOOTSTRAP_ADMIN_PASSWORD=your-admin-password-here
      - KC_HOSTNAME=keycloak.orb.local
      - KC_PROXY_HEADERS=xforwarded
      - KC_HTTP_ENABLED=true
      - KC_HOSTNAME_STRICT=false
      - KC_HOSTNAME_STRICT_HTTPS=false
    labels:
      - dev.orbstack.domains=keycloak.orb.local
    command: start-dev
    depends_on:
      - lldap
    restart: unless-stopped
```

## 实验流程

### Postman 作为 OIDC Client 通过 Keycloak（OIDC Server）完成授权码流程模拟登录

#### Keycloak创建测试用户

**创建新的realm（域）**

![创建realm](/images/img_13_NmRlZGU2YTMwZDJ.png)

**在test-realm中创建测试用户**

![创建用户](/images/img_18_ODk1YTdmYmRhNjY.png)

![用户详情](/images/img_1_M2E1NzBjMzFlNTE.png)

#### Keycloak将Postman注册为OIDC Client

**Part 1：Postman 中的 OAuth 2.0 配置项目及作用**

| Postman 配置字段      | 字段英文名称                 | 作用说明                                                     | 在 OAuth 2.0 / OIDC 流程中的位置          | 是否必须         |
| --------------------- | ---------------------------- | ------------------------------------------------------------ | ----------------------------------------- | ---------------- |
| Auth URL              | Authorization Endpoint       | 用户登录和授权的入口地址。Postman 会将浏览器重定向到此 URL 让用户完成登录和同意。 | 授权请求第一步（浏览器跳转）              | 是               |
| Access Token URL      | Token Endpoint               | 用授权码（code）或其他方式换取 access_token、id_token、refresh_token 的端点。 | 后端 POST 请求（code 交换 token）         | 是               |
| Callback URL          | Redirect URI                 | 授权完成后，Keycloak 将浏览器重定向回的地址，用于携带授权码（code）。Postman 推荐使用其内置回调地址。 | 授权服务器 → 浏览器 → Postman 拦截 code   | 是               |
| Client ID             | Client ID                    | 在 Keycloak 中注册客户端时生成的唯一标识符，用于标识你的"应用"（这里是 Postman 测试）。 | 所有请求中都需要携带                      | 是               |
| Client Secret         | Client Secret                | 机密客户端（Confidential Client）的密钥，用于在 Token Endpoint 认证客户端身份。公共客户端留空。 | Token Endpoint 请求时的客户端认证（可选） | 机密客户端时是   |
| Scope                 | Scope                        | 请求的权限范围。OIDC 常用 `openid profile email`（必须包含 `openid` 才能返回 id_token）。 | 授权请求和 token 请求中携带               | 推荐填写         |
| State                 | State                        | 防 CSRF 攻击的随机字符串，授权响应会原样返回，用于验证请求一致性。 | 授权请求 → 响应验证                       | 推荐填写         |
| Client Authentication | Client Authentication Method | 客户端密钥的发送方式。通常选择 "Send as Basic Auth header" 或 "Send client credentials in body"。 | Token Endpoint 请求时使用                 | 有 Secret 时必选 |

**Part 2：Postman 配置项与 Keycloak 配置的对应关系**

| Postman 配置字段      | Keycloak 中对应的配置位置                                    | 如何获取 / 设置                                              |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Auth URL              | Realm → Clients → 选中客户端 → "Settings" → Authorization endpoint（或从发现文档获取） | 最方便方式：访问 `https://keycloak.orb.local/realms/{realm-name}/.well-known/openid-configuration`，复制里面的 `"authorization_endpoint"` |
| Access Token URL      | Realm → Clients → 选中客户端 → "Settings" → Token endpoint（或从发现文档获取） | 同上，发现文档中的 `"token_endpoint"`                        |
| Callback URL          | Realm → Clients → 选中客户端 → "Settings" → Valid Redirect URIs | 必须在此处添加 Postman 支持的回调地址： `https://oauth.pstmn.io/v1/browser-callback`（推荐，使用内置浏览器） `https://oauth.pstmn.io/v1/callback` |
| Client ID             | Realm → Clients → 选中客户端 → "Client ID"                   | 创建客户端时自行填写，例如 `postman-client`                  |
| Client Secret         | Realm → Clients → 选中客户端 → "Credentials" 标签（仅当 Client authentication 为 ON 时） | 开启客户端认证后，Keycloak 会自动生成 Secret，或手动再生     |
| Scope                 | Realm → Clients → 选中客户端 → "Client Scopes" 或直接在 Postman 中填写 | OIDC 必须包含 `openid`；其他如 `profile`、`email` 可在 Client Scopes 中配置默认值 |
| State                 | 无需在 Keycloak 配置，由 Postman 自动生成或手动填写          | Keycloak 会原样返回，Postman 用于校验                        |
| Client Authentication | Realm → Clients → 选中客户端 → "Advanced" → Access Type（Confidential/Public） | Confidential（机密）客户端需要 Secret 并选择合适的认证方式；Public（公共）客户端无需 Secret |

**Part 3：配置示例**

![Postman配置1](/images/img_32_ZDYwNWFkMWU5YWI.png)

![Postman配置2](/images/img_8_MWYzYmE0ZThiNmQ.png)

#### Postman发起OIDC认证

**在Postman中点击"Get New Access Token"按钮，输入测试用户凭证**

![获取token](/images/img_17_ODgzYmQyNTEyZDI.png)

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciO...",
  "id_token": "eyJhbGciOiRS...",
  "scope": "openid profile email",
  "session_state": "7c6b4fe8-c60c-5de7-d146-22a42a19004e",
  "not-before-policy": 0
}
```

**重要字段详细介绍**

| 字段名                 | 值示例（截取）                       | 说明                                                         |
| ---------------------- | ------------------------------------ | ------------------------------------------------------------ |
| **access_token**       | eyJhbGciOiJSUzI1NiIs...              | 最核心的访问令牌，用于调用受保护的 API。Header 中携带 `Authorization: Bearer <access_token>`。 |
| **token_type**         | Bearer                               | 令牌类型，几乎总是 "Bearer"。                                |
| **expires_in**         | 300                                  | access_token 的剩余有效时间（秒）。这里是 5 分钟（300秒）。  |
| **refresh_token**      | eyJhbGciOiJIUzUxMiIs...              | 刷新令牌，用于在 access_token 过期后获取新的 access_token（无需重新登录）。 |
| **refresh_expires_in** | 1800                                 | refresh_token 的剩余有效时间（秒）。这里是 30 分钟。         |
| **id_token**           | eyJhbGciOiJSUzI1NiIs...              | OpenID Connect 专有的身份令牌（JWT），包含用户身份信息（如 sub、name、email 等）。 |
| **scope**              | openid profile email                 | 本次授权获得的权限范围。包含 `openid` 表示是 OIDC 流程。     |
| **session_state**      | 7c6b4fe8-c60c-5de7-d146-22a42a19004e | Keycloak 会话 ID，用于单点注销（Single Sign-Out）和会话状态检查。 |
| **not-before-policy**  | 0                                    | 用户账户的"not-before"策略时间戳，0 表示无限制。             |

**额外说明（从 JWT 内容可直接看到的关键信息）**

- **access_token 已解码 payload 中的重要 claim**：
  - `sub`: "2ad9d2e3-e495-473e-b3e7-f1705a4df9f7" → 用户唯一 ID
  - `preferred_username`: "testuser" → 登录用户名
  - `email`: "testuser@example.com"
  - `name`: "Test User"
  - `realm_access.roles`: 包含默认角色和 offline_access
  - 过期时间 `exp`: 1767496854（Unix 时间戳，可转换为 2026-01-04 约 5 分钟后过期）
- **id_token** 主要用于客户端验证用户身份（可直接在 https://jwt.io 解码查看）。

**端到端功能测试**

1. **Userinfo 端点（验证 ID Token）**
   - 方法：`GET`
   - URL：`https://keycloak.orb.local/realms/test-realm/protocol/openid-connect/userinfo`
   - Auth：`Inherit auth from parent`（使用已获取的 access token）
   - 预期：返回用户信息 JSON，如 `{"sub": "...", "email": "..."}`

2. **令牌内省（Introspection）**
   - 方法：`POST`
   - URL：`https://keycloak.orb.local/realms/test-realm/protocol/openid-connect/token/introspect`
   - Body（x-www-form-urlencoded）：
     - `client_id: postman-client`
     - `client_secret: <secret>（如有）`
     - `token: <your-access-token>`
   - 预期：`{"active": true, ...}`

3. **刷新令牌（Refresh Token）**
   - 方法：`POST`
   - URL：Token endpoint（如 `/token`）
   - Body（x-www-form-urlencoded）：
     - `grant_type: refresh_token`
     - `refresh_token: <your-refresh-token>`
     - `client_id: postman-client`
     - `client_secret: <secret>（如有）`
   - 预期：返回新 `access_token`

4. **注销（Logout）**
   - 方法：`GET`
   - URL：`https://keycloak.orb.local/realms/test-realm/protocol/openid-connect/logout?id_token_hint=<your-id-token>&post_logout_redirect_uri=https://oauth.pstmn.io/v1/callback`
   - 预期：会话终止，重定向到回调页

### Token SSO Generator（模拟客户方Token SSO生成）

> ⚠️ **安全说明：** 此部分涉及客户方内部 Token 生成逻辑，包含敏感的加密算法和密钥生成方式，已省略。

在实际部署时，需要与客户方确认以下信息：
- Token 加密算法（如 AES-128-CBC）
- 密钥生成规则
- Token 格式和参数
- 验证端点 URL

以下是 Keycloak SPI 端的解密和验证逻辑（需根据客户方实际规则调整）：
