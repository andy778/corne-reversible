# firmware

ZMK config for the reversible Corne. Stock `corne_left` / `corne_right` shields, unmodified; the PCB uses the stock Corne pin map.

## Files

| File | Purpose |
| --- | --- |
| `build.yaml` | Build matrix: one entry per `.uf2`. Commented nice!view and settings_reset entries. |
| `west.yml` | Pins ZMK (main, Zephyr 4.1) to a commit. |
| `corne.keymap` | 42-key, 4-layer starter keymap. |
| `corne.conf` | Shared Kconfig: sleep, battery, Studio locking. |

The config sits directly in `firmware/`, not `firmware/config/`. The reusable workflow runs `west init -l <config_path>`, and the west topdir is the parent of that path, so a nested config breaks the build. The repo root becomes the topdir in CI.

## CI

`.github/workflows/build-firmware.yml` calls `zmkfirmware/zmk/.github/workflows/build-user-config.yml` with `build_matrix_path: firmware/build.yaml` and `config_path: firmware`. Runs on push or PR touching `firmware/**`, and on manual dispatch.

Artifacts (from the run's summary page):

- `artifact-corne_left` containing `corne_left.uf2` (central, Studio on)
- `artifact-corne_right` containing `corne_right.uf2`
- `corne-firmware` merged archive with both

Pinning: `west.yml` and the workflow `uses:` ref point to the same ZMK commit. The latest release tag `v0.3.0` (Zephyr 3.5) does not have `nice_nano//zmk`. Move both to a release once ZMK ships one with Zephyr 4.1.

## Flashing

1. Double-tap the reset button on the controller. A USB drive appears (nice!nano shows as `NICENANO`; clones may differ).
2. Copy the `.uf2` onto it. The board reboots and the drive disappears.
3. Left half pairs with the computer over BLE. Flash the right half too; it pairs with the left.

Pairing reset: flash `settings_reset` (uncomment in `build.yaml`) to a half that will not pair, then flash the normal firmware again.

## Studio

ZMK Studio is on the left half only (`studio-rpc-usb-uart` snippet plus `-DCONFIG_ZMK_STUDIO=y`). It talks over USB.

Locking is on (`CONFIG_ZMK_STUDIO_LOCKING=y`), so press `&studio_unlock` (top-left of the adjust layer) before editing. The lock also re-engages on disconnect.

## Host layout: Finnish/Swedish

The keymap assumes the computer is set to the Finnish or Swedish (ISO) keyboard layout. `corne.keymap` defines `FI_*` names for the key positions that produce each character under that layout.

- Base layer: Å Ä Ö sit right of P and L, `-` replaces `/`, Backspace moves to the right thumb (Alt is on that thumb in Lower and Raise).
- Raise: € (AltGr+E) and the Nordic symbol positions. `^`, `~` and `` ` `` are dead keys on this layout, so they are macros that add a space.
- With the host on US layout every symbol on Raise and the Nordic letters will be wrong.

## Layers

| # | Name | Reach |
| --- | --- | --- |
| 0 | Default | - |
| 1 | Lower | Left thumb (`&mo 1`) |
| 2 | Raise | Right thumb (`&mo 2`) |
| 3 | Adjust | Lower held + bottom-left key (`&mo 3`) |

Adjust: BT_SEL 0-4, BT_PRV/NXT, BT_CLR (current profile), BT_CLR_ALL (all bonds), OUT_USB / OUT_BLE / OUT_TOG, bootloader, sys_reset, studio_unlock.

## 36-key (outer column removed)

Only after the break-off tab is snapped off on the PCB.

1. In `corne.keymap`, add near the top, after the includes:

   ```dts
   / { chosen { zmk,physical-layout = &foostan_corne_5col_layout; }; };
   ```

   The 5-column transform is already defined in `corne.dtsi`, so the shields need no change.
2. Drop the first and last key of each of the three main rows in every layer. Thumbs stay. That is 10 + 10 + 10 + 6 = 36 bindings per layer, or ZMK rejects the keymap.

## nice!view (not fitted in v1)

1. In `build.yaml`, uncomment the nice_view entries. Shield order is `corne_left nice_view_adapter nice_view`; the adapter must come first.
2. In `corne.conf`, uncomment `CONFIG_ZMK_DISPLAY=y`.
3. The adapter puts the nice!view CS on `&pro_micro 1` (D1). Route that pin on the PCB, or override `cs-gpios` in a custom overlay.

Not built or tested yet.

## Local build (optional)

Requires the ZMK dev environment (`west`, Zephyr SDK) or the `zmkfirmware/zmk-build-arm` container. From the repo root:

```bash
west init -l firmware
west update
west build -s zmk/app -b nice_nano//zmk -d build/left -S studio-rpc-usb-uart \
  -- -DZMK_CONFIG=$PWD/firmware -DSHIELD=corne_left -DCONFIG_ZMK_STUDIO=y
```

`zmk/`, `zephyr/` and friends are created in the repo root. The root `.gitignore` does not cover them, so keep them out of commits.
