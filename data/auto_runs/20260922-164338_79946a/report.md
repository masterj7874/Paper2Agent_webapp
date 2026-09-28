# Auto-analysis run 20260922-164338_79946a

- **status**: done (79.04 s)
- **input**: `/media/jerisuh/4,0TBDisk/Paper2Agent_out/HDBET_Agent/data/samples/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz`
- **detected**: mri_volume (modality guess: MRI)
- **recipe**: mri_brain_extraction - MRI volume -> HD-BET skull-stripping -> mask QC -> evaluation
- **started**: 2026-09-22 16:43:38

## Detection

- 3-D volume [97, 115, 97] @ [2.0, 2.0, 2.0] mm, int16, intensity [0, 9882]
- no Hounsfield air (< -500) -> MRI-like volume; HD-BET brain extraction (skull-stripping) is applied
- reference brain mask found next to the input (tpl-MNI152NLin2009cAsym_res-02_desc-brain_mask.nii.gz): Dice/IoU/Hausdorff are computed

## Steps

| # | step | agent.tool | status | time | key numbers |
|---|---|---|---|---|---|
| 0 | HD-BET brain extraction | `HDBET.hdbet_extract_brain` | done | 28.01 | n_cases=1; input_mode=file; save_mask=True; save_brain_image=True; timing_s.import_s=2.469; timing_s.maybe_download_parameters_s=0; timing_s.get_hdbet_predictor_s=1.747; timing_s.hdbet_predict_s=18.66 |
| 1 | mask QC (volume, components, overlays) | `HDBET.hdbet_inspect_brain_mask` | done | 2.5 | foreground_voxels=237292; volume_mm3=1.898e+06; foreground_rule=mask != 0; threshold=0.5; mask_is_binary_01=True; mask_n_unique=2; voxel_volume_mm3=8; volume_mL=1898 |
| 2 | Dice/IoU/Hausdorff vs reference mask | `HDBET.hdbet_evaluate_brain_mask` | done | 3.0 | n_cases=1; mean_metrics.Dice=0.9784; mean_metrics.IoU=0.9576; mode=file; hd95_computed=False; mean_metrics.TP=231444; mean_metrics.FP=5848; mean_metrics.FN=4396 |
| 3 | literature context (MedKG related work) | `MedKG.medkg_related_work` | done | 45.52 | summary.n_rows=10; summary.n_q1=10; summary.status=ok; summary.llm.provider=codex; summary.llm.model=gpt-6-astra; summary.llm.elapsed_s=44.54; summary.llm.fallback_used=False; summary.timing.total_ms=4.523e+04 |

## Artifacts

### step 0 - HDBET.hdbet_extract_brain
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_extract_brain_20260922T074340Z_da65b03a/tpl-MNI152NLin2009cAsym_res-02_T1w_bet.nii.gz` - tpl-MNI152NLin2009cAsym_res-02_T1w: binary brain mask (uint8 0/1, input grid)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_extract_brain_20260922T074340Z_da65b03a/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz` - tpl-MNI152NLin2009cAsym_res-02_T1w: skull-stripped image (input voxels inside the mask)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_extract_brain_20260922T074340Z_da65b03a/tpl-MNI152NLin2009cAsym_res-02_T1w_overlay.png` - tpl-MNI152NLin2009cAsym_res-02_T1w: orthogonal QC overlay of the mask contour on the input (PNG)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_extract_brain_20260922T074340Z_da65b03a/hdbet_extract_brain_result.json` - summary JSON of this call (cases, device, model, timing)

### step 1 - HDBET.hdbet_inspect_brain_mask
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_inspect_brain_mask_20260922T074406Z_5cdb66a9/mask_statistics.json` - mask statistics JSON (voxel count, volume, bounding box, value set, components, grid/orientation checks)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_inspect_brain_mask_20260922T074406Z_5cdb66a9/tpl-MNI152NLin2009cAsym_res-02_T1w_bet_overlay.png` - overlay PNG of the slice with the most foreground along array axis 0 (exact nnunetv2 plot_overlay output)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_inspect_brain_mask_20260922T074406Z_5cdb66a9/tpl-MNI152NLin2009cAsym_res-02_T1w_bet_overlay_axis1.png` - overlay PNG along array axis 1 (adaptation: upstream select_slice_to_plot2 + generate_overlay on the moved axis)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_inspect_brain_mask_20260922T074406Z_5cdb66a9/tpl-MNI152NLin2009cAsym_res-02_T1w_bet_overlay_axis2.png` - overlay PNG along array axis 2 (adaptation: upstream select_slice_to_plot2 + generate_overlay on the moved axis)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_inspect_brain_mask_20260922T074406Z_5cdb66a9/plot_overlay_child.stdout.log` - child-process stdout log of the upstream call (captured fd 1; expected 0 bytes)

### step 2 - HDBET.hdbet_evaluate_brain_mask
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/metrics_per_case.csv` - per-case metrics CSV (Dice, IoU, TP/FP/FN/TN, n_pred, n_ref, Hausdorff max/avg mm, volumes)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/summary.json` - summary JSON (settings, per-case metrics, mean metrics, notes, warnings, case details)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/nnunet_metrics.json` - native nnunetv2 output (compute_metrics result)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/binarised/reference` - binarised uint8 reference masks used for evaluation
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/binarised/prediction` - binarised uint8 prediction masks used for evaluation
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/outputs/hdbet_evaluate_brain_mask_20260922T074408Z_421e5e85/logs/child_stdout.log` - captured stdout of the nnunetv2/SimpleITK child process

### step 3 - MedKG.medkg_related_work
- `/media/jerisuh/4,0TBDisk/MedKG/data/mcp_outputs/related_work_20260922-164457-4cdc20.json` - related_work — full JSON response
- `/media/jerisuh/4,0TBDisk/MedKG/data/mcp_outputs/related_work_20260922-164457-4cdc20.md` - related_work — markdown

### run

- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/summary.json` - run summary (JSON)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164338_79946a/report.md` - run report (markdown)
