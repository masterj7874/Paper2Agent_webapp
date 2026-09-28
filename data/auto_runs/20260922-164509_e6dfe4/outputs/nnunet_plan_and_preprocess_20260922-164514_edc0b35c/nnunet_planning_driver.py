
"""nnunet_planning child driver: upstream nnunetv2 calls + PlansManager summary. Written per call by the MCP tool."""
import json
import os
import sys
import time
import traceback


def _plain(o):
    import numpy as np
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, np.ndarray):
        return _plain(o.tolist())
    if isinstance(o, np.generic):
        return o.item()
    return o


def configuration_summary(cm) -> dict:
    """ConfigurationManager accessors -> plain dict (no recomputation; plans_handler.py at the pinned commit)."""
    arch_kwargs = cm.network_arch_init_kwargs
    raw = cm.configuration
    patch = list(cm.patch_size)
    strides = [list(s) for s in cm.pool_op_kernel_sizes]
    architecture = {
        "network_class_name": cm.network_arch_class_name,
        "n_stages": arch_kwargs.get("n_stages"),
        "features_per_stage": arch_kwargs.get("features_per_stage"),
        "conv_op": arch_kwargs.get("conv_op"),
        "kernel_sizes": arch_kwargs.get("kernel_sizes"),
        "strides": arch_kwargs.get("strides"),
        "n_conv_per_stage_decoder": arch_kwargs.get("n_conv_per_stage_decoder"),
        "conv_bias": arch_kwargs.get("conv_bias"),
        "norm_op": arch_kwargs.get("norm_op"),
        "norm_op_kwargs": arch_kwargs.get("norm_op_kwargs"),
        "dropout_op": arch_kwargs.get("dropout_op"),
        "nonlin": arch_kwargs.get("nonlin"),
        "nonlin_kwargs": arch_kwargs.get("nonlin_kwargs"),
        "_kw_requires_import": list(cm.network_arch_init_kwargs_req_import),
    }
    # PlainConvUNet plans carry n_conv_per_stage, ResidualEncoderUNet plans carry n_blocks_per_stage
    for key in ("n_conv_per_stage", "n_blocks_per_stage"):
        if key in arch_kwargs:
            architecture[key] = arch_kwargs[key]
    return {
        "data_identifier": cm.data_identifier,
        "preprocessor_name": cm.preprocessor_name,
        "batch_size": cm.batch_size,
        "patch_size": patch,
        "spacing": list(cm.spacing),
        "median_image_size_in_voxels": list(cm.median_image_size_in_voxels),
        "normalization_schemes": list(cm.normalization_schemes),
        "use_mask_for_norm": list(cm.use_mask_for_norm),
        "resampling_fn_data": raw.get("resampling_fn_data"),
        "resampling_fn_seg": raw.get("resampling_fn_seg"),
        "resampling_fn_probabilities": raw.get("resampling_fn_probabilities"),
        "architecture": architecture,
        "pool_op_kernel_sizes": strides,
        "batch_dice": cm.batch_dice,
        "previous_stage_name": cm.previous_stage_name,
        "next_stage_names": cm.next_stage_names,
        "inherits_from": raw.get("inherits_from"),
        "patch_voxels": int(__import__("numpy").prod(patch)),
        "n_downsamplings_per_axis": [int(sum(1 for s in strides if s[ax] > 1)) for ax in range(len(patch))],
    }


def plans_summary(plans_file: str) -> dict:
    from nnunetv2.utilities.plans_handling.plans_handler import PlansManager
    pm = PlansManager(plans_file)
    summary = {
        "plans_file": plans_file,
        "dataset_name": pm.dataset_name,
        "plans_name": pm.plans_name,
        "experiment_planner_name": pm.experiment_planner_name,
        "image_reader_writer": pm.plans.get("image_reader_writer"),
        "label_manager": pm.plans.get("label_manager"),
        "transpose_forward": list(pm.transpose_forward),
        "transpose_backward": list(pm.transpose_backward),
        "original_median_spacing_after_transp": list(pm.original_median_spacing_after_transp),
        "original_median_shape_after_transp": list(pm.original_median_shape_after_transp),
        "available_configurations": list(pm.available_configurations),
        "foreground_intensity_properties_per_channel": pm.foreground_intensity_properties_per_channel,
        "configurations": {c: configuration_summary(pm.get_configuration(c)) for c in pm.available_configurations},
    }
    return _plain(summary)


