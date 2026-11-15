# Reversible Corne-style split keyboard: design and build plan

As of 15 Nov 2026.

## Summary

Build a 42-key Corne-layout wireless split on one reversible PCB design: order 5 identical boards, use one face-up as the left half and one flipped as the right half.

- **Layout:** Corne 3x6+3 at MX spacing (19.05 mm), so both MX and Choc switches fit. The outer column sits on a break-off tab for a 36-key variant.
- **Switches:** a combined footprint that takes either a Kailh MX socket or a Kailh Choc socket per key. You choose per build, not per day. First build is MX.
- **Assembled by JLCPCB:** the diodes only, all on one face, basic-library part.
- **Soldered by hand:** hot-swap sockets, controller sockets, power switch, reset button, battery connector, battery. Sockets cannot be factory-fitted on a reversible board (see PCB architecture).
- **Controller:** Pro Micro-footprint nRF52840 board (nice!nano v2 or a cheap SuperMini clone), socketed, on a solder-jumper reversible footprint.
- **Display:** nice!view footprint reserved in v1.
- **Firmware:** ZMK. Wiring the matrix to the same pins as the stock Corne means the existing ZMK `corne` shield works unmodified.
- **Case:** 3D printed tray and plate, mirrored in the slicer for the right half, with separate plate files for MX and Choc.

Five boards give two complete keyboards (for example one MX, one Choc) plus a spare.

## How the design meets each criterion

| Criterion | Design answer | Caveat |
| --- | --- | --- |
| One PCB for left and right | Reversible board; every footprint works from both faces | Hot-swap sockets must be hand-soldered |
| JLCPCB standard parts | Only SOD-123 diodes are factory-fitted, and 1N4148W (C81598) is a basic part | Power switch, reset and battery connector are hand-soldered |
| Expensive parts self-mounted | Controller, sockets and battery are bought separately and fitted by hand | About 130 easy solder joints per half, plus the controller jumpers |
| ZMK | nRF52840 controller; stock `corne` shield | None |
| 3D printer | Printed case, plate and optional tenting feet | Choc plate needs small pockets over the diodes |
| Choc and MX | Dual-socket footprint at MX spacing | Choc keycaps sit with wider gaps than on a native Choc board |
| Corne layout | 3x6+3, Corne pin assignment | Board is larger than 100x100 mm, so not JLCPCB's cheapest size tier |

## Reversible PCB architecture

The board is a 2-layer, 1.6 mm PCB that is used face-up for the left hand and flipped for the right. Call the faces A and B: on the left half A is the underside, on the right half A is the top.

**What reversibility forces**

- **Sockets go on the underside of each half**, which is face A on one board and face B on the other. A factory run places parts on the same face of every board, and a socket on the top face would block the switch. So sockets are hand-soldered.
- **Factory-fitted parts all go on face A**, so on the right half they end up on the top, between the switches. Every such part must therefore sit where it clears switch bodies and the plate.
- **The controller footprint is mirrored when the board flips.** See controller mirroring below.

**Diode placement.** Put each diode in the gap between vertically adjacent keys in the same column, long axis across the column. At 19.05 mm pitch that gap is about 3.4 mm for MX housings and about 4 mm for Choc, and a SOD-123 body is 1.6 mm wide. Check this against the footprint's courtyard before routing.

**Controller mirroring (decided: solder jumpers).** Each controller hole is wired to a pair of small pads on each face. One face's pads connect the hole to its left-hand signal, the other face's pads to its right-hand signal. On each half, bridge only the pads on the face pointing up.

- The controller sits face-up on both halves, and the right case is a true mirror of the left.
- Cost: about 25 extra solder blobs per half and a denser footprint to route.
- Risk: bridging pads on both faces of one board shorts signals together, including battery to ground.
- The nice!view header uses the same jumper scheme.

The alternative that was rejected: a single plain footprint with the controller mounted face-down on one half. It needs no jumpers, but the halves differ and the case is not a pure mirror.

Include the two battery holes next to the USB end in the footprint, and confirm the pinout of the exact controller bought before sending the board to fab.

**Parts that work from either face.** Use a side-actuated slide switch for power and a right-angle tactile button for reset, both at the board edge, with footprints on both faces so they can be hand-soldered on whichever face is the underside.

