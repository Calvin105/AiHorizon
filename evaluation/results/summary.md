# Evaluation — 2026-10-02 03:59

Ran in 65.3s. All images synthetic (vision/synth), all operator answers simulated (evaluation/scenarios.py, team judgement). No API, no database, no LLM.

## A. Measurement — does the photo raise the right signal?

40 images per condition, spread over 4 dispense patterns.

**Missed** = the defect's signal didn't fire, so ranking leans on the interview. **False alarm** = a signal fired that the image doesn't contain — the outcome that misleads.

| Condition | Correct | Refused | Missed | False alarm | Correct means |
|---|---|---|---|---|---|
| good | 100% | 0% | 0% | 0% | no alarm: spread in spec, nothing missing, no irregular deposits, no carryover |
| carryover | 52% | 0% | 48% | 0% | small-then-big pattern found above chance (p < 0.05) |
| scatter | 100% | 0% | 0% | 0% | size spread out of spec, and NO false carryover pattern |
| missing_dots | 100% | 0% | 0% | 0% | missing deposits counted, and NO false carryover pattern |
| irregular_shape | 100% | 0% | 0% | 0% | irregular deposits counted (the blockage rule's trigger) |

Correct, by dispense pattern:

| Condition | area | grid_landmark | perimeter | pattern |
|---|---|---|---|---|
| good | 100% | 100% | 100% | 100% |
| carryover | 70% | 70% | 70% | 0% |
| scatter | 100% | 100% | 100% | 100% |
| missing_dots | 100% | 100% | 100% | 100% |
| irregular_shape | 100% | 100% | 100% | 100% |

## B. Diagnosis — is the top cause right?

60 simulated cases per cause x 7 causes. *Reliability* = chance each answer comes from the scenario card rather than a random guess.

| Evidence given | Top-1 | In top 3 | 'No cause ahead' | Top-1 when it named one | Brier (lower=better) |
|---|---|---|---|---|---|
| questions_only@1.0 | 71% | 94% | 4% | 74% | 0.0783 |
| questions_only@0.75 | 54% | 81% | 3% | 56% | 0.1002 |
| questions_only@0.5 | 40% | 75% | 3% | 42% | 0.1114 |
| photo_only | 36% | 47% | 38% | 58% | 0.1093 |
| photo_and_questions@1.0 | 80% | 94% | 1% | 82% | 0.0762 |
| photo_and_questions@0.75 | 66% | 87% | 1% | 67% | 0.0959 |
| photo_and_questions@0.5 | 57% | 84% | 1% | 58% | 0.1049 |

Chance level for top-1 is 14% (1 in 7).

### Per cause (photo + questions, reliability 0.75)

| True cause | Top-1 | In top 3 | 'No cause ahead' |
|---|---|---|---|
| volume_too_small_carryover | 58% | 78% | 2% |
| pressure_time_instability | 93% | 100% | 0% |
| air_in_fluid_path | 83% | 98% | 0% |
| material_rheology_change | 82% | 95% | 0% |
| nozzle_blockage | 77% | 100% | 0% |
| dispense_height_or_board_bending | 37% | 67% | 5% |
| equipment_condition | 33% | 70% | 3% |

### What it picked instead (photo + questions, reliability 0.75)

- **volume_too_small_carryover** → volume_too_small_carryover 35, pressure_time_instability 18, air_in_fluid_path 3, dispense_height_or_board_bending 2, nozzle_blockage 1, (no cause ahead) 1
- **pressure_time_instability** → pressure_time_instability 56, air_in_fluid_path 2, volume_too_small_carryover 1, material_rheology_change 1
- **air_in_fluid_path** → air_in_fluid_path 50, material_rheology_change 4, pressure_time_instability 3, dispense_height_or_board_bending 1, equipment_condition 1, volume_too_small_carryover 1
- **material_rheology_change** → material_rheology_change 49, air_in_fluid_path 7, nozzle_blockage 2, dispense_height_or_board_bending 1, volume_too_small_carryover 1
- **nozzle_blockage** → nozzle_blockage 46, air_in_fluid_path 6, material_rheology_change 6, pressure_time_instability 1, dispense_height_or_board_bending 1
- **dispense_height_or_board_bending** → pressure_time_instability 28, dispense_height_or_board_bending 22, equipment_condition 4, (no cause ahead) 3, air_in_fluid_path 2, nozzle_blockage 1
- **equipment_condition** → equipment_condition 20, pressure_time_instability 17, material_rheology_change 10, air_in_fluid_path 5, dispense_height_or_board_bending 3, nozzle_blockage 2, (no cause ahead) 2, volume_too_small_carryover 1

### Calibration — when it is confident, is it right? (photo + questions, all reliabilities)

| Stars shown | Cases | Top-1 accuracy |
|---|---|---|
| 0 | 23 | 26% |
| ★ | 522 | 52% |
| ★★ | 429 | 75% |
| ★★★ | 210 | 95% |
| ★★★★ | 58 | 97% |

| Top cause shown at | Cases | Mean shown | Actually right |
|---|---|---|---|
| 0-40% | 209 | 35% | 46% |
| 40-55% | 172 | 49% | 60% |
| 55-70% | 358 | 62% | 63% |
| 70-85% | 284 | 76% | 76% |
| 85-100% | 219 | 91% | 98% |

## C. Stress — damaged photos

20 images per condition per level, all 5 measurement conditions. Compare each row with the **undamaged** row: that gap is what the damage cost. Refusing is the safe failure; a rise in false alarms is the unsafe one.

| Damage | Level | Correct | Refused | Missed | False alarm |
|---|---|---|---|---|---|
| **undamaged** | — | 89% | 0% | 11% | 0% |
| blur | 1 sigma px | 89% | 0% | 11% | 0% |
| blur | 2 sigma px | 89% | 0% | 11% | 0% |
| blur | 4 sigma px | 79% | 0% | 21% | 0% |
| blur | 7 sigma px | 68% | 0% | 32% | 0% |
| noise | 8 sigma grey levels | 89% | 0% | 11% | 0% |
| noise | 16 sigma grey levels | 89% | 0% | 11% | 0% |
| noise | 32 sigma grey levels | 89% | 0% | 11% | 0% |
| noise | 56 sigma grey levels | 89% | 0% | 11% | 0% |
| uneven_light | 30 grey levels edge to edge | 89% | 0% | 11% | 0% |
| uneven_light | 60 grey levels edge to edge | 89% | 0% | 11% | 0% |
| uneven_light | 110 grey levels edge to edge | 89% | 0% | 11% | 0% |
| uneven_light | 170 grey levels edge to edge | 89% | 0% | 11% | 0% |
| glare | 40 peak grey levels | 89% | 0% | 11% | 0% |
| glare | 80 peak grey levels | 89% | 0% | 11% | 0% |
| glare | 130 peak grey levels | 14% | 82% | 4% | 0% |
| glare | 180 peak grey levels | 1% | 97% | 2% | 0% |
| low_contrast | 0.6 contrast kept | 89% | 0% | 11% | 0% |
| low_contrast | 0.4 contrast kept | 89% | 0% | 11% | 0% |
| low_contrast | 0.25 contrast kept | 89% | 0% | 11% | 0% |
| low_contrast | 0.12 contrast kept | 89% | 0% | 11% | 0% |
| jpeg | 60 quality | 89% | 0% | 11% | 0% |
| jpeg | 35 quality | 89% | 0% | 11% | 0% |
| jpeg | 15 quality | 89% | 0% | 11% | 0% |
| jpeg | 5 quality | 89% | 0% | 11% | 0% |
| rotate | 1 degrees | 89% | 0% | 11% | 0% |
| rotate | 2 degrees | 89% | 0% | 11% | 0% |
| rotate | 4 degrees | 89% | 0% | 11% | 0% |
| rotate | 8 degrees | 89% | 0% | 11% | 0% |
| shift | 5 px | 89% | 0% | 11% | 0% |
| shift | 12 px | 89% | 0% | 11% | 0% |
| shift | 25 px | 89% | 0% | 11% | 0% |
| shift | 50 px | 89% | 0% | 11% | 0% |
| low_resolution | 0.5 of full resolution | 89% | 0% | 11% | 0% |
| low_resolution | 0.3 of full resolution | 89% | 0% | 11% | 0% |
| low_resolution | 0.2 of full resolution | 89% | 0% | 11% | 0% |
| low_resolution | 0.12 of full resolution | 83% | 0% | 17% | 0% |
| board_clutter | 5 pads/traces | 65% | 18% | 9% | 8% |
| board_clutter | 15 pads/traces | 29% | 57% | 5% | 9% |
| board_clutter | 30 pads/traces | 6% | 91% | 2% | 1% |
| board_clutter | 60 pads/traces | 3% | 97% | 0% | 0% |
| phone_photo | 1 combined level | 89% | 0% | 11% | 0% |
| phone_photo | 2 combined level | 89% | 0% | 11% | 0% |
| phone_photo | 3 combined level | 89% | 0% | 11% | 0% |
| phone_photo | 4 combined level | 89% | 0% | 11% | 0% |
| zoom | 0.6 x scale | 89% | 0% | 11% | 0% |
| zoom | 0.8 x scale | 89% | 0% | 11% | 0% |
| zoom | 1.25 x scale | 89% | 0% | 11% | 0% |
| zoom | 1.6 x scale | 89% | 0% | 11% | 0% |
| reframe | 50 px off-centre | 89% | 0% | 11% | 0% |
| reframe | 100 px off-centre | 89% | 0% | 11% | 0% |
| reframe | 200 px off-centre | 89% | 0% | 11% | 0% |
| reframe | 300 px off-centre | 89% | 0% | 11% | 0% |
| handheld | 1 combined level | 89% | 0% | 11% | 0% |
| handheld | 2 combined level | 89% | 0% | 11% | 0% |
| handheld | 3 combined level | 89% | 0% | 11% | 0% |
| handheld | 4 combined level | 89% | 0% | 11% | 0% |
| on_desk | 0 x 3% camera tilt | 89% | 0% | 11% | 0% |
| on_desk | 1 x 3% camera tilt | 89% | 0% | 11% | 0% |
| on_desk | 2 x 3% camera tilt | 89% | 0% | 11% | 0% |
| on_desk | 3 x 3% camera tilt | 89% | 0% | 11% | 0% |
