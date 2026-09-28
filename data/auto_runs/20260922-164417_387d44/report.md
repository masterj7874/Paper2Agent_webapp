# Auto-analysis run 20260922-164417_387d44

- **status**: partial (96.15 s)
- **input**: `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/uploads/20260922-161902_913709_clip_frames`
- **detected**: frames_folder (modality guess: video frame)
- **recipe**: video_frames_medsam - video -> 5 evenly spaced frames -> MedSAM box -> per-frame CSV + overlays
- **started**: 2026-09-22 16:44:17

## Detection

- 588 video frames: 5 evenly spaced frames are analysed (MedSAM box)

## Steps

| # | step | agent.tool | status | time | key numbers |
|---|---|---|---|---|---|
| 0 | MedSAM box frame_00001.png | `MedSAM.medsam_segment_with_box` | done | 3.51 | n_boxes=1; total_foreground_pixels=179198; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.732; timing_seconds.image_embedding=1.299; timing_seconds.box_decoding=0.122 |
| 1 | MedSAM box frame_00148.png | `MedSAM.medsam_segment_with_box` | done | 2.51 | n_boxes=1; total_foreground_pixels=94143; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.853; timing_seconds.image_embedding=1.02; timing_seconds.box_decoding=0.01 |
| 2 | MedSAM box frame_00295.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=130629; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.51; timing_seconds.image_embedding=0.975; timing_seconds.box_decoding=0.009 |
| 3 | MedSAM box frame_00441.png | `MedSAM.medsam_segment_with_box` | done | 2.03 | n_boxes=1; total_foreground_pixels=165463; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.377; timing_seconds.image_embedding=0.981; timing_seconds.box_decoding=0.009 |
| 4 | MedSAM box frame_00588.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=129299; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.367; timing_seconds.image_embedding=0.967; timing_seconds.box_decoding=0.008 |
| 5 | per-frame CSV + overlay gallery | `auto.auto_frames_table` | done | 0.0 | n_frames=5; n_done=5; mean_per_frame=1.397e+05; metric=foreground_pixels |
| 6 | literature context (MedKG related work) | `MedKG.medkg_related_work` | error - Error calling tool 'medkg_related_work': MedKG service unreachable at http://127.0.0.1:8790 (ConnectError: [Errno 111] Connection refused). Start it with script | 84.09 |  |

## Artifacts

### step 0 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164417_d5bd1074/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164417_d5bd1074/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164417_d5bd1074/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164417_d5bd1074/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 1 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164420_0c1d241c/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164420_0c1d241c/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164420_0c1d241c/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164420_0c1d241c/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 2 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164423_d7c1d195/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164423_d7c1d195/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164423_d7c1d195/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164423_d7c1d195/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 3 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164425_799fa242/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164425_799fa242/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164425_799fa242/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164425_799fa242/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 4 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164427_7a2432c9/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164427_7a2432c9/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164427_7a2432c9/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/outputs/medsam_segment_with_box_20260922-164427_7a2432c9/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 5 - auto.auto_frames_table
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/frames.csv` - per-frame results (CSV)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/overlays/00_frame_00001_overlay.png` - overlay for frame_00001.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/overlays/01_frame_00148_overlay.png` - overlay for frame_00148.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/overlays/02_frame_00295_overlay.png` - overlay for frame_00295.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/overlays/03_frame_00441_overlay.png` - overlay for frame_00441.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/overlays/04_frame_00588_overlay.png` - overlay for frame_00588.png

### run

- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/summary.json` - run summary (JSON)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/report.md` - run report (markdown)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164417_387d44/frames.csv` - per-frame results (CSV)

## Warnings

- optional step 6 (MedKG.medkg_related_work) failed: Error calling tool 'medkg_related_work': MedKG service unreachable at http://127.0.0.1:8790 (ConnectError: [Errno 111] Connection refused). Start it with scripts/run_service.sh.