def fingerprint_summary(fingerprint_file: str) -> dict:
    """Descriptive summary of dataset_fingerprint.json (keys as written by DatasetFingerprintExtractor.run)."""
    import numpy as np
    from batchgenerators.utilities.file_and_folder_operations import load_json
    fp = load_json(fingerprint_file)
    spacings = fp.get("spacings", [])
    shapes = fp.get("shapes_after_crop", [])
    out = {
        "fingerprint_file": fingerprint_file,
        "keys": sorted(fp.keys()),
        "n_cases": len(spacings),
        "median_spacing": np.median(np.array(spacings, dtype=float), 0).tolist() if len(spacings) else None,
        "median_shape_after_crop": np.median(np.array(shapes, dtype=float), 0).tolist() if len(shapes) else None,
        "min_shape_after_crop": np.min(np.array(shapes, dtype=float), 0).tolist() if len(shapes) else None,
        "max_shape_after_crop": np.max(np.array(shapes, dtype=float), 0).tolist() if len(shapes) else None,
        "median_relative_size_after_cropping": fp.get("median_relative_size_after_cropping"),
        "foreground_intensity_properties_per_channel": fp.get("foreground_intensity_properties_per_channel"),
    }
    out["n_channels"] = len(out["foreground_intensity_properties_per_channel"] or {})
    return _plain(out)


def preprocessed_folder_counts(folder: str) -> dict:
    names = sorted(n for n in os.listdir(folder) if os.path.isfile(os.path.join(folder, n))) if os.path.isdir(folder) else []
    n_data = sum(1 for n in names if (n.endswith(".b2nd") and not n.endswith("_seg.b2nd")) or (n.endswith(".npz")))
    n_seg = sum(1 for n in names if n.endswith("_seg.b2nd") or n.endswith("_seg.npy"))
    n_pkl = sum(1 for n in names if n.endswith(".pkl"))
    return {"path": folder, "exists": os.path.isdir(folder), "n_files": len(names), "n_cases": n_data,
            "n_seg_files": n_seg, "n_properties_pkl": n_pkl,
            "total_bytes": int(sum(os.path.getsize(os.path.join(folder, n)) for n in names))}


def dataset_folder_summary(preprocessed_root: str, dataset_name: str, plans_identifier: str, summary: dict) -> dict:
    ds_dir = os.path.join(preprocessed_root, dataset_name)
    folders = {}
    for c, cs in summary["configurations"].items():
        folders[c] = preprocessed_folder_counts(os.path.join(ds_dir, cs["data_identifier"]))
    gt = os.path.join(ds_dir, "gt_segmentations")
    gt_n = len([n for n in os.listdir(gt) if os.path.isfile(os.path.join(gt, n))]) if os.path.isdir(gt) else 0
    return {"dataset_folder": ds_dir, "preprocessed_folders": folders,
            "gt_segmentations": {"path": gt, "exists": os.path.isdir(gt), "n_files": gt_n},
            "splits_final_json_present": os.path.isfile(os.path.join(ds_dir, "splits_final.json"))}


