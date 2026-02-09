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

```javascript
// legacy.js
import express from 'express';
import crypto from 'crypto';
import dayjs from 'dayjs';

const app = express();
const port = 3000;

// 固定 IV（与 Java 端一致）
const AES_IV = '***REDACTED***';

// 获取 AES Key（当天 YYYYMMDD 重复两次）
function getAESKey() {
  const now = dayjs();
  const formattedDate = now.format('YYYYMMDD');
  return formattedDate + formattedDate; // 如 2026010420260104
}

// AES-128-CBC 加密（与 Java 端保持一致）
function aesEncrypt(str, key, iv) {
  const cipher = crypto.createCipheriv('aes-128-cbc', Buffer.from(key, 'utf8'), Buffer.from(iv, 'utf8'));
  let encrypted = cipher.update(str, 'utf8', 'buffer');
  encrypted = Buffer.concat([encrypted, cipher.final()]);
  return encrypted.toString('base64');
}

// 生成 SSO token
function generateTokenSSO(userid) {
  const user4aId = userid;
  const moduleAddress = 'legacy-module';
  const sendTime = new Date().toISOString(); // 如 2026-01-04T12:34:56.789Z
  const plainStr = [userid, user4aId, moduleAddress, sendTime].join('$');

  const aesKey = getAESKey();
  return aesEncrypt(plainStr, aesKey, AES_IV);
}

// ========================
// 路由 1: 实际 SSO 登录入口
// ========================
app.get('/login-sso', (req, res) => {
  const userid = req.query.userid || 'testuser';
  const ssoToken = generateTokenSSO(userid);

  // Keycloak 标准授权端点
  const keycloakAuthUrl = new URL('https://keycloak.orb.local/realms/experiment/protocol/openid-connect/auth');

  // 必须配置的 OIDC 参数（请根据你的实际 client 调整）
  keycloakAuthUrl.searchParams.append('client_id', 'legacy-module');     // 在 Keycloak 中创建的 client_id
  keycloakAuthUrl.searchParams.append('redirect_uri', 'http://localhost:9000/sso-callback'); // 你的应用回调地址（可随意，后面可以不处理）
  keycloakAuthUrl.searchParams.append('response_type', 'code');
  keycloakAuthUrl.searchParams.append('scope', 'openid profile email');

  // 把加密后的 token 作为自定义参数传给你的 Authenticator
  keycloakAuthUrl.searchParams.append('paramString', ssoToken);

  // 可选：添加 state 防止 CSRF（推荐生产环境使用）
  // const state = crypto.randomBytes(16).toString('hex');
  // keycloakAuthUrl.searchParams.append('state', state);

  console.log(`Redirecting user "${userid}" to Keycloak with SSO token`);
  console.log(`Full URL: ${keycloakAuthUrl.toString()}`);

  res.redirect(keycloakAuthUrl.toString());
});

// ========================
// 路由 2: 调试用 - 只显示 token，不跳转
// ========================
app.get('/debug-token', (req, res) => {
  const userid = req.query.userid || 'testuser';
  const ssoToken = generateTokenSSO(userid);

  const debugUrl = new URL('https://keycloak.orb.local/realms/experiment/protocol/openid-connect/auth');
  debugUrl.searchParams.append('client_id', 'legacy-module');
  debugUrl.searchParams.append('redirect_uri', 'http://localhost:9000/sso-callback');
  debugUrl.searchParams.append('response_type', 'code');
  debugUrl.searchParams.append('scope', 'openid');
  debugUrl.searchParams.append('paramString', ssoToken);

  res.type('html');
  res.send(`
    <h2>SSO Token Debug</h2>
    <p><strong>UserID:</strong> ${userid}</p>
    <p><strong>Generated Token:</strong><br><code>${ssoToken}</code></p>
    <p><strong>Full Redirect URL:</strong><br>
       <a href="${debugUrl.toString()}" target="_blank">${debugUrl.toString()}</a>
    </p>
    <hr>
    <p><a href="/login-sso?userid=${userid}">→ Click here to perform real SSO login</a></p>
  `);
});

// ========================
// 简单首页
// ========================
app.get('/', (req, res) => {
  res.type('html');
  res.send(`
    <h1>Legacy SSO Token Generator</h1>
    <ul>
      <li><a href="/login-sso?userid=testuser">Login as testuser</a></li>
      <li><a href="/login-sso?userid=admin">Login as admin</a></li>
      <li><a href="/debug-token?userid=testuser">Debug token (no redirect)</a></li>
    </ul>
  `);
});

app.listen(port, () => {
  console.log(`SSO Simulation Server running at http://localhost:${port}`);
  console.log(`→ Try: http://localhost:${port}/login-sso?userid=testuser`);
});
```

### docker-compose.yml

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

![创建realm](images/img_13_NmRlZGU2YTMwZDJ.png)

**在test-realm中创建测试用户**

![创建用户](images/img_18_ODk1YTdmYmRhNjY.png)

![用户详情](images/img_1_M2E1NzBjMzFlNTE.png)

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

![Postman配置1](images/img_32_ZDYwNWFkMWU5YWI.png)

![Postman配置2](images/img_8_MWYzYmE0ZThiNmQ.png)

#### Postman发起OIDC认证

**在Postman中点击"Get New Access Token"按钮，输入测试用户凭证**

![获取token](images/img_17_ODgzYmQyNTEyZDI.png)

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

### Token SSO Generator+Keycloak 开启 SPI 扩展认证

#### 创建SPI项目

```bash
keycloak-sso-provider/
├── pom.xml                                          # Maven项目配置文件
│   ├── 定义项目坐标 (groupId/artifactId/version)
│   ├── Keycloak 26.0.7 依赖配置
│   └── Maven编译器插件配置 (Java 11)
│
├── src/
│   └── main/
│       ├── java/
│       │   └── com/example/keycloak/sso/
│       │       ├── SSOTokenAuthenticator.java       # 核心认证器实现类
│       │       │   └── 从URL参数解密token，验证时间戳，查找/创建用户
│       │       │
│       │       ├── SSOTokenAuthenticatorFactory.java # 认证器工厂类
│       │       │   └── 提供Keycloak SPI接口实现，配置认证器属性
│       │       │
│       │       └── TokenDecryptor.java              # Token解密工具类
│       │           ├── 使用AES-128-CBC解密Base64编码的token
│       │           ├── 密钥基于当前日期生成 (yyyyMMdd+yyyyMMdd)
│       │           └── 解析格式: userid$user4aId$moduleAddress$sendTime
│       │
│       └── resources/
│           └── META-INF/services/
│               └── org.keycloak.authentication.AuthenticatorFactory
│                   └── SPI服务注册文件 (指向SSOTokenAuthenticatorFactory)
```

**SSOTokenAuthenticator.java**

```java
package com.example.keycloak.sso;

