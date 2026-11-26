# news-image-20261126

[![news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/ahmed1813544/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/ahmed1813544/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126)

**Sum up 26 November's world news in one image** — a make.fun bounty entry.

`main.py` (Python 3.13, standard library only) draws a newspaper front
page — **THE WORLD TODAY, Thursday 26 November 2026** — and writes it to
`$MAKEFUN_OUTPUT_DIR/entry.png` (or `/output/entry.png`): a 1024×1024
PNG of the day's news, drawn entirely in code with a hand-rolled 5×7
bitmap font, rasterizer and PNG encoder. No network, no randomness:
every run writes byte-identical output.

## The day in the picture

- **Lead story — Missiles over Riyadh:** Saudi defences shoot down a
  Houthi ballistic missile aimed at the kingdom's west, hours after a
  drone is downed near Jeddah, as tankers burn in the Strait of Hormuz.
- **South Africa:** the High Court throws out the Phala Phala
  impeachment report against President Ramaphosa as unlawful.
- **Space:** Pakistan's Muhammad Zeeshan Ali docks with China's
  Tiangong station on Shenzhou-24, the first foreign astronaut aboard it.
- **United States:** Thanksgiving travel chaos as storms and long lines
  hit airports; six die in a Cessna crash off Mississippi.
- Plus NATO's eastern-flank patrols, Russian jets near South Korea, a
  record migrant arrival in the Canary Islands, Lille stunning Bayern,
  and 22 more stories in the "In Brief" column — 30 stories in all,
  each verified against wire reports of 26 November 2026.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Two runs produce the same bytes (`sha256sum` to confirm).
