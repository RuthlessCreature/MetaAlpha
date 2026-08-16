# RFC-QIMEN-V1 — Deterministic Shijia Qimen Plate Engine

Status: **FROZEN ENGINE CONVENTION / NO MARKET EVALUATION YET**  
Version: `QIMEN_V1`  
Registered: 2026-08-16

## 1. Purpose

QIMEN_V1 defines a deterministic, testable **Shijia rotating-plate Qimen Dunjia** engine for MetaAlpha.

The engine exists to produce raw symbolic state variables that can later be evaluated as a falsifiable hypothesis family. It is not an interpretation engine and does not assign auspicious/inauspicious scores.

No market outcome may be used to choose or modify the conventions in this RFC.

## 2. Scope

QIMEN_V1 includes:

- year/month/day/hour pillars;
- exact current solar term;
- Chai-Bu (`拆补法`) three-yuan and 72-ju determination;
- Yin/Yang Dun and ju number;
- earth-plate Sanqi/Liuyi placement;
- hour-pillar Xunshou and hidden instrument;
- duty star (`值符`) and duty door (`值使`);
- heaven-plate stars and stems;
- eight doors;
- eight spirits;
- day/hour Xunkong;
- hour-branch Yima;
- star Fuyin/Fanyin state;
- raw per-palace plate representation.

QIMEN_V1 does **not** include:

- Feipan Qimen;
- Zhirun (`置闰`) or Maoshan date-fixing conventions;
- Yinpan Qimen;
- custom ju selection;
- textual divination;
- ten-stem response (`十干克应`) scoring;
- Three Wonders/doors/stars auspiciousness scores;
- any aggregate fortune or market-direction score.

Alternative conventions must be separate versioned engines/controls.

## 3. Time convention

For A-share research:

```text
timezone: Asia/Shanghai
market feature timestamp: 09:25:00
calendar engine: lunar_python==1.4.8
```

A general plate function may accept other timestamps for validation fixtures, but market features are frozen to 09:25.

### 3.1 Solar-term boundary

The active solar term is determined at timestamp precision. The engine explicitly requests the previous solar term with whole-day mode disabled and compares the returned exact solar timestamp.

A civil date is not sufficient to switch terms. If a term occurs at 23:03, a 10:00 plate on the same civil date still belongs to the preceding term.

### 3.2 Zi-hour convention

The market anchor is far from Zi hour, so the research result is not sensitive to the 23:00 day-boundary dispute. The engine records the frozen convention as `zi_sect=1` for future general use. Any alternative must be separately versioned.

## 4. Plate type and hosting convention

```text
plate_type: rotating plate / 转盘
center_palace: 5
center_host_palace: 2 (Kun)
```

Tianqin is a center star and rotates together with Tianrui under the frozen host convention. There is no door or spirit physically assigned to palace 5 in the rendered rotating plate.

## 5. Luoshu palaces and rotating perimeter

Palaces:

| Palace | Trigram | Direction |
|---:|---|---|
| 1 | Kan | North |
| 2 | Kun | Southwest |
| 3 | Zhen | East |
| 4 | Xun | Southeast |
| 5 | Center | Center |
| 6 | Qian | Northwest |
| 7 | Dui | West |
| 8 | Gen | Northeast |
| 9 | Li | South |

Frozen clockwise rotating perimeter:

```text
1 -> 8 -> 3 -> 4 -> 9 -> 2 -> 7 -> 6 -> 1
```

The star and door rotating ring does not reverse between Yang Dun and Yin Dun. Spirit placement direction does reverse.

## 6. Three Wonders and Six Instruments

Frozen earth-plate order:

```text
戊 己 庚 辛 壬 癸 丁 丙 乙
```

- Yang Dun: begin at the ju palace and advance by numeric palace number `+1`, wrapping `9 -> 1`.
- Yin Dun: begin at the ju palace and advance by numeric palace number `-1`, wrapping `1 -> 9`.

This is the earth plate only; rotating heaven-plate movement is separate.

## 7. Chai-Bu three-yuan rule

Let `day_index` be the zero-based Jiazi index of the day pillar in the 60-day cycle.

```text
five_day_block = day_index // 5
yuan_index = five_day_block % 3
fu_head_index = five_day_block * 5
```

Mapping:

```text
0 -> Upper Yuan / 上元
1 -> Middle Yuan / 中元
2 -> Lower Yuan / 下元
```

The `fu_head` is the Jiazi at `fu_head_index`.

The active solar term does not change inside its interval except at the exact term timestamp. The day pillar determines which five-day Yuan is used with that term's 72-ju row.

## 8. Frozen 72-ju table

Each tuple is `(Upper, Middle, Lower)`.

### Yang Dun

| Solar term | Ju |
|---|---|
| 冬至 | 1, 7, 4 |
| 小寒 | 2, 8, 5 |
| 大寒 | 3, 9, 6 |
| 立春 | 8, 5, 2 |
| 雨水 | 9, 6, 3 |
| 惊蛰 | 1, 7, 4 |
| 春分 | 3, 9, 6 |
| 清明 | 4, 1, 7 |
| 谷雨 | 5, 2, 8 |
| 立夏 | 4, 1, 7 |
| 小满 | 5, 2, 8 |
| 芒种 | 6, 3, 9 |

### Yin Dun

