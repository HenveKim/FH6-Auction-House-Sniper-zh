[![在 Ko-fi 上支持](https://img.shields.io/badge/Support_on-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/frostyisbored) [![需要帮助？加入 Discord](https://img.shields.io/badge/Need_help%3F-Join_the_Discord-5865F2?logo=discord&logoColor=white)](https://discord.gg/PWPmVWdP8r)
# FH6 拍卖行狙击器

> ### ⚡ 这是免费版本 — 如需优化版本，请查看 [**FH6 Sniper V2**](https://fh6sniper.com)
>
> 我会继续维护这个免费版本，提供 **Bug 修复** 和游戏更新后的补丁。
>
> **V2** 是重构并优化后的狙击器版本，**速度更快、可靠性更高**，带有焕新的悬浮窗和一个**自动更新启动器**，可始终让你保持在最新版本。想要最佳性能？请访问 **[fh6sniper.com](https://fh6sniper.com/)**。
>
> <img width="459" height="508" alt="完整界面预览" src="https://github.com/user-attachments/assets/6428d0f9-47a4-4823-8cb8-aada581304a8" />


---
<img width="1655" height="792" alt="image-3" src="https://github.com/user-attachments/assets/61b58048-c3e6-4156-9510-0c2600aa7e9f" />
<img width="340" height="488" alt="image" src="https://github.com/user-attachments/assets/d594b885-9e5d-4519-bbea-182a3d99999b" />



## 适用于《Forza Horizon 6》的自动拍卖行狙击器

它会监控拍卖行中你设置好的车辆，一旦出现就立即买断、领取车辆并循环执行。只需设置一次筛选条件，然后让它保持运行即可。这个工具的买断成功率大约为 10%，通常能在 5 分钟内狙到一辆车。




---

# 功能

- 自动搜索并买断
- 跳过已售出的列表，寻找新的拍卖项
- 自动领取所有成功拍下的车辆
- 小巧的置顶悬浮窗，实时显示状态数据
- F8 开始/停止，F9 紧急停止
- 可在达到指定车辆数量或运行分钟数后自动停止
- 智能识别页面，避免误点到其他页面

---

# 支持

如果你遇到问题并需要帮助，可以加入支持服务器，在 #Get-Help 中发帖，我会看一下。https://discord.gg/PWPmVWdP8r

---

# 要求

- Windows 10 或 11
- PC 版《Forza Horizon 6》
- 1920 x 1080 分辨率 - 全屏，帧率不限制（你可能需要调整 Windows 设置以匹配）
- 极低画质预设
- **开启**动态背景（或在配置文件中设为 false）
- UI 缩放设为 **100**
- 游戏语言设为 English
- 使用键盘菜单导航（机器人使用按键，而不是鼠标）
- 如果你的 Forza 以提升权限启动，则需要以管理员身份启动机器人（右键 + 以管理员身份运行）
- 强烈建议使用有线以太网

<img width="1386" height="763" alt="image-4" src="https://github.com/user-attachments/assets/fd2bf173-259f-4458-938b-2267144ce3ab" />
<img width="1386" height="758" alt="image-5" src="https://github.com/user-attachments/assets/34f3fe88-9575-4ec5-aa6c-0c9e04a9964c" />



---

# 下载

从 [Releases 页面](https://github.com/FrostyIsBored/FH6-Auction-House-Sniper/releases) 获取最新的 **FH6-Sniper.zip**，并将其解压到电脑上的任意位置。

---

# 设置

## 第 1 步 - 打开拍卖行

启动《Forza Horizon 6》，前往嘉年华站点中的拍卖行。

<img width="1916" height="971" alt="image-1" src="https://github.com/user-attachments/assets/2e4c412e-974e-4bf4-9d4d-bbc31fcd2432" />

---

## 第 2 步 - 配置搜索

打开 **Search Auctions** 并设置筛选条件：

- 想要车辆的 **Make** 和 **Model**
- 将 **Max Buyout** 作为你的安全上限。机器人会在不检查价格的情况下购买第一辆匹配车辆，因此这是你每辆车最多可能花费的金额。请谨慎设置。

返回上一层，让屏幕停留在 **Search config** 视图。机器人会从这里开始运行。

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/7fac68c0-f89d-45ee-a10a-5133b02da681" />

---

## 第 3 步 - 运行狙击器

双击 **FH6-Sniper.exe**。屏幕左上角会出现一个小悬浮窗。

点击回到 FH6，按 **F8** 或 **Start**，然后让它保持运行。

停止方式：再次按 **F8**，按 **F9** 紧急停止，或点击悬浮窗上的 **STOP**。

<img width="1902" height="1062" alt="image-2" src="https://github.com/user-attachments/assets/ccdfba46-4c90-42de-bb79-fe26658bb262" />

---

# SmartScreen 警告

由于 exe 未签名，Windows SmartScreen 会给出警告。如要继续运行：

1. 点击 **More info**
2. 点击 **Run anyway**

---

# 热键

| 按键 | 操作 |
|---|---|
| **F8** | 开始/停止 |
| **F9** | 紧急停止 |
| **STOP** 按钮 | 与 F8 相同 |
| 悬浮窗上的 **✕** | 关闭并退出 |

---

# 设置项

机器人开箱即可使用。如果你想进行调整，请打开 **config.json**（首次运行时会在 exe 旁边创建）：

- **max_cars** - 获胜达到该数量后自动停止（默认：1）
- **max_minutes** - 运行达到该分钟数后自动停止（默认：180）
- **collect_after_buyout** - 如果你希望手动领取车辆，请设为 `false`
- **notify_sound** / **notify_toast** - 关闭获胜提示音或通知弹窗
- **buyout_select_delay_ms** - 在选择 Buy Out 与按 Enter 之间额外等待的毫秒数。如果机器人偶尔打开 Place Bid 对话框而不是 Buy Out，可以调到 `200`（默认：0）
- **moving_background** - 如果你已在 FH6 中**关闭**动态背景视频设置，请设为 `false`（默认：true）

---

# 重要提示

> [!WARNING]
> - 拍卖行自动化可能违反 Forza 的执行准则。
> - 结果可能因电脑/网络环境而异。
> - 你可能会收到警告、被暂时封禁，或被永久封禁。
> - 请自行承担风险。

---

# 备注

- 机器人只会在 FH6 是当前聚焦窗口时运行。如果你切出游戏，悬浮窗会显示 **Paused**。点击回到游戏即可继续。
- 悬浮窗会从屏幕录制/截图中隐藏，因此你可以把它放在屏幕任意位置。
- 点击并按住标题栏即可拖动悬浮窗。
- 你不会赢下每一次狙击。和其他工具一样，机器人受限于 FH6 的菜单动画和拍卖服务器响应。
- 如果服务器很慢或过载，会导致机器人出错（很快会有修复）。
---

# 故障排查

**悬浮窗显示 "Paused"** - FH6 不是当前聚焦窗口。请点击回到游戏。

**F8 没有任何反应** - 你电脑上的另一个应用可能拦截了 F8 键。关闭它，或在 `config.json` 中修改热键。

**机器人漏判某个画面并卡在那里** - 重启 FH6 和机器人。确保画质预设为 **Very Low**，分辨率为 **1920 x 1080**。

  **狙击器打开了 Buy Out 对话框，但不会点击 Yes。**
  <img width="1513" height="840" alt="image" src="https://github.com/user-attachments/assets/61472f11-389c-47f9-90e3-197530331486" />


  这几乎总是因为 FH6 的 **Moving Background** 视频设置与狙击器中的设置不匹配。如果你在游戏内关闭了动态背景，请打开悬浮窗中的 **Settings** 标签页，并取消勾选 **Moving background mode**，这样狙击器就会为你的设置加载正确的模板。

  <img width="331" height="472" alt="image" src="https://github.com/user-attachments/assets/049c4dab-a718-4cab-882e-d45782f5391c" />


  **狙击器在 Start 后马上显示 "Stopped: could not recover"。**

  两个常见原因：

  - **游戏语言不是 English。** 狙击器模板只能匹配英文 UI。
  请在 Settings > Language Select 中将 FH6 切换为 English。
  - **可被截屏捕获的悬浮窗遮住了菜单。** 如果你启用了 **Show overlay in screenshots & recordings**，悬浮窗可能会落在狙击器正在读取的区域上方。把它拖到右上角或右下角，避免遮挡游戏 UI。

  如果这些都没有帮助，请[提交 issue](https://github.com/FrostyIsBored/FH6-Auction-House-Sniper/issues) 或在 Discord 上联系我。
  **发布与机器人相关的问题时** - 请附上你的 Sniper.log，方便我排查。