**36-key break-off.** The outer column of each half sits on a tab with mouse-bite perforations. That column's three diodes sit on the tab, and only the one column trace crosses the break line. Firmware uses the 5-column Corne layout when the tab is removed.

**Prior art to copy from, not redraw**

- [daprice keyswitch footprints](https://github.com/chgray/daprice-keyswitches): KiCad `Kailh_socket_MX_reversible` and `Kailh_socket_PG1350_reversible` footprints.
- [ezxzeng/sweep_squared_rot](https://github.com/ezxzeng/sweep_squared_rot): Ergogen `key_switches.js` footprint that combines MX, Choc and Gateron low-profile sockets on a reversible board.
- The original Corne (crkbd) and Lily58 are open-source reversible designs. The Lily58 Pro footprint is believed to accept both MX and Choc sockets; verify before relying on it.

## Switch footprint: Choc and MX on the same board

Each key position carries pads for a Kailh MX socket and a Kailh Choc socket, on both faces, and one socket type is soldered per key.

- **Spacing is MX (19.05 x 19.05 mm).** Native Choc spacing is 18 x 17 mm, so a board cannot be optimal for both. MX spacing is the only one where both switch types physically fit.
- **Choc V1 and V2.** Use a Choc footprint with the larger centre hole so V2 switches fit too. V2 takes MX-stem keycaps, which suits MX spacing well.
- **The swap is per build.** Moving a finished half from MX to Choc means desoldering 21 sockets and printing a different plate and case. Building the second pair of boards for the other switch type is easier.
- **This footprint is the main technical risk.** Four socket positions per key (two types, two faces) leave little room for pads, holes and traces. Take a proven footprint from the prior art above, then print the PCB 1:1 on paper and test-fit both socket types and both switch types before ordering.

**Plate heights for the case**

| | MX | Choc V1 |
| --- | --- | --- |
| Plate cutout | 14.0 x 14.0 mm | 13.8 x 13.8 mm |
| Plate thickness at the clip | 1.5 mm | 1.2 to 1.3 mm |
| PCB top to plate top | 5.0 mm | 2.2 mm |

The Choc plate underside is under 1 mm above the PCB, and a SOD-123 diode is about 1.1 mm tall. On the half where diodes face up, the printed Choc plate needs a shallow pocket over each diode, or run Choc plateless.

## Electronics and BOM

The board itself is nearly passive: a 4x6 diode matrix, a power switch, a reset button, a battery connector and a display header. Everything active lives on the controller module.

**Fitted by JLCPCB (face A, Economic PCBA)**

| Part | Qty per board | Package | JLCPCB library |
| --- | --- | --- | --- |
| 1N4148W diode | 21 | SOD-123 | Basic, [C81598](https://jlcpcb.com/partdetail/ST_Semtech-1N4148W/C81598) |

With only a basic part on the order there are no extended-part fees.

**Fitted by hand**

| Part | Qty per keyboard | Note |
| --- | --- | --- |
| Kailh MX socket (CPG151101S11) or Choc socket (CPG135001S30) | 42 | LCSC lists them as C2803348 (MX) and C5333465 (Choc); also sold by keyboard shops |
| nRF52840 controller, Pro Micro footprint | 2 | See controller options |
| Low-profile machine-pin sockets and pins | 2 sets | Keeps the controller removable and reusable |
| Power slide switch, side-actuated | 2 | Through-hole or large-pad footprint, both faces |
| Reset button, right-angle tactile | 2 | Through-hole or large-pad footprint, both faces |
| Battery connector, JST PH 2-pin | 2 | Through-hole or large-pad footprint, both faces |
| 1S LiPo battery with JST PH lead | 2 | 100 to 300 mAh, sized to fit under or beside the controller |
| nice!view display (optional) | 2 | Header reserved in v1 |
| Switches and keycaps | 42 | MX first; Choc V1 or V2 on a later build |

**Deliberately left out of v1:** RGB LEDs, encoders and a TRRS jack. The halves talk over Bluetooth, so no cable or jack is needed.

**nice!view header.** Place it where the Corne's OLED header sits and route chip-select to the pin the ZMK `nice_view_adapter` expects, so the stock adapter shield works. Verify the adapter pinout in the ZMK repo before routing.

LCSC part numbers and basic or extended status change; confirm each one in the JLCPCB parts library on the day of ordering.

## Controller options

Use a Pro Micro-footprint nRF52840 board: it is what ZMK's Corne shield targets, and it has enough pins for the 10-line matrix plus the display.

| Controller | Approx. price each | ZMK board | Note |
| --- | --- | --- | --- |
| SuperMini nRF52840 (AliExpress) | 4 to 6 EUR | `nice_nano` | Cheapest; quality varies by seller, and sleep current is usually higher |
| nice!nano v2 | 21 to 25 EUR | `nice_nano` | The reference ZMK controller; available from EU shops |
| Seeed XIAO nRF52840 | 10 to 12 EUR | `xiao_ble` | Different, smaller footprint with too few pins for a 42-key matrix plus display; not recommended here |

Start with two SuperMini boards for bring-up. Because they are socketed, nice!nano boards can be swapped in later without touching the PCB.

Sources: [ZMK supported hardware](https://zmk.dev/docs/hardware), [nRFMicro wiki controller list](https://github.com/joric/nrfmicro/wiki). Prices are approximate.

## ZMK firmware

Wire the matrix exactly like the original Corne and no custom firmware is needed: ZMK's in-tree `corne_left` and `corne_right` shields build as-is.

- **Pin assignment.** Copy rows, columns and diode direction from `corne.dtsi` in the ZMK repository (`app/boards/shields/corne`). The right half uses the same pins in reversed column order, which is what a flipped reversible board gives.
- **Config.** Keep a ZMK config (from the ZMK template) under `firmware/` or in a separate `zmk-config` repo. GitHub Actions builds two `.uf2` files on every push.
- **Board name.** Since ZMK moved to Zephyr 4.1, the nice!nano v2 and its clones are [`nice_nano//zmk`](https://zmk.dev/blog/2025/12/09/zephyr-4-1) rather than `nice_nano_v2`. Older tutorials use the old name.
- **Flashing.** Double-tap reset, the controller mounts as a USB drive, drop the `.uf2` on it. The left half is the central and pairs with the computer; the right half pairs with the left.
- **Keymap editing.** Enable ZMK Studio on the left half to change the keymap live over USB without rebuilding.

```yaml
# build.yaml
include:
  - board: nice_nano//zmk
    shield: corne_left
    snippet: studio-rpc-usb-uart
    cmake-args: -DCONFIG_ZMK_STUDIO=y
  - board: nice_nano//zmk
    shield: corne_right
```

When the display is fitted, add `nice_view_adapter nice_view` to each shield line. If the layout changes later, copy the Corne shield into the config as a custom shield and edit it there.

## 3D printed case and plate

Design one left-hand case and mirror it in the slicer for the right hand; only the plate differs between MX and Choc builds.

- **Parts per half:** bottom tray, switch plate, optional controller cover, optional tenting feet.
- **Source geometry:** export the board outline, switch positions and mounting holes from the PCB (Ergogen outputs these directly, or export DXF/STEP from KiCad) so case and PCB cannot drift apart.
- **Tray depth under the PCB:** at least 2.5 mm for sockets and diodes, more where the battery sits. Put the battery under the controller area or in a pocket beside it.
- **Fasteners:** M2 screws into heat-set inserts, 5 mounting holes per half, placed so they work on both faces and with the outer column broken off.
- **Plate:** print flat on the bed, 0.2 mm layers. MX plate 1.5 mm at the cutouts; Choc plate 1.2 to 1.3 mm with diode pockets on the underside.
- **Edge openings:** USB-C, power switch and reset button.
- **Variants:** 42-key and 36-key trays and plates.
- **Material:** PETG for the tray, PLA or PETG for the plate. Print one test plate with three cutouts first to tune switch fit on the printer.

## Cost estimate

One complete keyboard with clone controllers should land around 80 to 130 EUR, most of it switches and keycaps. All figures are approximate and from memory, before shipping and Finnish import VAT; get a live JLCPCB quote before deciding.

| Item | Approx. cost (EUR) |
| --- | --- |
| 5 PCBs, 2-layer, about 135 x 95 mm | 8 to 15 |
| Economic PCBA on 5 boards: setup, stencil, diodes | 10 to 15 |
| 2 controllers (SuperMini clones; nice!nano v2 would be 42 to 50) | 8 to 12 |
| 50 hot-swap sockets | 7 to 10 |
| 2 batteries, switches, buttons, connectors, pin sockets, screws, inserts, filament | 15 to 22 |
| 42 switches and a keycap set | 30 to 60 |

The second keyboard from the same PCB order costs only the controllers, sockets, batteries, switches and keycaps.

## Build plan

Seven steps, with the cheap checks placed before the PCB order because a footprint mistake costs a full re-order and two to three weeks.

1. **Order long-lead parts now.** Two SuperMini controllers, a few MX and Choc sockets, batteries. They are needed in hand to test-fit.
2. **Generate the layout.** Describe the Corne 3x6+3 geometry in Ergogen (or start from the open-source Corne KiCad files) with the combined reversible switch footprint, face-A diodes, the jumper controller footprint, the display header and the break-off tab.
3. **Route in KiCad.** Matrix nets on Corne pin assignments, battery through the power switch to the controller battery pin, reset button. Run DRC against JLCPCB's 2-layer rules.
4. **Paper and firmware check.** Print the board 1:1 and test-fit sockets, switches and the controller on both faces. Flash stock Corne ZMK to the two bare controllers and confirm they pair with each other and with the computer.
5. **Order from JLCPCB.** 5 boards, Economic PCBA on face A. Export Gerbers, BOM and placement files with the KiCad JLCPCB fabrication plugin and check part rotation in JLCPCB's preview.
6. **Print and assemble.** While boards ship, print the test plate, then tray and plate. On arrival: bridge the jumpers on the upward face of each half, solder sockets to the underside, fit controller sockets, power switch, reset and battery connector, connect the battery, mount in the case.
7. **Bring-up.** Flash left and right, test every key with a tweezers short before fitting switches, then load the keymap through ZMK Studio.

Steps 1 to 4 are a few evenings; JLCPCB production and shipping to Finland typically adds two to three weeks.

## Risks

- **Combined reversible footprint does not fit.** Mitigation: reuse a proven footprint and do the paper test. Fallback: drop to a single switch type per PCB revision.
- **Top-facing diodes foul the Choc plate.** Mitigation: plate pockets or plateless Choc. Fallback: use both-face diode pads and hand-solder the diodes on one half.
- **Clone controller pinout or battery pins differ from the nice!nano.** Mitigation: buy controllers first and measure before finalising the footprint.
- **Jumpers bridged on the wrong face or on both faces.** Mitigation: clear silkscreen on each face saying which half bridges there; check for shorts with a multimeter before connecting a battery.
- **Part rotation errors in JLCPCB placement.** Diodes fitted backwards disable a whole half. Check every diode's polarity mark in the order preview.
- **Not verified:** current JLCPCB fees, part stock and basic or extended status, the Lily58 Pro footprint claim, and the nice!view adapter pinout. Dimensions and prices are from memory.

## Decisions (15 Nov 2026)

- First build is MX.
- 36-key variant on the same board with break-off tabs.
- nice!view display footprint reserved in v1.
- Solder-jumper controller footprint.
- Power switch, reset button and battery connector are hand-soldered; JLCPCB fits only the diodes.

## Sources

- [ZMK supported hardware](https://zmk.dev/docs/hardware)
- [ZMK blog: Zephyr 4.1 board renames](https://zmk.dev/blog/2025/12/09/zephyr-4-1)
- [JLCPCB part C81598, 1N4148W](https://jlcpcb.com/partdetail/ST_Semtech-1N4148W/C81598)
- [nRFMicro wiki: nRF52840 controller list](https://github.com/joric/nrfmicro/wiki)
- [Kailh Choc socket, LCSC C5333465](https://www.flux.ai/whitelynx/kailh-choc-hot-swap-socket.md)
- [daprice keyswitch footprints (reversible sockets)](https://github.com/chgray/daprice-keyswitches)
- [ezxzeng/sweep_squared_rot (combined MX and Choc Ergogen footprint)](https://github.com/ezxzeng/sweep_squared_rot)
