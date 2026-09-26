# 反重力 (Antigravity) 免 TUN 模式与内网共存配置规范

> **状态**：生效中（环境与工具战略级规范）  
> **适用范围**：团队内所有使用 Antigravity（Google 反重力 IDE）进行开发的 macOS 电脑（如 2019 PRO、Mac mini 等）。  
> **核心使命**：彻底摆脱 Clash / Mihomo 的 TUN（虚拟网卡）模式，保障 Tailscale 与局域网 100% 畅通直连，杜绝改动梯子订阅带来的配置被刷与整机断网，0 成本、0 额外软件实现反重力秒开。

---

## 一、背景与核心痛点

1. **为什么要关掉虚拟网卡（TUN 模式）？**
   - 开启全局 TUN 虚拟网卡会霸占整台 Mac 的所有网络，导致 **Tailscale（连接家里 Mac mini `100.83.64.112`）**、公司局域网和本地开发服务经常被劫持断连。
2. **为什么改动梯子（Clash / Party）配置是死路？**
   - 任何在梯子配置文件里写排除规则的方案都是流沙建筑：机场只要一更新订阅，改动直接被云端覆盖冲刷回白纸；且手动改 YAML 错一个缩进整台电脑直接断网。
3. **为什么不要装第三方外挂软件（ProxyBridge / Proxifier）？**
   - **ProxyBridge**：自 2026 年 6 月起已转为商业闭源收费（Pro-only），在 macOS 下网络扩展与透明代理通道经常静默失效，极不稳定；
   - **Proxifier**：商业收费软件（售价约 39 美元），有试用期限制且有系统兼容性包袱。

---

## 二、官方底层原理：环境变量自动注入机制

反重力主程序（`app.asar`）在拉起负责 AI 对话的后台核心（`language_server`）时，内置了如下官方源码：

```javascript
// Electron 应用在桌面启动时不会继承终端环境变量
// 官方主动调用 shellEnvSync() 执行系统 shell，显式装载用户环境配置：
const env = { ...process.env, ...(0, shell_env_1.shellEnvSync)() };
```

**结论**：反重力官方天生支持从用户的终端环境文件（`~/.zprofile` 和 `~/.zshrc`）中自动加载代理配置。只要配置写在系统环境底座里，无论怎么换机场订阅，配置雷打不动，终生有效！

---

## 三、新电脑 1 分钟快速配置流程（只需 2 步）

未来有任何新 Mac 电脑需要配置反重力免 TUN 模式，只需在终端中执行以下两步：

### 第 1 步：将代理与内网白名单注入系统环境底座

打开终端，直接复制并运行以下命令（梯子默认端口按 `7890`，局域网与 Tailscale 焊死直连）：

```bash
cat << 'EOF' >> ~/.zshrc

# Antigravity & AI Proxy (No TUN, Tailscale safe)
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="socks5://127.0.0.1:7891"
export NO_PROXY="100.64.0.0/10,10.0.0.0/8,192.168.0.0/16,127.0.0.1,localhost,*.local"
export no_proxy="100.64.0.0/10,10.0.0.0/8,192.168.0.0/16,127.0.0.1,localhost,*.local"
EOF

cat << 'EOF' >> ~/.zprofile

# Antigravity & AI Proxy (No TUN, Tailscale safe)
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="socks5://127.0.0.1:7891"
export NO_PROXY="100.64.0.0/10,10.0.0.0/8,192.168.0.0/16,127.0.0.1,localhost,*.local"
export no_proxy="100.64.0.0/10,10.0.0.0/8,192.168.0.0/16,127.0.0.1,localhost,*.local"
EOF
```

### 第 2 步：配置反重力用户代理偏好

在终端中执行以下命令，确保反重力编辑器前端界面也走本地代理：

```bash
mkdir -p "$HOME/Library/Application Support/Antigravity/User"
cat << 'EOF' > "$HOME/Library/Application Support/Antigravity/User/settings.json"
{
  "http.proxy": "http://127.0.0.1:7890",
  "http.proxySupport": "override",
  "http.proxyStrictSSL": false
}
EOF
```

---

## 四、验证与日常使用

1. **关掉虚拟网卡**：
   - 打开 Clash / Mihomo Party，**直接关掉“虚拟网卡”（TUN 模式）**，保持常规代理运行即可。
2. **打开方式完全自由**：
   - **直接从程序坞/启动台打开反重力**：秒开秒连，绝不白屏；
   - **使用 Cockpit Tools（多账号切换器）打开反重力**：切换账号后拉起同样自动继承代理，绝不白屏；
   - **电脑关机重启后**：开机即用，零手动维护。
3. **验证连通性**：
   - 在终端执行：`lsof -nP -c language_server | grep -i TCP`，可见大量到 `127.0.0.1:7890` 的 `ESTABLISHED` 稳定连接；
   - 在终端执行：`ping -c 2 100.83.64.112`，验证 Tailscale 内网直连畅通无阻。