import org.jboss.logging.Logger;
import org.keycloak.authentication.AuthenticationFlowContext;
import org.keycloak.authentication.AuthenticationFlowError;
import org.keycloak.authentication.Authenticator;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;

import jakarta.ws.rs.core.MultivaluedMap;
import java.time.Duration;
import java.time.Instant;

public class SSOTokenAuthenticator implements Authenticator {

    private static final Logger logger = Logger.getLogger(SSOTokenAuthenticator.class);
    private static final String PARAM_NAME = "paramString";
    private static final long TOKEN_VALIDITY_MINUTES = 5;

    @Override
    public void authenticate(AuthenticationFlowContext context) {
        // 从查询参数获取加密 token
        MultivaluedMap<String, String> queryParams = context.getHttpRequest().getUri().getQueryParameters();
        String encryptedToken = queryParams.getFirst(PARAM_NAME);

        if (encryptedToken == null || encryptedToken.isEmpty()) {
            logger.warn("Missing paramString in request");
            context.attempted();
            return;
        }

        try {
            // 解密 token
            String decryptedStr = TokenDecryptor.decrypt(encryptedToken);
            logger.infof("Decrypted token: %s", decryptedStr);

            // 解析 token 数据
            TokenDecryptor.TokenData tokenData = TokenDecryptor.parseToken(decryptedStr);

            // 验证 token 时间戳(防止重放攻击)
            if (!isTokenValid(tokenData.getSendTime())) {
                logger.warnf("Token expired or invalid timestamp: %s", tokenData.getSendTime());
                context.failure(AuthenticationFlowError.EXPIRED_CODE);
                return;
            }

            // 查找或创建用户
            UserModel user = findOrCreateUser(context, tokenData);

            if (user == null) {
                logger.errorf("Failed to find or create user: %s", tokenData.getUserid());
                context.failure(AuthenticationFlowError.INVALID_USER);
                return;
            }

            // 设置用户并标记认证成功
            context.setUser(user);
            context.success();

            logger.infof("User %s authenticated successfully via SSO token", tokenData.getUserid());

        } catch (Exception e) {
            logger.errorf(e, "Failed to process SSO token");
            context.failure(AuthenticationFlowError.INVALID_CREDENTIALS);
        }
    }

