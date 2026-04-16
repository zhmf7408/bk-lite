import type { OAuthConfig, OAuthUserConfig } from "next-auth/providers/oauth";

export interface WechatProfile {
  openid: string;
  nickname?: string;
  sex?: string;
  province?: string;
  city?: string;
  country?: string;
  headimgurl?: string;
  privilege?: string[];
  unionid?: string;
  access_token?: string;
}

export default function WeChatProvider<P extends WechatProfile>(
  options: OAuthUserConfig<P> & { redirectUri: string }
): OAuthConfig<P> {
  console.log("[WeChat OAuth] Initializing WeChat Provider with options:", {
    clientId: options.clientId ? "Set" : "Not set",
    clientSecret: options.clientSecret ? "Set" : "Not set",
    redirectUri: options.redirectUri,
  });

  return {
    id: "wechat",
    name: "WeChat",
    type: "oauth",
    version: "2.0",
    wellKnown: undefined,
    authorization: {
      url: "https://open.weixin.qq.com/connect/qrconnect",
      params: {
        appid: options.clientId,
        response_type: "code",
        scope: "snsapi_login",
        redirect_uri: options.redirectUri
      }
    },
    token: {
      url: "https://api.weixin.qq.com/sns/oauth2/access_token",
      async request({ params }) {
        console.log("[WeChat OAuth] Token request params:", params);
        
        const url = new URL("https://api.weixin.qq.com/sns/oauth2/access_token");
        url.searchParams.set("appid", options.clientId);
        url.searchParams.set("secret", options.clientSecret);
        url.searchParams.set("code", params.code!);
        url.searchParams.set("grant_type", "authorization_code");

        console.log("[WeChat OAuth] Token request URL:", url.toString());

        const response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            "Accept": "application/json",
          },
        });

        const tokens = await response.json();
        console.log("[WeChat OAuth] Token response:", tokens);

        if (tokens.errcode) {
          throw new Error(`WeChat token error: ${tokens.errmsg} (${tokens.errcode})`);
        }

        return {
          tokens: {
            access_token: tokens.access_token,
            openid: tokens.openid,
            unionid: tokens.unionid,
          }
        };
      }
    },
    userinfo: {
      url: "https://api.weixin.qq.com/sns/userinfo",
      async request({ tokens }) {
        console.log("[WeChat OAuth] Userinfo request with tokens:", tokens);
        
        const url = new URL("https://api.weixin.qq.com/sns/userinfo");
        url.searchParams.set("access_token", tokens.access_token!);
        url.searchParams.set("openid", (tokens as any).openid!);
        url.searchParams.set("lang", "zh_CN");

        console.log("[WeChat OAuth] Userinfo request URL:", url.toString());

        const response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            "Accept": "application/json",
          },
        });

        const profile = await response.json();
        console.log("[WeChat OAuth] Userinfo response:", profile);

        if (profile.errcode) {
          throw new Error(`WeChat userinfo error: ${profile.errmsg} (${profile.errcode})`);
        }

        return {
          ...profile,
          access_token: tokens.access_token,
        };
      }
    },
    async profile(profile) {
      console.log("[WeChat OAuth] Processing profile:", {
        openid: profile.openid || "Not received",
        nickname: profile.nickname || "Not received",
        unionid: profile.unionid ? "Set" : "Not set"
      });

      try {
        const registerResponse = await fetch(`${process.env.NEXTAPI_URL}/api/v1/core/api/wechat_user_register/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: profile.openid,
            nick_name: profile.nickname || profile.openid
          }),
        });

        const registerData = await registerResponse.json();
        console.log("[WeChat OAuth] Register API response:", registerData);

        if (!registerResponse.ok || !registerData.result) {
          console.error("[WeChat OAuth] Register API failed:", registerData);
          throw new Error(`WeChat user register failed: ${registerData.message || 'Unknown error'}`);
        }

        // Use data returned from registration interface
        const userData = registerData.data;
        return {
          id: userData.id.toString(),
          name: userData.username || profile.nickname || profile.openid,
          username: userData.username,
          image: profile.headimgurl,
          email: null,
          token: userData.token,
          locale: userData.locale || 'zh',
          timezone: userData.timezone || 'Asia/Shanghai',
          wechatOpenId: profile.openid,
          wechatUnionId: profile.unionid,
        };

      } catch (error) {
        console.error("[WeChat OAuth] Error during user registration:", error);
        throw error;
      }
    },
    clientId: options.clientId || "",
    clientSecret: options.clientSecret || ""
  };
}
