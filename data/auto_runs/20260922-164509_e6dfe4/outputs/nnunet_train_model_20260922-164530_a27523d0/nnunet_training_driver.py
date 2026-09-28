
"""Child driver written by src/tools/nnunet_training.py: calls the bound nnunetv2 functions and writes a JSON result.
usage: python nnunet_training_driver.py <args.json> <result.json>
"""
import hashlib
import json
import os
import re
import sys
import time
import traceback
import zipfile


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path):
    return {"path": os.path.abspath(path), "bytes": os.path.getsize(path), "sha256": sha256_of(path)}


def to_num(x):
    if isinstance(x, str):
        for cast in (int, float):
            try:
                return cast(x)
            except ValueError:
                pass
    return x


def key_str(k):
    return str(k)


def resolve_configuration(plans, configuration):
    """Follow 'inherits_from' as nnunetv2's ConfigurationManager does to read patch_size etc. of a configuration."""
    cfgs = plans.get("configurations", {})
    cfg = dict(cfgs.get(configuration, {}))
    seen = set()
    while "inherits_from" in cfg and cfg["inherits_from"] not in seen:
        seen.add(cfg["inherits_from"])
        parent = dict(cfgs.get(cfg["inherits_from"], {}))
        parent.update({k: v for k, v in cfg.items() if k != "inherits_from"})
        cfg = parent
    return cfg


def summarize_validation(fold_folder, file_ending):
    from nnunetv2.evaluation.evaluate_predictions import load_summary_json  # bound reader
    val_dir = os.path.join(fold_folder, "validation")
    out = {"folder": val_dir, "exists": os.path.isdir(val_dir), "summary_json": None}
    if not out["exists"]:
        return out
    names = os.listdir(val_dir)
    out["n_segmentations"] = sum(1 for n in names if file_ending and n.endswith(file_ending))
    out["n_npz"] = sum(1 for n in names if n.endswith(".npz"))
    out["n_pkl"] = sum(1 for n in names if n.endswith(".pkl"))
    summary_path = os.path.join(val_dir, "summary.json")
    if os.path.isfile(summary_path):
        s = load_summary_json(summary_path)
        out["summary_json"] = summary_path
        out["summary_sha256"] = sha256_of(summary_path)
        out["n_cases"] = len(s.get("metric_per_case", []))
        fg = s.get("foreground_mean", {})
        out["foreground_mean"] = {key_str(k): (float(v) if isinstance(v, (int, float)) else v) for k, v in fg.items()}
        out["foreground_mean_dice"] = float(fg["Dice"]) if "Dice" in fg else None
        out["mean_per_label"] = {key_str(lab): {m: (float(v) if isinstance(v, (int, float)) else v)
                                                for m, v in metrics.items() if m in ("Dice", "IoU", "n_pred", "n_ref")}
                                 for lab, metrics in s.get("mean", {}).items()}
        out["mean_dice_per_label"] = {key_str(lab): (float(m["Dice"]) if isinstance(m.get("Dice"), (int, float)) else m.get("Dice"))
                                      for lab, m in s.get("mean", {}).items()}
    return out


def summarize_checkpoint(path):
    import torch
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    info = {"trainer_name": ckpt.get("trainer_name"), "current_epoch": to_num(ckpt.get("current_epoch")),
            "best_ema_fg_dice": (float(ckpt["_best_ema"]) if ckpt.get("_best_ema") is not None else None),
            "inference_allowed_mirroring_axes": (list(ckpt["inference_allowed_mirroring_axes"])
                                                 if ckpt.get("inference_allowed_mirroring_axes") is not None else None)}
    init_args = ckpt.get("init_args") or {}
    info["init_args"] = {"configuration": init_args.get("configuration"), "fold": init_args.get("fold"),
                         "plans_name": (init_args.get("plans") or {}).get("plans_name"),
                         "dataset_name": (init_args.get("plans") or {}).get("dataset_name")}
    weights = ckpt.get("network_weights") or {}
    try:
        info["n_parameters"] = int(sum(int(v.numel()) for v in weights.values() if hasattr(v, "numel")))
        info["n_weight_tensors"] = len(weights)
    except Exception:
        pass
    logging_ = ckpt.get("logging") or {}

    def last(key):
        vals = logging_.get(key)
        if not vals:
            return None
        v = vals[-1]
        if isinstance(v, (list, tuple)):
            return [float(x) for x in v]
        try:
            return float(v)
        except (TypeError, ValueError):
            return v
    starts, ends = logging_.get("epoch_start_timestamps") or [], logging_.get("epoch_end_timestamps") or []
    durations = [float(e) - float(s) for s, e in zip(starts, ends)]
    info["epochs_logged"] = len(logging_.get("train_losses") or [])
    info["final_train_loss"] = last("train_losses")
    info["final_val_loss"] = last("val_losses")
    info["final_mean_fg_pseudo_dice"] = last("mean_fg_dice")
    info["final_ema_fg_pseudo_dice"] = last("ema_fg_dice")
    info["final_pseudo_dice_per_class"] = last("dice_per_class_or_region")
    info["final_lr"] = last("lrs")
    info["epoch_time_s_first"] = round(durations[0], 3) if durations else None
    info["epoch_time_s_mean"] = round(sum(durations) / len(durations), 3) if durations else None
    return info