    /**
     * 验证 token 时间戳
     */
    private boolean isTokenValid(String sendTimeStr) {
        try {
            Instant sendTime = Instant.parse(sendTimeStr);
            Instant now = Instant.now();
            long minutesDiff = Duration.between(sendTime, now).toMinutes();

            return Math.abs(minutesDiff) <= TOKEN_VALIDITY_MINUTES;
        } catch (Exception e) {
            logger.errorf(e, "Failed to parse timestamp: %s", sendTimeStr);
            return false;
        }
    }

    /**
     * 查找或创建用户
     */
    private UserModel findOrCreateUser(AuthenticationFlowContext context, TokenDecryptor.TokenData tokenData) {
        KeycloakSession session = context.getSession();
        RealmModel realm = context.getRealm();
        String username = tokenData.getUserid();

        // 先尝试查找现有用户
        UserModel user = session.users().getUserByUsername(realm, username);

        if (user == null) {
            // 用户不存在,创建新用户
            logger.infof("Creating new user: %s", username);
            user = session.users().addUser(realm, username);
            user.setEnabled(true);

            // 设置用户属性
            user.setSingleAttribute("user4aId", tokenData.getUser4aId());
            user.setSingleAttribute("moduleAddress", tokenData.getModuleAddress());
            user.setSingleAttribute("sso_created", "true");
        }

        return user;
    }

    @Override
    public void action(AuthenticationFlowContext context) {
        // 不需要处理表单提交
    }

    @Override
    public boolean requiresUser() {
        return false;
    }

    @Override
    public boolean configuredFor(KeycloakSession session, RealmModel realm, UserModel user) {
        return true;
    }

    @Override
    public void setRequiredActions(KeycloakSession session, RealmModel realm, UserModel user) {
        // 无需设置必需操作
    }

    @Override
    public void close() {
        // 清理资源(如果需要)
    }
}
```

**SSOTokenAuthenticatorFactory.java**

```java
package com.example.keycloak.sso;

import org.keycloak.Config;
import org.keycloak.authentication.Authenticator;
import org.keycloak.authentication.AuthenticatorFactory;
import org.keycloak.models.AuthenticationExecutionModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.provider.ProviderConfigProperty;

import java.util.Collections;
import java.util.List;

public class SSOTokenAuthenticatorFactory implements AuthenticatorFactory {

    public static final String PROVIDER_ID = "sso-token-authenticator";

    @Override
    public String getDisplayType() {
        return "Legacy SSO Token Authenticator";
    }

    @Override
    public String getReferenceCategory() {
        return "sso-token";
    }

    @Override
    public boolean isConfigurable() {
        return false;
    }

    @Override
    public AuthenticationExecutionModel.Requirement[] getRequirementChoices() {
        return new AuthenticationExecutionModel.Requirement[]{
            AuthenticationExecutionModel.Requirement.REQUIRED,
            AuthenticationExecutionModel.Requirement.ALTERNATIVE,
            AuthenticationExecutionModel.Requirement.DISABLED
        };
    }

    @Override
    public boolean isUserSetupAllowed() {
        return false;
    }

    @Override
    public String getHelpText() {
        return "Validates encrypted SSO tokens from legacy systems and auto-creates users.";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return Collections.emptyList();
    }

    @Override
    public Authenticator create(KeycloakSession session) {
        return new SSOTokenAuthenticator();
    }

    @Override
    public void init(Config.Scope config) {
        // 初始化配置
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
        // 后置初始化
    }

    @Override
    public void close() {
        // 清理资源
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }
}
```

**TokenDecryptor.java**

```java
package com.example.keycloak.sso;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Base64;

