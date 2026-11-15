# Bill of materials (WP3 verification)

Checked 2026-11-15, read-only, using public pages only (no accounts, no quotes, no carts).

## How to read this document

- **Live stock and prices could not be read for most LCSC and JLCPCB parts.** The part pages are rendered by JavaScript and a plain page fetch returns only static fields (MPN, package, attributes). Where a stock or price figure appears below it comes from a web-search snippet of an LCSC page, which may be cached. Those cells are marked "snippet". Cells marked "not shown" mean the page was reached but did not expose the value. Nothing here is from memory unless a row says "from memory".
- **Re-check every LCSC and JLCPCB number in the JLCPCB parts library on the day of ordering.** The plan already says this; WP7 and WP8 should treat the stock columns as unverified.
- Prices are USD unless marked EUR. The EUR conversion uses the ECB reference rate of **1 EUR = 1.1052 USD, published 13 Nov 2026** ([ECB page](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html), read 2026-11-15).

## JLCPCB assembled

| Part | Qty per board | LCSC / MPN | Library | Stock | Price | Source | Checked |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Diode 1N4148W, SOD-123 | 21 (105 on a 5-board order) | C81598 / 1N4148W, ST(Semtech) | Basic ("SMT Basic" on the LCSC page) | 1,770,050 | $0.0117 at 50+, $0.0092 at 500+ | [LCSC C81598](https://www.lcsc.com/product-detail/C81598.html), [JLCPCB C81598](https://jlcpcb.com/partdetail/ST_Semtech-1N4148W/C81598) | 2026-11-15 (live page) |
| Reset button TS-1187A-B-A-B, top-actuated | 1 (5 on a 5-board order) | C318884 / XKB TS-1187A-B-A-B, SMD-4P 5.1 x 5.1 x 1.5 mm | Basic (JLCPCB part page) | 544,620 | $0.0216 at 20+ | [JLCPCB C318884](https://jlcpcb.com/partdetail/C318884), [LCSC C318884](https://www.lcsc.com/product-detail/C318884.html) | 2026-11-15 (live page) |

- Package confirmed as SOD-123 on both pages.
- Because stock was not readable, the "if out of stock, list a basic alternative" step could not be triggered. No alternative was chosen. If WP7 sees zero stock at order time, search the JLCPCB basic library for "1N4148W SOD-123" and compare footprint and polarity before swapping.
- The manufacturer string "ST (Semtech)" is odd (ST and Semtech are different companies). It is what the pages show; the datasheet should be opened by WP7 to confirm cathode marking and footprint dimensions.

### Fee-free parts for JLCPCB (checked 2026-11-15)

Only JLCPCB "Basic" and "Promotional Extended" parts have no feeder loading fee in Economic PCBA ([list](https://jlcpcb.com/parts/basic_parts)). Of this board's parts:

- 1N4148W (C81598) and TS-1187A-B-A-B (C318884) are Basic, so both are factory-fitted.
- MSK12C02 (C431540) and TS-1186F-B-A (C908470) are Extended; JLCPCB's parts search found no Basic slide switch.
- S2B-PH-K-S (C173752) is through-hole, which Economic PCBA does not fit.
- The Kailh sockets cannot be factory-fitted on a reversible board (they go on the underside of each half), and LCSC has none in stock.

## Hand-soldered per keyboard (2 halves)

| Part | Qty | LCSC / MPN | Stock | Price | Source | Checked |
| --- | --- | --- | --- | --- | --- | --- |
| Kailh MX hot-swap socket | 42 (+ spares) | C2803348 / CPG151101S11 | "Not available now" | none listed | [LCSC C2803348](https://www.lcsc.com/product-detail/C2803348.html) | 2026-11-15 (live page) |
| Kailh MX socket, variants | as above | CPG151101S11-1 = C5184526; CPG151101S11-16 = C5156480 | Both "Not available now" | none listed | [C5184526](https://www.lcsc.com/product-detail/C5184526.html), [C5156480](https://www.lcsc.com/product-detail/C5156480.html) | 2026-11-15 (live page) |
| Kailh Choc hot-swap socket | 42 (+ spares) | C5333465 / CPG135001S30 | "Not available now" | none listed | [LCSC C5333465](https://www.lcsc.com/product-detail/C5333465.html) | 2026-11-15 (live page) |
| Kailh hot-swap sockets, keyboard shop (use this) | 50 per pack | splitkb KLH-SKT-MXS-050; variants MX (black, white, beige, blue, green) and Choc (black) | Orderable, quantity selector shown | EUR 7.95 per 50 incl. 21% NL VAT | [splitkb](https://splitkb.com/products/kailh-hotswap-sockets) | 2026-11-15 (live page) |
| Power slide switch, THT candidate | 2 | ECE ESP2010 = C40646683: SPDT, through hole, right angle, 3 pin, 10 x 2.5 mm, 6.5 mm switch height; JLCPCB library: Extended | 91 | $0.73 at 1, $0.59 at 10+ | [LCSC C40646683](https://www.lcsc.com/product-detail/C40646683.html) | 2026-11-15 (live page) |
| Slide switch MSK12C02 (SMD, right angle) | 2 | SHOU HAN MSK12C02 = C431540: SPDT, "Surface Mount, Right Angle", 8 x 2.8 mm, 1.4 mm high, 50 mA; JLCPCB library: Extended | 161,620 | $0.052 at 10+ | [C431540](https://www.lcsc.com/product-detail/C431540.html) (C2681568 and C431541 are colour variants, not re-read) | 2026-11-15 (live page) |
| Reset button, right-angle SMD (fallback only, not used) | 2 | XKB TS-1186F-B-A = C908470: SPST, "Surface Mount, Right Angle", 3.6 x 3.5 mm, 3.6 mm high; JLCPCB library: Extended | 345 | $0.19 at 5+ | [LCSC C908470](https://www.lcsc.com/product-detail/C908470.html) | 2026-11-15 (live page) |
| JST PH 2-pin, side entry (right angle), THT | 2 | JST S2B-PH-K-S(LF)(SN) = C173752: through hole, right angle, 2.0 mm pitch; JLCPCB library: Extended | 180,780 | $0.04 at 20+ | [LCSC C173752](https://www.lcsc.com/product-detail/C173752.html) | 2026-11-15 (live page) |
| JST PH 2-pin, vertical, THT | alt | B2B-PH-K-S(LF)(SN) = C131337. Width about 4.5 mm, mounted height about 8.0 mm (LCSC FAQ), 5.9 mm edge length | Snippet: about 26K | Snippet: $0.033 | [LCSC C131337](https://www.lcsc.com/product-detail/C131337.html) | 2026-11-15 |
| Controller socket strips, low profile | 4 strips (2 per controller) | Mill-Max 315-43-112-41-003000 (series 315, 2.54 mm, single row; 12 positions inferred from the part-number pattern and a sibling listing) | Snippet: 4,425 at one Mouser site | Snippet: about $4.31 each | [Mouser series 315](https://www.mouser.ca/c/connectors/ic-component-sockets/?series=315). The distributor page ibselectronics returned HTTP 403 | 2026-11-15 (snippet only) |
| Matching pins for the controller side | 2 sets | Mill-Max 3305 series pins: not looked up, part number from the task brief, unverified | n/a | n/a | n/a | not verified |
| 1S LiPo, JST PH lead | 2 | See notes below | n/a | n/a | see below | 2026-11-15 |
| nice!view display (optional) | 2 | Not looked up | n/a | n/a | [nicekeyboards.com/nice-view](https://nicekeyboards.com/nice-view) lists regional retailers | not verified |

### Notes on the hand-soldered rows

**Hot-swap sockets.** Both LCSC numbers in the plan are correct for MPN and manufacturer. The MX socket C2803348 is reported out of stock in a snippet, so have C5184526 or a keyboard-shop supply as a fallback. Check that fallback variants have the same pad geometry (the -1 and -16 suffixes may differ in packaging or pad plating); the plan's footprint is built around CPG151101S11.

**Slide switch footprint and dimensions for WP5/WP7.**

- MSK12C02 family (SMD, right angle, side-actuated): LCSC attributes give body length 8 mm, width 2.8 mm, switch height 1.4 mm, package "SMD, 8 x 2.8 mm". The page names it surface mount with SMD tabs. It is only large-pad hand-solderable on one face per board, but its pads are on the board face, so it can be fitted from either face with a mirrored pad set. This matches the plan's "large-pad" option rather than through-hole.
- ECE ESP2010 (C40646683): THT, right angle, three pins, package "10 x 2.5 mm" per snippet. Pin pitch and actuator direction were not confirmed. A through-hole part is simpler to hand solder from either face, but WP5 needs the datasheet before drawing the footprint.
- Alps SSSS811101 and PCM12SMTR (named in the task brief) were not looked up; no data here.
- The 2.8 mm / 1.4 mm figures belong to the MSK12C02 SMD variants; the classic through-hole MSK-12C02 was not found on LCSC in these searches.

**Reset button (decided 2026-11-15).** TS-1187A-B-A-B (C318884) is top-actuated ("Surface Mount, Vertical"), not right-angle, but it is a JLCPCB Basic part, so JLCPCB fits it on face A with the diodes at no feeder fee. Left half: pressed through a hole in the tray; right half: faces up beside the controller, outside the plate. TS-1186F-B-A (C908470, right-angle, Extended) stays as a hand-soldered fallback footprint.

**JST PH connector, vertical or right angle.** Recommendation (judgement, not a verified fact): use the side-entry S2B-PH-K-S (C173752). The vertical B2B body is about 8.0 mm tall, which is more than a 2.5 to 5 mm tray gives, and its cable climbs vertically into the controller. The side-entry part keeps the wire lying flat under or beside the controller. WP5 should put the 5.9 mm edge length and 4.5 mm width into the keepout, and the cable exit toward the board edge.

**Controller sockets.** The Mill-Max 315 series is described by a distributor as ultra low profile. Exact height of the -112 variant and compatibility of 3305 pins were not confirmed. A cheaper common alternative, standard 2.54 mm machine-pin strips or soldering the controller to the pads through the "diode-leg" approach, is from general knowledge and was not checked here.

**LiPo.** Naming convention "4.0 x 12 x 30" for a 401230 cell (thickness x width x length in mm) is inferred from a listing that states 3.9 x 19.9 x 27 mm for a 402025 cell. I did not find a listing for a 401230 pack with a JST PH lead, so no dimensions are confirmed for it. Cells found with a PH lead are wider (about 20 mm wide, 27 to 28 mm long, 4.2 to 4.3 mm thick, 150 mAh) from [Kiwi Electronics](https://www.kiwi-electronics.com/en/brand-pkcell/lithium-polymer-li-po-battery-3-7v-150mah-3459) and [The Pi Hut](https://thepihut.com/products/150mah-3-7v-lipo-battery); a Pro Micro is about 18 mm wide, so a 20 mm wide cell sits beside, not strictly under, the controller. Polarity caveat: JST PH polarity is not standardised across sellers. Always check red and black against the board marking, and swap pins in the connector if needed, before connecting.

## Controllers

| Controller | Source | Price | Notes | Link | Checked |
| --- | --- | --- | --- | --- | --- |
| nice!nano v2 | Splitkb (Netherlands) | 21.44 EUR, "original price" in a snippet; the page returned HTTP 429 when opened, and the snippet does not say whether it is v2 | Official ZMK board `nice_nano//zmk` | [Splitkb](https://splitkb.com/products/nice-nano) | 2026-11-15 (snippet only) |
| nice!nano, spec page | nicekeyboards.com | No price on the page | nRF52840, 3.3 V, quiescent about 20 uA, charger 4.2 V at 100/500 mA, 21 GPIO, mid-mount USB-C, 3.2 mm thick | [nicekeyboards.com](https://nicekeyboards.com/nice-nano) | 2026-11-15 |
| SuperMini nRF52840 (EU resale) | Fruugo and OnBuy listings | About 16 to 24 EUR, sold as "compatible with nice!nano v2" (snippets) | These are not the 4 to 6 EUR AliExpress price in the plan | [Fruugo example](https://www.fruugo.ie/nrf52840-development-board-supermini-compatible-for-nice-nano-v20/p-398113173) | 2026-11-15 (snippet only) |
| SuperMini nRF52840, keeb.io | keeb.io | Not read, page returned HTTP 403 | | [keeb.io](https://keeb.io/products/supermini-nrf52840-pro-micro-bluetooth-le-ble-controller) | not reachable |
| SuperMini, AliExpress | AliExpress | Not checked | The plan's 4 to 6 EUR is unverified | none | not verified |

### SuperMini variants and known issues

Source for everything in this block: [joric/nrfmicro wiki, Alternatives](https://github.com/joric/nrfmicro/wiki/Alternatives) (first 100,000 of 117,492 characters read), read 2026-11-15. It is a community wiki, so treat it as reports, not specs.

- **Pinout:** the wiki says the pinout is the same as the nice!nano v2, and the board runs ZMK as a nice!nano board. A pin-naming issue is referenced as wiki issue 77. For this design, "same pinout" still needs a multimeter or schematic check on the exact boards bought, as the plan already says.
- **Charger:** LTH7R or TP4054 (SOT-23-6) instead of the nice!nano's BQ24072. Battery voltage divider is unpopulated, so battery voltage cannot be read while charging (VDDH goes to 5 V). A back jumper (0R, 0402) selects 100 to 300 mA charge current.
- **Regulator:** external 3.3 V LDO with an enable pin (ME6217C33M5G in early boards; RT9013-33GB or TP2028-3.3YN5G in an August 2024 revision; a "red" September 2024 revision uses an LDO marked S2LC). VCC can be cut by driving P0.13 low, which is the same control the ZMK nice!nano board file uses for external power (`EXT_POWER` on gpio0 pin 13).
- **Sleep current:** early batches leaked about 700 uA with VCC off versus about 20 uA for a nice!nano, caused by a 5.6 k pull-up; replacing it with 10 M fixes it, and batches after April 2024 use 10 M. Some late batches use silicon instead of Schottky diodes (about 60 uA instead of about 4 uA, wiki issue 85). Black/red "TENSTAR" boards from 2025-03 leak about 6 uA. A March 2026 report says to power-cycle after flashing to restore deep sleep (issue 87).
- **Other reported issues:** cheap salvaged parts and early-failure reports; 6 of 18 black TENSTAR boards faulty in a July 2025 report while red ones were fine; trouble with the 32.768 kHz crystal (ZMK docs have a workaround); some sellers use a 1.2 mm PCB with wrong USB connector (WCMCU and A+A+A blacklisted); LEDs swapped (red is Bluetooth, blue is charging).
- **Battery pads:** the wiki text I read does not describe pad positions. One search snippet said some clones carry battery pads on the back and have a slightly offset trio of middle pins; I could not verify this. WP5 must measure the exact boards before finalising the battery holes.
- **Different board with the same name:** a "SuperMini V2" with an LPS BMCU3 charger and no external LDO exists. Buy by checking photos and seller data, not by name.
- **ZMK hardware list:** [zmk.dev/docs/hardware](https://zmk.dev/docs/hardware) does not mention the SuperMini; the Pro Micro interconnect lists nice!nano, nRFMicro, BlueMicro840 and Puchi-BLE.

## Mechanical

| Part | Qty per half | Spec | Source | Checked |
| --- | --- | --- | --- | --- |
| M2 brass heat-set insert | 5 | Hole size guidance from a supplier: 3.0 to 3.2 mm pilot hole for a typical M2 insert; a flanged insert (4.8 mm flange, 3.9 mm long) lists 3.2 mm +0.1/-0; McMaster lists a 3.2 mm drill for a 4 mm installed length. Test-print a scrap hole first. | [accu-components size chart](https://accu-components.com/p/488-threaded-insert-hole-size-charts-for-3d-printing-pla-petg-resin), [flanged M2 insert](https://accu-components.com/us/brass-threaded-inserts/985938-HTFBI-M2-BR) | 2026-11-15 |
| M2 screw | 5 | Length depends on the final stack, not verified. For a 2.5 to 5 mm tray, 4 to 6 mm screws are a reasonable starting range (judgement, not sourced) | n/a | not verified |
| Spacers | not decided | The Lily58 Pro guide uses M2 spacers 4 mm for Choc and 7 mm for MX between plate and PCB; this design uses a printed case, so not applicable | [Lily58 Pro build guide](https://raw.githubusercontent.com/kata0510/Lily58/master/Pro/Doc/buildguide_en.md) | 2026-11-15 |

## Verified claims

### a. ZMK `nice_view_adapter` pinout

Read from `zmkfirmware/zmk` main on 2026-11-15:

- [`nice_view_adapter/boards/nice_nano_nrf52840_zmk.overlay`](https://github.com/zmkfirmware/zmk/blob/main/app/boards/shields/nice_view_adapter/boards/nice_nano_nrf52840_zmk.overlay)
- [`nice_view_adapter/README.md`](https://github.com/zmkfirmware/zmk/blob/main/app/boards/shields/nice_view_adapter/README.md)
- [`nicekeyboards/nice_nano/arduino_pro_micro_pins.dtsi`](https://github.com/zmkfirmware/zmk/blob/main/app/module/boards/nicekeyboards/nice_nano/arduino_pro_micro_pins.dtsi) (the Pro Micro to nRF GPIO map)

| Signal | nRF52840 pin | Pro Micro pin (ZMK `&pro_micro N` / Arduino label) |
| --- | --- | --- |
| SPI SCK | P0.20 | 3 (D3, the I2C SCL position) |
| SPI MOSI | P0.17 | 2 (D2, the I2C SDA position) |
| SPI MISO | P0.25 | not on the Pro Micro header (declared in the pinctrl, not used by the display) |
| Chip select | P0.06 | **1 (D1, "TX0", top-left pin looking at the front with USB up)**, `cs-gpios = <&pro_micro 1 GPIO_ACTIVE_HIGH>` |

- The adapter disables the I2C bus (`&pro_micro_i2c { status = "disabled"; }`) and reuses the OLED header's SDA and SCL pins for MOSI and SCK. Power and ground come from the usual OLED header pins.
- The README states the adapter assumes CS is `&pro_micro 1`, "top left pin when looking at the front of the board", and that another pin means overriding `cs-gpios`.
- Corne matrix pins from `corne.dtsi`, `corne_left.overlay`, `corne_right.overlay`: rows `&pro_micro 4, 5, 6, 7`; left columns 21, 20, 19, 18, 15, 14; right columns 14, 15, 18, 19, 20, 21 (reversed order, as the plan says). So D1, D2 and D3 are free for the display and do not collide with the matrix.
- Caution: the Corne shield's own RGB example overlay uses P0.06 as the WS2812 MOSI. RGB is left out of v1, so there is no conflict, but it would clash with the display CS pin.
- Note: the GPIO map lists labels D16 = P0.10 and D14 = P1.11. Use ZMK numbers (14, 15, 16, 18 to 21) when wiring, and cross-check against the physical controller silkscreen.

### b. Lily58 Pro and MX and Choc hot-swap

Partly verified from the [kata0510/Lily58](https://github.com/kata0510/Lily58) repo, read 2026-11-15:

- The Pro build guide lists "Key switch (Cherry MX, Kailh choc), 58 pieces" and says "MX switch and choc switches use separate connectors". It tells the builder to solder the MX socket on the pad area and the "Choc socket on the lower side" of the same footprint, with sockets on the back side, the same side as the diodes ([build guide](https://raw.githubusercontent.com/kata0510/Lily58/master/Pro/Doc/buildguide_en.md)).
- The repo ships a footprint file `MX_Choc_Hotswap.kicad_mod` (internal module name `CherryMX_KailhLowProfile_Hotswap_edge`) in `Pro/PCB/Lily58_Pro-footprint.pretty/` ([listing](https://github.com/kata0510/Lily58/tree/master/Pro/PCB/Lily58_Pro-footprint.pretty)). I read only the header of that file, not the pad geometry.
- Conclusion: the claim that the Lily58 Pro accepts both MX and Choc hot-swap sockets is supported by the build guide and the footprint name. Whether it supports Choc V2 and whether it works from both faces was not checked. WP5 can use `MX_Choc_Hotswap.kicad_mod` as prior art; check its licence in the repo first (not checked).

### c. JLCPCB fees

See the next section. Short answer: assembly fees verified; bare 5-board 135 x 95 mm price not obtainable without the quote tool.

### d. JLCPCB 2-layer design rules

See the next section.

## JLCPCB fees and design rules

### Economic PCBA fees (USD)

From [JLCPCB PCB assembly price details](https://jlcpcb.com/help/article/pcb-assembly-price), read 2026-11-15. A [JLCPCB blog post](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype) quoted on 9 Oct 2026 shows the same setup and stencil numbers.

| Item | Economic fee |
| --- | --- |
| Setup | $8.18 |
| Stencil | $1.53 |
| SMT assembly | $0.0016 per joint (1 to 100,000 joints) |
| Pre-reflow soldering | $0.016 per joint (1 to 1,000,000 joints); the page lists this row, but whether it applies to an ordinary SMT order is unclear |
| Feeder loading | $3.07 per unique Extended part. Zero for Basic parts. |
| Through-hole / manual | $0.0164 per joint, plus $3.58 hand-soldering labour per order (not used here) |
| Large size | $57.46 if a board is over 650 cm2 (not relevant at about 128 cm2) |
| Handling, stencil storage, fixtures | not applicable to Economic |

[Assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) for Economic: single-sided placement, single board 10 x 10 to 470 x 500 mm, panel up to 250 x 250 mm, board thickness 0.8 to 1.6 mm, 2 to 50 pieces, minimum component 0402, edge rails and fiducials not necessary, **V-cut not supported** (single boards or mouse-bite panels only).

For this order (5 boards, 21 diodes each, 2 joints each, 210 joints): SMT about $0.34. Adding the TS-1187A reset button (4 joints per board, 20 joints, Basic so no feeder fee) adds about $0.03 in joints and about $0.11 in parts. With setup and stencil that is about **$10.05 (9.09 EUR)**, or about **$13.41 (12.13 EUR)** if the pre-reflow row also applies. Diode part cost is not included (price not readable; likely cents) and neither is shipping or any large-board or ENIG extra.

### Bare 2-layer boards, 5 pieces, about 135 x 95 mm

- **No price could be obtained.** The public pages do not give a per-size table. The [extra charges page](https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra) says single boards "within or equal to 102 x 102 mm" get a special price; 135 x 95 mm exceeds that in one dimension, so the promo price does not apply. I did not run a quote. Treat the plan's 8 to 15 EUR as unverified.
- Large-board surcharge applies above 650 cm2 per board; this board is about 128 cm2.
- Maximum size for 2-layer fabrication is far above this board (page says 10 x 10 to 480 x 320 mm or larger).

### 2-layer design rules for WP7

From [JLCPCB PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), read 2026-11-15.

| Rule | Value |
| --- | --- |
| Track width / spacing, 1 oz | 0.10 / 0.10 mm minimum (use 0.15 or more for margin) |
| Track width / spacing, 2 oz | 0.16 / 0.16 mm |
| Via hole | 0.15 mm minimum; 0.2 mm preferred |
| Via pad diameter | 0.25 mm minimum; should be 0.1 mm larger than the hole (0.15 mm preferred). So a 0.3 mm hole with a 0.6 mm pad is comfortably within the rules. |
| PTH annular ring, 1 oz | 0.25 mm recommended; 0.18 mm absolute minimum |
| Via hole-to-hole spacing | 0.2 mm; pad hole-to-hole 0.45 mm |
| Copper to routed board edge | 0.2 mm |
| Copper to V-cut edge | 0.4 mm (V-cut not usable with Economic PCBA) |
| Copper to non-mouse-bite edge | 0.2 mm |
| Silkscreen | 0.15 mm line width, 1.0 mm text height, width:height 1:6 preferred |
| Solder mask bridge, 1 oz | 0.10 mm (0.13 mm black and white) |
| Mouse bites | Bite diameter 0.5 to 0.8 mm, bite spacing 0.2 to 0.3 mm (the page's wording), minimum break-away tab width 4 mm, 5 mm when mouse bites are used, panel board spacing 1.6 or 2 mm |

The page's mouse-bite figures are written for panels (board to rail). The plan's break-off column is an internal tab inside one board, so these numbers are guidance, not a spec for that use. WP7 should keep mounting holes and traces off the perforation line and place only one column trace across it, as planned.

## Cost estimate (EUR)

Rate: 1 EUR = 1.1052 USD (ECB reference, 13 Nov 2026). All prices before shipping and Finnish VAT. "Verified" means read from a source on 2026-11-15; "snippet" means taken from a search result of the page.

| Item | Plan (EUR) | Updated (EUR) | Status |
| --- | --- | --- | --- |
| 5 PCBs, 2-layer, about 135 x 95 mm | 8 to 15 | 8 to 15, unchanged | Not verified; JLCPCB's special price stops at 102 x 102 mm |
| Economic PCBA on 5 boards, setup, stencil, 210 SMT joints | 10 to 15 | 9 to 12 plus diode parts and shipping | Verified fees |
| 2 controllers: nice!nano | 42 to 50 | about 43 (2 x 21.44 at Splitkb) | Snippet |
| 2 controllers: SuperMini | 8 to 12 | 8 to 12 on AliExpress is unverified; EU resale listings seen at about 32 to 48 for two | Snippet |
| 50 hot-swap sockets, LCSC | 7 to 10 | 3 to 6 at LCSC unit prices, plus LCSC shipping; about 10 to 15 if bought in a keyboard shop at about 5.7 EUR per pack | Snippet; the MX socket may be out of stock |
| 2 batteries, switches, buttons, connectors, pin sockets, screws, inserts, filament | 15 to 22 | 15 to 22, unchanged; connectors, switch and buttons are only cents each at LCSC; Mill-Max sockets are about 4 EUR each, 4 needed, so about 16 EUR on their own if used | Partly verified |
| 42 switches and a keycap set | 30 to 60 | 30 to 60, unchanged | Not checked |

Updated total for one keyboard with SuperMini controllers: unchanged at roughly 80 to 130 EUR if Mill-Max sockets are skipped; add about 16 EUR if Mill-Max sockets are used, and add about 25 to 35 EUR if buying SuperMini in the EU instead of from AliExpress.

## Open issues

1. **Stock and price were read from the live LCSC pages on 2026-11-15** for the diode, sockets, switches, buttons and JST connector (browser, JavaScript rendered). Re-check C81598 stock and Basic status on the JLCPCB order page at order time.
2. **No Kailh socket is available on LCSC** (C2803348, C5184526, C5156480 and C5333465 all "Not available now"). Buy sockets from a keyboard shop, for example splitkb (EUR 7.95 per 50, MX or Choc).
3. **Reset button decided:** TS-1187A-B-A-B (C318884, Basic) fitted by JLCPCB on face A. WP4 places it beside the controller, WP6 adds a press hole in the left tray.
4. **Power switch not settled.** MSK12C02 (the plan's example) is SMD on LCSC with 8 x 2.8 x 1.4 mm body, not through-hole; the through-hole candidate ECE ESP2010 (C40646683) lacks a confirmed pin pitch and actuator direction. Alps SSSS811101 and PCM12SMTR were not checked.
5. **Bare PCB price for 5 boards at 135 x 95 mm not obtained.** Needs a JLCPCB quote.
6. **JLCPCB per-joint fee ambiguity:** the table lists both "pre-reflow soldering" ($0.016) and "SMT assembly" ($0.0016). Difference on this order is about $3.
7. **SuperMini clones:** the pinout is reported as the same as the nice!nano v2, but charger, LDO, sleep current and battery pad positions vary by batch and colour. Buy two, measure, then freeze the battery holes. EU resale prices are about 16 to 24 EUR, not 4 to 6 EUR; AliExpress price not checked.
8. **LiPo:** no 401230 pack with a PH lead was found; cells found with PH leads are about 20 mm wide, wider than the 12 mm assumed. Check cell size against the final tray before buying.
9. **Mill-Max 315-43-112-41-003000:** 12 positions and exact height are inferred, and the 3305 pin part is unverified.
10. **Lily58 Pro:** the dual MX/Choc claim is supported by its build guide and footprint name, but pad geometry and licence were not read.
11. **nice_view_adapter** pins are verified from source (SCK P0.20 on D3, MOSI P0.17 on D2, CS P0.06 on D1) but depend on the nice!nano map in ZMK main; a different controller (SuperMini) is assumed identical by community reports only.
12. **ECB rate** is from 13 Nov 2026 (the last working day before 15 Nov).
