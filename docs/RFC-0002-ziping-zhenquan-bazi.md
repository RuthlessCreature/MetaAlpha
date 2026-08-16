# RFC-0002: Ziping Zhenquan Bazi Engine v0.2

## 1. Decision

The Bazi branch of MetaAlpha will use a **Ziping Zhenquan (《子平真诠》) operationalization** as its first registered classical school.

This means the research engine does **not** begin from a generic five-element balance score. Its first-order structure is:

1. determine the four pillars using a solar-term-aware calendar;
2. take the **month command (月令)** as the organizing axis;
3. map the day master against the month-command qi to identify the pattern family;
4. distinguish favorable patterns to be used constructively (顺用) from adverse patterns to be controlled/transformed (逆用);
5. represent formation, damage, rescue and pattern quality as explicit machine-readable rule flags;
6. test those flags statistically rather than treating textual interpretation as evidence.

The classical starting point is the passage usually rendered as: “八字用神，专求月令……财官印食……顺用；煞伤劫刃……逆用。” The v0.2 engine therefore treats month-command structure as primary and keeps strength/balance variables secondary.

## 2. Source policy

The engine distinguishes:

- **classical rule source**: 《子平真诠》 passages on 用神、成败救应、格局高低;
- **calendar implementation source**: `6tail/lunar-python`, pinned by project version;
- **MetaAlpha operationalization**: our exact deterministic conversion from textual rules to features.

A MetaAlpha rule is not claimed to be the only possible scholarly interpretation. Any material alternative becomes a separate version/hypothesis family rather than silently replacing the old rule.

## 3. Calendar convention

### 3.1 Timezone

All A-share research timestamps use `Asia/Shanghai`.

### 3.2 Daily market anchor

For a session-level feature generated before trading, v0.2 uses:

```text
09:25:00 Asia/Shanghai
```

This is a registered research convention, not a metaphysical claim. Alternative anchors (09:15, 09:30, close, midnight) must be separate hypotheses.

### 3.3 Year/month boundaries

Year and month pillars are calculated through the calendar library's solar-term-aware EightChar implementation. We do not substitute lunar-month boundaries or hand-written approximate solar-term tables.

### 3.4 Day boundary

v0.2 does not use a late-night trading prediction timestamp, so the historical 子初换日 dispute is intentionally outside the first market-session experiment. Any future intraday/overnight branch must register its day-boundary convention explicitly.

## 4. Pillar representation

For each observation timestamp:

```text
year_pillar
year_stem
year_branch
month_pillar
month_stem
month_branch
day_pillar
day_stem
day_branch
time_pillar
time_stem
time_branch
```

The day stem is the **day master (日主/日干)**.

## 5. Ten-god mapping

Ten-god labels are generated deterministically from elemental generation/control plus yin-yang polarity:

```text
比肩 劫财
食神 伤官
偏财 正财
七杀 正官
偏印 正印
```

The engine stores both visible-stem ten gods and hidden-stem ten gods.

## 6. Month command and hidden stems

Each earthly branch has an ordered hidden-stem list. v0.2 stores:

- principal qi (本气);
- secondary qi;
- residual qi;
- whether each month hidden stem is transmitted/visible in year, month or hour stems.

### Important restriction

v0.2 uses the month branch's **principal hidden stem** only as the deterministic `pattern_candidate` seed. It does **not** claim that every scholarly reading of 《子平真诠》 resolves the final pattern solely from principal qi. Transmission, combinations and transformations are retained as features so later registered versions can test alternative pattern-resolution rules without rewriting history.

## 7. Pattern families

The first-order pattern family is grouped as:

| Month-command ten god | Pattern family | Mode |
|---|---|---|
| 正官 | 官格 | 顺用 |
| 正财 / 偏财 | 财格 | 顺用 |
| 正印 / 偏印 | 印格 | 顺用 |
| 食神 | 食神格 | 顺用 |
| 七杀 | 七杀格 | 逆用 |
| 伤官 | 伤官格 | 逆用 |
| 阳刃 condition | 阳刃格 | 逆用 |
| 比肩 / 劫财 otherwise | 建禄月劫 | 逆用/制化 |