public class TokenDecryptor {

    private static final String AES_IV = "***REDACTED***";
    private static final String ALGORITHM = "AES/CBC/PKCS5Padding";
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * 获取 AES Key (基于当前日期)
     */
    private static String getAESKey() {
        String formattedDate = LocalDate.now().format(DATE_FORMATTER);
        return formattedDate + formattedDate;
    }

    /**
     * AES 解密
     */
    public static String decrypt(String encryptedBase64) throws Exception {
        String aesKey = getAESKey();

        byte[] encrypted = Base64.getDecoder().decode(encryptedBase64);
        byte[] keyBytes = aesKey.getBytes(StandardCharsets.UTF_8);
        byte[] ivBytes = AES_IV.getBytes(StandardCharsets.UTF_8);

        SecretKeySpec secretKey = new SecretKeySpec(keyBytes, "AES");
        IvParameterSpec iv = new IvParameterSpec(ivBytes);

        Cipher cipher = Cipher.getInstance(ALGORITHM);
        cipher.init(Cipher.DECRYPT_MODE, secretKey, iv);

        byte[] decrypted = cipher.doFinal(encrypted);
        return new String(decrypted, StandardCharsets.UTF_8);
    }

    /**
     * 解析 Token 内容
     */
    public static TokenData parseToken(String decryptedStr) {
        String[] parts = decryptedStr.split("\\$");
        if (parts.length != 4) {
            throw new IllegalArgumentException("Invalid token format");
        }

        return new TokenData(
            parts[0],  // userid
            parts[1],  // user4aId
            parts[2],  // moduleAddress
            parts[3]   // sendTime
        );
    }

    /**
     * Token 数据类
     */
    public static class TokenData {
        private final String userid;
        private final String user4aId;
        private final String moduleAddress;
        private final String sendTime;

        public TokenData(String userid, String user4aId, String moduleAddress, String sendTime) {
            this.userid = userid;
            this.user4aId = user4aId;
            this.moduleAddress = moduleAddress;
            this.sendTime = sendTime;
        }

        public String getUserid() { return userid; }
        public String getUser4aId() { return user4aId; }
        public String getModuleAddress() { return moduleAddress; }
        public String getSendTime() { return sendTime; }
    }
}
```

**META-INF/services/org.keycloak.authentication.AuthenticatorFactory**

```
com.example.keycloak.sso.SSOTokenAuthenticatorFactory
```

**pom.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example.keycloak</groupId>
    <artifactId>keycloak-sso-token-authenticator</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>11</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <keycloak.version>26.0.7</keycloak.version>
        <resteasy.version>6.2.9.Final</resteasy.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.keycloak</groupId>
            <artifactId>keycloak-core</artifactId>
            <version>${keycloak.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.keycloak</groupId>
            <artifactId>keycloak-server-spi</artifactId>
            <version>${keycloak.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.keycloak</groupId>
            <artifactId>keycloak-server-spi-private</artifactId>
            <version>${keycloak.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.keycloak</groupId>
            <artifactId>keycloak-services</artifactId>
            <version>${keycloak.version}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>jakarta.ws.rs</groupId>
            <artifactId>jakarta.ws.rs-api</artifactId>
            <version>3.1.0</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>

    <build>
        <finalName>${project.artifactId}</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
            </plugin>
        </plugins>
    </build>
</project>
```

**构建命令：**

```bash
mvn clean package
# 构建产物 ./target/keycloak-sso-token-authenticator.jar
```

#### 导入SPI

**挂载keycloak-sso-token-authenticator.jar**

```yaml
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
    volumes: # 将keycloak-sso-token-authenticator.jar挂载进keycloak容器
      - ./keycloak-sso-provider/target/keycloak-sso-token-authenticator.jar:/opt/keycloak/providers/keycloak-sso-token-authenticator.jar
```

**进入keycloak容器bash**

```bash
docker exec -it keycloak /bin/bash
```

**构建**

