# Auto-analysis run 20260922-164637_23fdfe

- **status**: partial (60.55 s)
- **input**: `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/uploads/20260922-161902_913709_clip_frames`
- **detected**: frames_folder (modality guess: video frame)
- **recipe**: video_frames_medsam - video -> 5 evenly spaced frames -> MedSAM box -> per-frame CSV + overlays
- **started**: 2026-09-22 16:46:37

## Detection

- 588 video frames: 5 evenly spaced frames are analysed (MedSAM box)

## Steps

| # | step | agent.tool | status | time | key numbers |
|---|---|---|---|---|---|
| 0 | MedSAM box frame_00001.png | `MedSAM.medsam_segment_with_box` | done | 2.01 | n_boxes=1; total_foreground_pixels=179198; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.649; timing_seconds.image_embedding=1.025; timing_seconds.box_decoding=0.013 |
| 1 | MedSAM box frame_00148.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=94143; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.435; timing_seconds.image_embedding=0.97; timing_seconds.box_decoding=0.008 |
| 2 | MedSAM box frame_00295.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=130629; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.348; timing_seconds.image_embedding=0.953; timing_seconds.box_decoding=0.01 |
| 3 | MedSAM box frame_00441.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=165463; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.333; timing_seconds.image_embedding=0.912; timing_seconds.box_decoding=0.008 |
| 4 | MedSAM box frame_00588.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=129299; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.365; timing_seconds.image_embedding=0.965; timing_seconds.box_decoding=0.008 |
| 5 | per-frame CSV + overlay gallery | `auto.auto_frames_table` | done | 0.01 | n_frames=5; n_done=5; mean_per_frame=1.397e+05; metric=foreground_pixels |
| 6 | literature context (MedKG related work) | `MedKG.medkg_related_work` | error - Error calling tool 'medkg_related_work': MedKG service unreachable at http://127.0.0.1:8790 (RemoteProtocolError: Server disconnected without sending a response | 50.52 |  |

## Artifacts

### step 0 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164637_2222a28b/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164637_2222a28b/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164637_2222a28b/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164637_2222a28b/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 1 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164639_5f35c573/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164639_5f35c573/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164639_5f35c573/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164639_5f35c573/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 2 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164641_b09475d2/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164641_b09475d2/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164641_b09475d2/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164641_b09475d2/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 3 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164643_e8936fb6/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164643_e8936fb6/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164643_e8936fb6/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164643_e8936fb6/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 4 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164645_c3e3c809/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164645_c3e3c809/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164645_c3e3c809/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/outputs/medsam_segment_with_box_20260922-164645_c3e3c809/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 5 - auto.auto_frames_table
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/frames.csv` - per-frame results (CSV)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/overlays/00_frame_00001_overlay.png` - overlay for frame_00001.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/overlays/01_frame_00148_overlay.png` - overlay for frame_00148.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/overlays/02_frame_00295_overlay.png` - overlay for frame_00295.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/overlays/03_frame_00441_overlay.png` - overlay for frame_00441.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/overlays/04_frame_00588_overlay.png` - overlay for frame_00588.png

### run

- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/summary.json` - run summary (JSON)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/report.md` - run report (markdown)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-164637_23fdfe/frames.csv` - per-frame results (CSV)

## Warnings

- optional step 6 (MedKG.medkg_related_work) failed: Error calling tool 'medkg_related_work': MedKG service unreachable at http://127.0.0.1:8790 (RemoteProtocolError: Server disconnected without sending a response.). Start it with scripts/run_service.sh.
