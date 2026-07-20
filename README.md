# Survivalcraft 社区语言包 (SurvivalcraftLangPack)

为 Survivalcraft 联机版（SurvivalcraftNet 2.4）翻译**游戏本体界面**的多语言包。
本体只内置 5 种语言（en-US / es-MX / pt-BR / ru-RU / zh-CN），引擎**没有英语回退**——
缺失的键会直接显示成键名，所以每种语言都必须**整包翻译**（游戏本体约 3267 条）。

> 独立的语言包 mod，只翻译游戏本体。旅行地图 mod 自己的 `TravelMap` 文本由旅行地图仓库
> 单独提供 `<code>.json`，运行时按同一语言代码自动合并。

## 配合模组使用

游戏本体只内置 5 种语言。模组（如 [旅行地图](https://github.com/zh667/SurvivalCraftTravelMap)）即便自带了其他语言的文本，若游戏本体缺这门语言，它在游戏里仍是残缺的“孤儿语言”（界面显示键名）。**想使用这些扩展语言时，把本语言包和对应模组一起放进 `NetMods/` 即可**：本包补齐游戏本体翻译，模组补齐自己的文本，二者在同一语言代码下自动合并，整个界面即完整显示。仅需游戏内置的 5 种语言时，可不安装本包。

## 现状

`Assets/Lang/` 下已通过 Crowdin 预翻译生成**全部 13 种语言**（`Language.Name` 用母语名，占位符已保护）：

`vi-VN` · `id-ID` · `tr-TR` · `ja-JP` · `ko-KR` · `fr-FR` · `de-DE` · `it-IT` · `pl-PL` · `hi-IN` · `th-TH` · `uk-UA` · `ar-SA`（阿拉伯语为 RTL，需重点验 UI）。

⚠️ 目前均为**机翻草稿，尚未逐条人工校对**，术语（尤其方块/物品名）仍在通过 Crowdin 众包完善。

## 结构

```
source/en-US.json        # 翻译源（游戏本体英文 3267 条）——不打进包
Assets/Lang/<code>.json  # 各语言译文（打进 .netmod）
modinfo.json             # mod 元数据
crowdin.yml              # Crowdin 源→各语言映射
tools/build.py           # 打包 .netmod（自动收集所有语言文件）
tools/mt_seed_all.py     # 免费端点机翻脚本（有限流，仅作打样）
artifacts/SurvivalcraftLangPack.netmod
```

## 安装测试

`python3 tools/build.py` 出包，把 `artifacts/SurvivalcraftLangPack.netmod` 复制到 Windows
游戏 `NetMods/`，进 设置 → 语言 逐一选着看。重点：
1. 是否是像样的目标语言（不是键名/中文兜底）；
2. **UI 有没有被挤爆**（越南语/德语等常比英文长）；
3. **方块/物品名**能否接受；
4. **阿拉伯语的 RTL** 有没有错乱。

## 用 Crowdin 完善并生成剩余语言（checklist）

1. 在 [crowdin.com](https://crowdin.com) 建项目：源语言 **English**，目标语言加上
   Vietnamese / Indonesian / Turkish / Japanese / Korean / French / German / Italian /
   Polish / Hindi / Thai / Ukrainian / Arabic。开源项目可申请免费方案。
2. 把本仓库推到 GitHub，在 Crowdin 里用 **Integrations → GitHub** 连上本仓库
   （`crowdin.yml` 已配好：源 `source/en-US.json` → 输出 `Assets/Lang/<code>.json`）。
3. 在 Crowdin 里开 **Pre-translation（机翻预填）**，一次性把全部目标语言机翻打底
   （已有的 vi/id/tr 可作为翻译记忆导入，避免重复）。
4. 邀请对应母语玩家在网页上逐条校对，重点统一方块名术语。
5. Crowdin 会**自动往 GitHub 开 PR**，把各语言 `Assets/Lang/<code>.json` 回填。
6. 合并后跑 `python3 tools/build.py` 重新出包。

## 待办

- [x] Crowdin 生成全部 13 种语言（机翻草稿）。
- [x] 旅行地图仓库补齐各语言的 `TravelMap` 文本（已随包发布 18 种语言）。
- [ ] Windows 逐语言 UI 溢出 / 阿拉伯语 RTL 检查。
- [ ] 各语言逐条人工校对（重点统一方块/物品名术语）。