def summarize_fold_folder(fold_folder, checkpoint_details=True):
    model_folder = os.path.dirname(fold_folder)
    out = {"model_folder": model_folder, "fold_folder": fold_folder, "fold_folder_exists": os.path.isdir(fold_folder)}
    plans, dataset_json = {}, {}
    for name, target in (("plans.json", "plans"), ("dataset.json", "dataset_json")):
        p = os.path.join(model_folder, name)
        if os.path.isfile(p):
            with open(p) as fh:
                if target == "plans":
                    plans = json.load(fh)
                else:
                    dataset_json = json.load(fh)
    file_ending = dataset_json.get("file_ending")
    out["model_folder_entries"] = sorted(os.listdir(model_folder)) if os.path.isdir(model_folder) else []
    out["available_fold_folders"] = {n: sorted(c for c in _CHECKPOINTS if os.path.isfile(os.path.join(model_folder, n, c)))
                                     for n in out["model_folder_entries"] if n.startswith("fold_")}
    out["labels"] = dataset_json.get("labels")
    out["file_ending"] = file_ending
    if not out["fold_folder_exists"]:
        return out
    entries = sorted(os.listdir(fold_folder))
    out["fold_folder_entries"] = entries
    out["training_logs"] = [n for n in entries if n.startswith("training_log_") and n.endswith(".txt")]
    out["checkpoints"] = {c: file_info(os.path.join(fold_folder, c)) for c in _CHECKPOINTS if os.path.isfile(os.path.join(fold_folder, c))}
    prog = os.path.join(fold_folder, "progress.png")
    out["progress_png"] = file_info(prog) if os.path.isfile(prog) else None
    dbg_path = os.path.join(fold_folder, "debug.json")
    out["debug"] = None
    if os.path.isfile(dbg_path):
        with open(dbg_path) as fh:
            dbg = json.load(fh)
        keys = ("num_epochs", "current_epoch", "num_iterations_per_epoch", "num_val_iterations_per_epoch", "batch_size",
                "configuration_name", "fold", "device", "gpu_name", "torch_version", "cudnn_version", "network",
                "initial_lr", "weight_decay", "oversample_foreground_percent", "enable_deep_supervision",
                "inference_allowed_mirroring_axes", "hostname", "is_ddp")
        out["debug"] = {k: to_num(dbg[k]) for k in keys if k in dbg}
        out["debug"]["path"] = dbg_path
    cfg_name = (out["debug"] or {}).get("configuration_name") or os.path.basename(model_folder).split("__")[-1]
    cfg = resolve_configuration(plans, cfg_name) if plans else {}
    out["configuration"] = {k: cfg.get(k) for k in ("patch_size", "batch_size", "spacing", "data_identifier",
                                                       "network_arch_class_name", "preprocessor_name") if k in cfg}
    out["plans_name"] = plans.get("plans_name")
    out["dataset_name"] = plans.get("dataset_name")
    out["validation"] = summarize_validation(fold_folder, file_ending)
    if out["training_logs"]:
        newest = os.path.join(fold_folder, out["training_logs"][-1])
        try:
            with open(newest, errors="replace") as fh:
                text = fh.read()
            out["latest_training_log"] = {"path": newest, "torch_compile_used": "Using torch.compile" in text,
                                          "n_epoch_time_lines": len(re.findall(r"Epoch time: ", text)),
                                          "validation_complete": "Validation complete" in text,
                                          "tail": text.strip().splitlines()[-3:]}
        except OSError:
            pass
    if checkpoint_details and "checkpoint_final.pth" in out["checkpoints"]:
        try:
            out["checkpoint_final_info"] = summarize_checkpoint(out["checkpoints"]["checkpoint_final.pth"]["path"])
        except Exception as exc:  # informational only
            out["checkpoint_final_info_error"] = f"{type(exc).__name__}: {exc}"
    return out


_CHECKPOINTS = ("checkpoint_final.pth", "checkpoint_best.pth", "checkpoint_latest.pth")