def run_plan_and_preprocess(req: dict) -> dict:
    from nnunetv2.paths import nnUNet_preprocessed
    from nnunetv2.experiment_planning.plan_and_preprocess_api import extract_fingerprints, plan_experiments, preprocess
    from nnunetv2.utilities.dataset_name_id_conversion import convert_id_to_dataset_name

    dataset_id = int(req["dataset_id"])
    timings = {}
    dataset_name = convert_id_to_dataset_name(dataset_id)

    # 1) fingerprint (extract_fingerprints; CLI: -fpe DatasetFingerprintExtractor -npfp --verify_dataset_integrity --clean)
    print("Fingerprint extraction...", flush=True)
    t0 = time.perf_counter()
    extract_fingerprints([dataset_id], req["fingerprint_extractor"], int(req["num_processes_fingerprint"]),
                         bool(req["check_dataset_integrity"]), bool(req["clean"]), bool(req["verbose"]),
                         show_progress_bar=False)
    timings["extract_fingerprints"] = round(time.perf_counter() - t0, 3)

    # 2) planning (plan_experiments; CLI: -pl -gpu_memory_target -preprocessor_name -overwrite_target_spacing -overwrite_plans_name)
    print("Experiment planning...", flush=True)
    t0 = time.perf_counter()
    plans_identifier = plan_experiments([dataset_id], req["planner"], req["gpu_memory_target_in_gb"],
                                        req["preprocessor_name"], req["overwrite_target_spacing"],
                                        req["overwrite_plans_name"])
    timings["plan_experiments"] = round(time.perf_counter() - t0, 3)

    plans_file = os.path.join(str(nnUNet_preprocessed), dataset_name, plans_identifier + ".json")
    summary = plans_summary(plans_file)
    available = summary["available_configurations"]
    requested = list(req["configurations"])
    to_run = [c for c in requested if c in available]
    skipped = [c for c in requested if c not in available]

    # 3) preprocessing (preprocess; CLI: -c -np --no_pp). Upstream skips configurations absent from the plans.
    if req["run_preprocessing"]:
        print("Preprocessing...", flush=True)
        if req["num_processes"] is None:
            # plan_and_preprocess_entrypoints.plan_and_preprocess_entry: default -np per configuration
            default_np = {"2d": 8, "3d_fullres": 4, "3d_lowres": 8}
            num_processes = [default_np[c] if c in default_np else 4 for c in requested]
        else:
            num_processes = [int(req["num_processes"])] * len(requested)
        t0 = time.perf_counter()
        preprocess([dataset_id], plans_identifier, configurations=requested, num_processes=num_processes,
                   verbose=bool(req["verbose"]), show_progress_bar=False)
        timings["preprocess"] = round(time.perf_counter() - t0, 3)
    else:
        num_processes = None

    fingerprint_file = os.path.join(str(nnUNet_preprocessed), dataset_name, "dataset_fingerprint.json")
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "plans_identifier": plans_identifier,
        "plans_file": plans_file,
        "fingerprint_file": fingerprint_file if os.path.isfile(fingerprint_file) else None,
        "plans": summary,
        "fingerprint": fingerprint_summary(fingerprint_file) if os.path.isfile(fingerprint_file) else None,
        "folders": dataset_folder_summary(str(nnUNet_preprocessed), dataset_name, plans_identifier, summary),
        "configurations_requested": requested,
        "configurations_preprocessed": to_run if req["run_preprocessing"] else [],
        "configurations_skipped": skipped,
        "num_processes_per_configuration": dict(zip(requested, num_processes)) if num_processes else None,
        "timings_seconds": timings,
    }


def run_inspect_plans(req: dict) -> dict:
    plans_file = req["plans_file"]
    summary = plans_summary(plans_file)
    fingerprint_file = req.get("fingerprint_file")
    out = {
        "dataset_name": summary["dataset_name"],
        "plans_identifier": summary["plans_name"],
        "plans_file": plans_file,
        "fingerprint_file": fingerprint_file if fingerprint_file and os.path.isfile(fingerprint_file) else None,
        "plans": summary,
        "fingerprint": fingerprint_summary(fingerprint_file) if fingerprint_file and os.path.isfile(fingerprint_file) else None,
    }
    preprocessed_root = req.get("preprocessed_root")
    if preprocessed_root and os.path.isdir(os.path.join(preprocessed_root, summary["dataset_name"])):
        out["folders"] = dataset_folder_summary(preprocessed_root, summary["dataset_name"], summary["plans_name"], summary)
    else:
        out["folders"] = None
    return out


def main() -> int:
    request_file, result_file = sys.argv[1], sys.argv[2]
    with open(request_file) as f:
        req = json.load(f)
    result = {"ok": False, "mode": req.get("mode")}
    try:
        import nnunetv2  # noqa: F401  (paths are read from the environment set by the parent)
        if req["mode"] == "plan_and_preprocess":
            result.update(run_plan_and_preprocess(req))
        elif req["mode"] == "inspect_plans":
            result.update(run_inspect_plans(req))
        else:
            raise ValueError(f"unknown mode {req.get('mode')!r}")
        result["ok"] = True
        code = 0
    except BaseException as e:  # noqa: BLE001  report every failure to the parent through the result file
        result["error_type"] = type(e).__name__
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()
        traceback.print_exc()
        code = 1
    with open(result_file, "w") as f:
        json.dump(result, f, indent=1)
    return code


if __name__ == "__main__":
    sys.exit(main())
