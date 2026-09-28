# Auto-analysis run 20260922-165229_141376

- **status**: done (56.55 s)
- **input**: `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/uploads/20260922-161902_913709_clip_frames`
- **detected**: frames_folder (modality guess: video frame)
- **recipe**: video_frames_medsam - video -> 5 evenly spaced frames -> MedSAM box -> per-frame CSV + overlays
- **started**: 2026-09-22 16:52:29

## Detection

- 588 video frames: 5 evenly spaced frames are analysed (MedSAM box)

## Steps

| # | step | agent.tool | status | time | key numbers |
|---|---|---|---|---|---|
| 0 | MedSAM box frame_00001.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=179198; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.614; timing_seconds.image_embedding=0.963; timing_seconds.box_decoding=0.007 |
| 1 | MedSAM box frame_00148.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=94143; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.346; timing_seconds.image_embedding=0.931; timing_seconds.box_decoding=0.01 |
| 2 | MedSAM box frame_00295.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=130629; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.343; timing_seconds.image_embedding=0.947; timing_seconds.box_decoding=0.009 |
| 3 | MedSAM box frame_00441.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=165463; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.348; timing_seconds.image_embedding=0.923; timing_seconds.box_decoding=0.009 |
| 4 | MedSAM box frame_00588.png | `MedSAM.medsam_segment_with_box` | done | 2.0 | n_boxes=1; total_foreground_pixels=129299; device=cuda:0; input_kind=image; boxes_source=argument; timing_seconds.model_load=0.352; timing_seconds.image_embedding=0.935; timing_seconds.box_decoding=0.008 |
| 5 | per-frame CSV + overlay gallery | `auto.auto_frames_table` | done | 0.0 | n_frames=5; n_done=5; mean_per_frame=1.397e+05; metric=foreground_pixels |
| 6 | literature context (MedKG related work) | `MedKG.medkg_related_work` | done | 46.53 | summary.n_rows=10; summary.n_q1=10; summary.status=ok; summary.llm.provider=codex; summary.llm.model=gpt-6-astra; summary.llm.elapsed_s=45.67; summary.llm.fallback_used=False; summary.timing.total_ms=4.616e+04 |

## Artifacts

### step 0 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165229_ee158ac5/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165229_ee158ac5/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165229_ee158ac5/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165229_ee158ac5/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 1 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165231_2c081ea0/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165231_2c081ea0/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165231_2c081ea0/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165231_2c081ea0/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 2 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165233_3e0315c9/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165233_3e0315c9/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165233_3e0315c9/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165233_3e0315c9/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 3 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165235_cc767ce7/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165235_cc767ce7/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165235_cc767ce7/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165235_cc767ce7/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 4 - MedSAM.medsam_segment_with_box
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165237_0495888c/segs.npz` - Label map npz: 'segs' uint8 (H,W) with label i+1 for box i (later boxes overwrite), 'boxes' int64 (N,4)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165237_0495888c/segs.png` - Label map PNG (uint8 label values 0..N)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165237_0495888c/seg_box_01.png` - Binary mask (values 0/1) for box 1 [72, 58, 648, 518]
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/outputs/medsam_segment_with_box_20260922-165237_0495888c/overlay.png` - Overlay figure: input image with boxes (left), MedSAM masks with boxes (right)

### step 5 - auto.auto_frames_table
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/frames.csv` - per-frame results (CSV)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/overlays/00_frame_00001_overlay.png` - overlay for frame_00001.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/overlays/01_frame_00148_overlay.png` - overlay for frame_00148.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/overlays/02_frame_00295_overlay.png` - overlay for frame_00295.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/overlays/03_frame_00441_overlay.png` - overlay for frame_00441.png
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/overlays/04_frame_00588_overlay.png` - overlay for frame_00588.png

### step 6 - MedKG.medkg_related_work
- `/media/jerisuh/4,0TBDisk/MedKG/data/mcp_outputs/related_work_20260922-165325-3b52af.json` - related_work — full JSON response
- `/media/jerisuh/4,0TBDisk/MedKG/data/mcp_outputs/related_work_20260922-165325-3b52af.md` - related_work — markdown

### run

- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/summary.json` - run summary (JSON)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/report.md` - run report (markdown)
- `/media/jerisuh/4,0TBDisk/Paper2Agent_webapp/data/auto_runs/20260922-165229_141376/frames.csv` - per-frame results (CSV)