The Yang-Blade lookup in v0.2 is explicitly registered for yang day masters:

```text
甲->卯
丙->午
戊->午
庚->酉
壬->子
```

Alternative Yang-Blade conventions require a new version.

## 8. 顺用 / 逆用 strategy flags

The engine does not output a free-form fortune judgment. It exposes rule flags derived from the classical strategy structure.

Examples:

### 官格

Positive structural flags include:

- visible wealth generating official;
- visible resource protecting official;
- absence/presence of month-command clash/harm/break/punishment is recorded separately.

### 财格

Flags include:

- visible food/hurting-output generating wealth;
- visible official receiving wealth generation;
- visible resource coexistence and relative position are retained for later rule versions.

### 印格

Flags include:

- visible official/seven-killings generating resource;
- visible output when body/resource is excessive is a later strength-dependent rule and is not hard-coded as universally favorable in v0.2.

### 食神格

Flags include:

- visible wealth;
- visible seven-killings for the 食神制杀 structure.

### 七杀格

Flags include:

- visible food god as control;
- visible resource as transformation route;
- visible wealth/resource are not automatically labeled good or bad without structural context.

### 伤官格

Flags include:

- visible wealth (伤官生财 route);
- visible resource (伤官佩印 route).

### 阳刃格

Flags include visible official/seven-killings as control.

### 建禄月劫

Flags include:

- official with wealth/resource;
- wealth with food/hurting-output;
- seven-killings with control.

These are stored as individual flags. A single opaque “命好/命坏” score is prohibited in v0.2.

## 9. Branch structural relations

For the month branch versus year/day/time branches, v0.2 records:

- 冲;
- 害;
- 破;
- 刑, including registered three-punishment and self-punishment sets.

These are used as auditable structural variables, especially because 《子平真诠》 repeatedly discusses formation/damage in relation to刑冲破害.

## 10. Strength variables

Strength is **not discarded**, but it is demoted from “first thing to score” to a later explanatory layer.

v0.2 may record:

- visible stem roots in branch hidden stems;
- count of same-element/supporting elements;
- month-command element;
- transmission count.

A future `zpzt_strength_v1` module may formalize旺衰/有力无力. It must be versioned separately because arbitrary numerical weights would otherwise create a giant overfitting surface.

## 11. Market applications

### 11.1 Transit-only timing

For each A-share session, generate the day's Ziping-state features at the registered anchor and test future index return/risk.

### 11.2 Market/index natal chart

A separate hypothesis may register an index/market origin timestamp and compute:

```text
natal chart × current transit
```

The origin timestamp must be frozen before testing.

### 11.3 Stock natal chart

For cross-sectional research, listing date/time may be treated as a registered stock-origin convention. A fake-origin control such as `IPO date + N days` must compete with it.

## 12. Anti-overfitting rules

- No changing hidden-stem order after seeing returns.
- No changing the daily anchor because another hour backtests better without registering a new hypothesis.
- No reclassifying a failed pattern by narrative interpretation.
- No collapsing dozens of rule variants into one reported “Ziping” result.
- Every alternate scholarly convention is a separate hypothesis/version.

## 13. v0.2 acceptance criteria

The implementation is complete when:

1. Gregorian date -> exact four-pillar output is deterministic;
2. known reference examples pass fixture tests;
3. ten-god mapping passes exhaustive stem-pair tests;
4. hidden-stem and relation tables are unit tested;
5. Ziping features can be attached to a DataFrame without future data;
6. the baseline pipeline can include/exclude Ziping features by configuration;
7. CI passes.

## 14. Deferred work

- full 成格/败格/救应 state machine;
- 有情/无情 and 有力/无力 quantitative model;
- detailed position-sensitive transformations;
- 合化条件;
- market natal-chart conventions;
- Qimen/Meihua/Yijing branches.

These are deferred deliberately. Encoding them before the primitive layer is tested would create a huge, discretionary parameter zoo.