def op_train(a):
    import multiprocessing
    import torch
    from nnunetv2.run.run_training import run_training  # bound: the function behind nnUNetv2_train
    from nnunetv2.utilities.file_path_utilities import get_output_folder

    # an unknown trainer name is rejected by upstream itself (recursive_find_trainer_class_by_name raises RuntimeError
    # "Could not find requested nnunet trainer ..." inside run_training -> get_trainer_from_args)
    # device handling as in run_training_entry (nnUNetv2_train): cpu -> many threads, cuda -> single thread
    if a["device"] == "cpu":
        torch.set_num_threads(multiprocessing.cpu_count())
        device = torch.device("cpu")
    else:
        if not torch.cuda.is_available():
            raise RuntimeError(f"CUDA is not available in the training process (CUDA_VISIBLE_DEVICES="
                               f"{os.environ.get('CUDA_VISIBLE_DEVICES')!r}); pass device='cpu' or free a GPU")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        device = torch.device("cuda")
    t0 = time.time()
    run_training(a["dataset_name"], a["configuration"], a["fold"], a["trainer"], a["plans_identifier"], None, 1,
                 a["export_validation_probabilities"], a["continue_training"], a["only_run_validation"],
                 a["disable_checkpointing"], False, device=device)
    wall = round(time.time() - t0, 3)
    fold_folder = get_output_folder(a["dataset_name"], a["trainer"], a["plans_identifier"], a["configuration"], a["fold"])
    res = summarize_fold_folder(fold_folder, checkpoint_details=True)
    res["upstream_wall_seconds"] = wall
    res["device"] = {"type": device.type, "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
                     "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                     "torch_version": torch.__version__, "nnUNet_compile_env": os.environ.get("nnUNet_compile")}
    return res


def op_inspect(a):
    from nnunetv2.utilities.file_path_utilities import get_output_folder  # bound
    fold_folder = get_output_folder(a["dataset_name"], a["trainer"], a["plans_identifier"], a["configuration"], a["fold"])
    model_folder = os.path.dirname(fold_folder)
    if not os.path.isdir(model_folder):
        raise FileNotFoundError(f"no trained model folder {model_folder} (dataset {a['dataset_name']}, trainer {a['trainer']}, "
                                f"plans {a['plans_identifier']}, configuration {a['configuration']})")
    if not os.path.isdir(fold_folder):
        folds = sorted(n for n in os.listdir(model_folder) if n.startswith("fold_"))
        raise FileNotFoundError(f"fold folder {fold_folder} does not exist; available fold folders in {model_folder}: {folds}")
    return summarize_fold_folder(fold_folder, checkpoint_details=a.get("checkpoint_details", True))


def zip_listing(path, cap):
    with zipfile.ZipFile(path) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
    members = [{"name": i.filename, "bytes": i.file_size} for i in infos]
    return {"n_members": len(members), "total_uncompressed_bytes": int(sum(i.file_size for i in infos)),
            "members": members[:cap], "members_truncated": len(members) > cap}


def op_export(a):
    from nnunetv2.model_sharing.model_export import export_pretrained_model  # bound
    t0 = time.time()
    export_pretrained_model(a["dataset_name"], a["output_file"], configurations=list(a["configurations"]),
                            trainer=a["trainer"], plans_identifier=a["plans_identifier"], folds=tuple(a["folds"]),
                            strict=a["strict"], save_checkpoints=tuple(a["checkpoint_names"]),
                            export_crossval_predictions=a["export_crossval_predictions"])
    res = {"upstream_wall_seconds": round(time.time() - t0, 3), "zip": file_info(a["output_file"])}
    res.update(zip_listing(a["output_file"], a["member_cap"]))
    return res


def op_install(a):
    from nnunetv2.paths import nnUNet_results
    from nnunetv2.model_sharing.model_import import install_model_from_zip_file  # bound
    results_root = str(nnUNet_results)
    with zipfile.ZipFile(a["zip_path"]) as zf:
        names = [i.filename for i in zf.infolist() if not i.is_dir()]
    existed_before = [n for n in names if os.path.isfile(os.path.join(results_root, n))]
    t0 = time.time()
    install_model_from_zip_file(a["zip_path"])
    wall = round(time.time() - t0, 3)
    installed, missing = {}, []
    for n in names:
        p = os.path.join(results_root, n)
        if os.path.isfile(p):
            installed[n] = file_info(p)
        else:
            missing.append(n)
    model_folders = sorted({"/".join(n.split("/")[:2]) for n in names if len(n.split("/")) >= 3 and n.split("/")[0].startswith("Dataset")})
    return {"nnUNet_results": results_root, "upstream_wall_seconds": wall, "n_files": len(installed),
            "installed_files": installed, "missing_after_install": missing, "overwritten_files": existed_before,
            "installed_model_folders": [os.path.join(results_root, m) for m in model_folders]}


OPS = {"train": op_train, "inspect": op_inspect, "export": op_export, "install": op_install}


def main():
    with open(sys.argv[1]) as fh:
        args = json.load(fh)
    result_path = sys.argv[2]
    try:
        payload = {"ok": True, "result": OPS[args["op"]](args)}
    except BaseException as exc:  # reported to the parent through the JSON file
        payload = {"ok": False, "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}
    with open(result_path, "w") as fh:
        json.dump(payload, fh, indent=1, default=str)
    sys.stdout.flush()
    sys.exit(0 if payload["ok"] else 3)


if __name__ == "__main__":
    main()
