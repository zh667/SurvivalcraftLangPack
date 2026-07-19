# Survivalcraft 社区语言包 (SurvivalcraftLangPack)

为 Survivalcraft 联机版（SurvivalcraftNet 2.4）翻译**游戏本体界面**的多语言包。
本体只内置 5 种语言（en-US / es-MX / pt-BR / ru-RU / zh-CN），引擎**没有英语回退**——
缺失的键会直接显示成键名，所以每种语言都必须**整包翻译**（游戏本体约 3267 条）。

> 独立的语言包 mod，只翻译游戏本体。旅行地图 mod 自己的 `TravelMap` 文本由旅行地图仓库
> 单独提供 `<code>.json`，运行时按同一语言代码自动合并。

## 现状

`Assets/Lang/` 下**已有 3 种机翻草稿**（免费端点打样，占位符已保护，`Language.Name` 用母语名）：

| 代码 | 语言 | 状态 |
|---|---|---|
| vi-VN | Tiếng Việt | 机翻草稿 ✅ |
| id-ID | Bahasa Indonesia | 机翻草稿 ✅ |
| tr-TR | Türkçe | 机翻草稿 ✅ |

**其余语言改由 Crowdin 预翻译生成**（免费端点按 IP 限流，翻 3 种就被封，扛不住 13 种的量；
Crowdin 用正规授权 MT，有配额、不被封）。`crowdin.yml` 已配好这些目标语言的代码映射：
ja-JP / ko-KR / fr-FR / de-DE / it-IT / pl-PL / hi-IN / th-TH / uk-UA / ar-SA（阿拉伯语 RTL，需重点验 UI）。

⚠️ 所有语言都是**机翻草稿，尚未人工校对**，术语（尤其方块/物品名）需通过 Crowdin 众包完善。

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

- [ ] Windows 逐语言 UI 溢出/RTL 检查（先测 vi/id/tr 三种草稿）。
- [ ] Crowdin 生成并众包校对其余 10 种。
- [ ] 旅行地图仓库补 `Assets/Lang/<code>.json`（各语言的 128 条 `TravelMap` 文本；
      vi 有 123 条人工翻译可从 git `4261e6a` 恢复）。