```bash
# 列出已部署的自定义认证器 JAR（确认存在）
bash-5.1$ ls /opt/keycloak/providers/keycloak-sso-token-authenticator.jar
/opt/keycloak/providers/keycloak-sso-token-authenticator.jar  # 自定义 SPI 实现 JAR 存在

# 执行 Keycloak 构建命令，将自定义 provider 注入运行时
bash-5.1$ /opt/keycloak/bin/kc.sh build
Updating the configuration and installing your custom providers, if any. Please wait.
2026-01-04 05:50:56,048 WARN [org.keycloak.services] (build-36) KC-SERVICES0047: sso-token-authenticator (com.example.keycloak.sso.SSOTokenAuthenticatorFactory) is implementing the internal SPI authenticator. This SPI is internal and may change without notice
# ↑ 警告：自定义认证器使用了内部 SPI（authenticator），该接口非公开，未来版本可能变更

2026-01-04 05:50:57,626 INFO [io.quarkus.deployment.QuarkusAugmentor] (main) Quarkus augmentation completed in 2509ms
# ↑ 构建成功，Quarkus 增强阶段耗时约 2.5 秒

Server configuration updated and persisted. Run the following command to review the configuration:
        kc.sh show-config
# ↑ 构建完成，配置已持久化；建议用 `kc.sh show-config` 查看最终生效配置
```

**重启keycloak**

```bash
docker compose restart keycloak
```

#### SPI导入成功

![SPI导入成功](images/img_20_OTUwYjVkYmNlMGM.png)

#### 配置 Authentication Flow

**复制内置的 "Browser" flow**

![复制Browser flow](images/img_23_Y2ExYjdhYzBkYzg.png)

**Add execution**

名称取决于Factory 的 getDisplayType() 方法里返回的值：

```java
@Override
public String getDisplayType() {
    return "Legacy SSO Token Authenticator";
}
```

![Add execution](images/img_12_NDcxYWE1YzI1YTB.png)

添加后，把它的 Action 设置为 ALTERNATIVE 或 REQUIRED（建议先设 ALTERNATIVE）：

- **REQUIRED：** 该执行器必须成功，否则整个认证失败。
- **ALTERNATIVE：** 该执行器是可选的替代路径；只要同一层级中任意一个 ALTERNATIVE 成功，就视为通过，其余 ALTERNATIVE 不再执行。

推荐位置：放在 "Cookie" 之后、"Identity Provider Redirector" 之前（这样可以先检查 cookie，如果没有再尝试你的 token）

![设置执行器](images/img_26_YTE0MDY4OTVmMDB.png)

#### 绑定 Flow

![绑定flow1](images/img_2_M2RjNDllYWVkYzA.png)

![绑定flow2](images/img_35_ZTUzYzI1YjZhYjM.png)

#### 测试Token SSO

使用 Token SSO Generator 生成paramString，访问：

```
http://localhost:3000/login-sso?userid=admin
```

跳转到：

```
https://keycloak.orb.local/realms/experiment/protocol/openid-connect/auth?paramString=...
```

![测试结果](images/img_28_YWY2NDk2MTYxNjI.png)

至此，Keycloak 完成对非标准 Token SSO的支持，且可将Token SSO转换为OIDC！

其中Keycloak配置项目过多，实际应用中需要依据文档按照实际情况配置，本教程列出的是主要的实现思路和步骤。

### LDAP

#### 在LLDAP中添加用户和组织

![LLDAP用户管理](images/img_21_OWI0MzRhNDNkNWM.png)

LLDAP支持使用[GraphQL](https://github.com/lldap/lldap/blob/main/schema.graphql)创建用户和组织

#### 添加LDAP provider

![添加provider](images/img_6_MTNjMGJiMWY1NmU.png)

#### 配置LLDAP的LDAP服务器

参考设置，具体按照LDAP Server文档配置

![配置LDAP服务器](images/img_7_MTRmM2JmNjRlYTh.png)

ldap服务器成功连接并成功同步人员和组织，可设置定时增量/全量同步

![同步结果](images/img_16_NzYxNWMwMjg2NmI.png)

## 总结

本实验实现了通过 Keycloak 将非标准的 Token SSO 转换为标准的 OIDC 认证流程，同时支持 LDAP 用户联邦。主要技术点包括：

1. Keycloak SPI 扩展实现自定义认证器
2. AES-128-CBC 加密的 Token 解析
3. OIDC 标准认证流程
4. LDAP 用户联邦

实际应用中需要根据具体业务场景调整配置，特别是安全相关的内容（密钥、密码等）需要使用生产级的安全方案。