| Solar term | Ju |
|---|---|
| 夏至 | 9, 3, 6 |
| 小暑 | 8, 2, 5 |
| 大暑 | 7, 1, 4 |
| 立秋 | 2, 5, 8 |
| 处暑 | 1, 4, 7 |
| 白露 | 9, 3, 6 |
| 秋分 | 7, 1, 4 |
| 寒露 | 6, 9, 3 |
| 霜降 | 5, 8, 2 |
| 立冬 | 6, 9, 3 |
| 小雪 | 5, 8, 2 |
| 大雪 | 4, 7, 1 |

## 9. Xunshou and hidden instrument

The hour pillar selects one of the six Jia-Xun heads:

```text
甲子 -> 戊
甲戌 -> 己
甲申 -> 庚
甲午 -> 辛
甲辰 -> 壬
甲寅 -> 癸
```

The earth-plate palace containing the hidden instrument is the true Xunshou palace.

If the true palace is 5:

- the duty star is Tianqin;
- Tianqin rotates with Tianrui through host palace 2;
- the duty door is Death Door (`死门`) under the center-host convention;
- **duty-door counting still starts from true palace number 5**, not host palace 2.

The true source palace and displayed/hosted palace are both retained in output.

## 10. Duty-star movement

The hour stem determines the destination earth-plate palace. When the hour stem is Jia, its hidden instrument is used.

For star rotation:

- source palace 5 is represented on the rotating ring by host palace 2;
- destination palace 5 is represented on the rotating ring by host palace 2;
- rotate the perimeter stars by the clockwise ring distance from effective source to effective destination;
- Tianqin accompanies Tianrui and carries the center earth-plate stem.

The earth-plate stem attached to each star's original home becomes that star's heaven-plate stem after rotation.

## 11. Duty-door movement

Let `hour_offset` be the zero-based position of the hour pillar inside its 10-hour Jia-Xun.

```text
raw_destination = true_xunshou_palace + direction * hour_offset
```

where `direction=+1` for Yang Dun and `-1` for Yin Dun on the numeric 1..9 palace cycle.

If the raw destination is palace 5, the displayed door destination is host palace 2. The raw destination is still retained.

The full eight-door plate rotates on the perimeter so that the duty door reaches the displayed destination.

## 12. Eight spirits

Frozen order:

```text
值符 螣蛇 太阴 六合 白虎 玄武 九地 九天
```

- Yang Dun: place forward on the frozen perimeter from the duty-star landing palace.
- Yin Dun: place backward on the frozen perimeter from the duty-star landing palace.

Palace 5 has no spirit.

## 13. Xunkong and Yima

Xunkong is derived independently for the day and hour pillars from their Jia-Xun.

Frozen Xun void pairs:

```text
甲子旬 -> 戌亥
甲戌旬 -> 申酉
甲申旬 -> 午未
甲午旬 -> 辰巳
甲辰旬 -> 寅卯
甲寅旬 -> 子丑
```

Hour-branch Yima:

```text
申子辰 -> 寅
寅午戌 -> 申
巳酉丑 -> 亥
亥卯未 -> 巳
```

Branch-to-palace mapping is deterministic and stored as raw plate metadata.

## 14. Validation fixtures

Before market evaluation, QIMEN_V1 must pass at least these independent golden fixtures:

### Fixture A — 2026-07-09 10:30 Asia/Shanghai

Expected core state:

```text
pillars: 丙午 乙未 甲申 己巳
solar term: 小暑
term timestamp: 2026-07-07 09:56:57
Dun/Ju/Yuan: 阴遁二局 中元
fu_head: 甲申
Xunshou: 甲子遁戊
Duty star: 天芮 -> palace 1
Duty door: 死门 -> palace 6
star rotation steps: 3
Fuyin: false
Fanyin: false
```

Earth plate:

```text
1己 2戊 3乙 4丙 5丁 6癸 7壬 8辛 9庚
```

### Fixture B — 2026-01-01 12:00 Asia/Shanghai

Expected core state:

```text
pillars: 乙巳 戊子 乙亥 壬午
solar term: 冬至
term timestamp: 2025-12-21 23:03:05
Dun/Ju/Yuan: 阳遁四局 下元
fu_head: 甲戌
Xunshou: 甲戌遁己
true Xunshou palace: 5
Duty star: 天禽 -> displayed palace 8
Duty door: 死门 -> raw/displayed palace 4
star rotation steps: 4
Fuyin: false
Fanyin: true
```

Earth plate:

```text
1丁 2丙 3乙 4戊 5己 6庚 7辛 8壬 9癸
```

### Solar-term exact-time boundary

For 2025-12-21:

```text
10:00 -> still 大雪
23:30 -> already 冬至
```

## 15. Research feature policy

Only raw deterministic plate states may be exported initially, for example:

- Yin/Yang Dun;
- ju number;
- Yuan;
- duty star/door and their palaces;
- hour stem/branch;
- day stem/branch;
- per-palace star/door/spirit/stems;
- day/hour void palaces;
- Yima palace;
- Fuyin/Fanyin;
- exact solar-term interval/phase inherited from the frozen calendar layer.

The engine must not generate a single auspiciousness score.

## 16. Failure conditions

QIMEN_V1 is not ready for market research if any of the following occurs:

- a golden fixture fails;
- exact solar-term boundary tests fail;
- a convention is inferred from market performance rather than frozen beforehand;
- one function silently mixes Chai-Bu and Zhirun rules;
- center-palace hosting is not auditable;
- duty-door counting silently starts from host palace 2 when the true Xunshou palace is 5;
- plate output cannot identify the convention/version used.

## 17. Next gate

Only after the engine passes the full validation suite may a separate `QIMEN_MARKET_001` hypothesis registry be created. Market targets, feature families, null controls and validation periods must be preregistered separately from this engine RFC.
