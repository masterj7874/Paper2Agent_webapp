
"""nnunet_evaluation child driver: runs one bound nnU-Net call and writes a JSON result file."""
import json
import math
import os
import sys
import traceback


def _json_safe(o):
    # numpy scalars (e.g. label ids in postprocessing kwargs, np.str_ dataset names) -> Python; NaN/inf (label absent
    # in reference and prediction -> upstream NaN) are not valid JSON -> None
    if isinstance(o, dict):
        return {str(k): _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except (TypeError, ValueError):
            return str(o)
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    if isinstance(o, (str, int, float, bool)) or o is None:
        return o
    return str(o)


def _case_id(fname, file_ending):
    for ending in (".nii.gz", file_ending):
        if ending and fname.endswith(ending):
            return fname[: -len(ending)]
    return os.path.splitext(fname)[0]


def _compact_summary(summary_file, file_ending):
    from batchgenerators.utilities.file_and_folder_operations import load_json
    s = load_json(summary_file)
    per_case = [{"case": _case_id(os.path.basename(r["prediction_file"]), file_ending), "metrics": r["metrics"]}
                for r in s["metric_per_case"]]
    return {"n_cases": len(per_case), "labels_or_regions": list(s["mean"].keys()),
            "foreground_mean": s["foreground_mean"], "mean": s["mean"], "metric_per_case": per_case}


def _check_case_files(reference_folder, prediction_folder, file_ending, chill):
    from batchgenerators.utilities.file_and_folder_operations import subfiles
    pred_files = subfiles(prediction_folder, suffix=file_ending, join=False)
    ref_files = subfiles(reference_folder, suffix=file_ending, join=False)
    if not pred_files:
        raise FileNotFoundError(f"No '{file_ending}' segmentation files in prediction folder {prediction_folder}")
    if not ref_files:
        raise FileNotFoundError(f"No '{file_ending}' segmentation files in reference folder {reference_folder}")
    ref_set = set(ref_files)
    missing_ref = [f for f in pred_files if f not in ref_set]
    if missing_ref:
        raise FileNotFoundError(
            f"{len(missing_ref)} of {len(pred_files)} prediction files have no reference file of the same name in "
            f"{reference_folder} (e.g. {missing_ref[:5]}). Prediction and reference files must share names and ending.")
    pred_set = set(pred_files)
    missing_pred = [f for f in ref_files if f not in pred_set]
    if missing_pred and not chill:
        raise FileNotFoundError(
            f"{len(missing_pred)} of {len(ref_files)} reference cases have no prediction in {prediction_folder} "
            f"(e.g. {missing_pred[:5]}). Set chill=True to evaluate only the predicted cases (upstream --chill).")
    return pred_files, ref_files, missing_pred


def op_evaluate(a):
    from batchgenerators.utilities.file_and_folder_operations import subfiles, load_json
    from nnunetv2.evaluation.evaluate_predictions import compute_metrics_on_folder2, compute_metrics_on_folder_simple
    ref, pred = a["reference_folder"], a["prediction_folder"]
    if a["mode"] == "dataset_plans":
        file_ending = load_json(a["dataset_json"])["file_ending"]
    else:
        ref_all = subfiles(ref, join=False)
        if not ref_all:
            raise FileNotFoundError(f"Reference folder {ref} is empty")
        file_ending = os.path.splitext(ref_all[0])[-1]  # upstream rule of compute_metrics_on_folder_simple
    pred_files, ref_files, missing_pred = _check_case_files(ref, pred, file_ending, a["chill"])
    if a["mode"] == "dataset_plans":
        compute_metrics_on_folder2(ref, pred, a["dataset_json"], a["plans_json"], output_file=a["output_file"],
                                   num_processes=a["num_processes"], chill=a["chill"])
    else:
        compute_metrics_on_folder_simple(ref, pred, a["labels"], output_file=a["output_file"],
                                         num_processes=a["num_processes"], ignore_label=a["ignore_label"],
                                         chill=a["chill"])
    res = _compact_summary(a["output_file"], file_ending)
    res.update({"file_ending": file_ending, "n_prediction_files": len(pred_files), "n_reference_files": len(ref_files),
                "n_reference_cases_without_prediction": len(missing_pred)})
    return res


def op_determine_postprocessing(a):
    from batchgenerators.utilities.file_and_folder_operations import join, isfile, load_json
    from nnunetv2.postprocessing.remove_connected_components import determine_postprocessing
    pred, ref = a["prediction_folder"], a["reference_folder"]
    plans_json, dataset_json = a["plans_json"], a["dataset_json"]
    # upstream: None -> the files nnUNetv2_predict copied into the prediction folder
    if plans_json is None:
        plans_json = join(pred, "plans.json")
        if not isfile(plans_json):
            raise FileNotFoundError(f"plans_json not given and {plans_json} does not exist; pass plans_json or "
                                    f"model_folder (nnUNetv2_predict writes plans.json into its output folder)")
    if dataset_json is None:
        dataset_json = join(pred, "dataset.json")
        if not isfile(dataset_json):
            raise FileNotFoundError(f"dataset_json not given and {dataset_json} does not exist; pass dataset_json or "
                                    f"model_folder")
    file_ending = load_json(dataset_json)["file_ending"]
    pred_files, ref_files, missing_pred = _check_case_files(ref, pred, file_ending, chill=True)
    baseline_summary_reused = isfile(join(pred, "summary.json"))  # upstream reuses an existing summary.json
    pp_fns, pp_kwargs = determine_postprocessing(pred, ref, plans_json, dataset_json,
                                                 num_processes=a["num_processes"],
                                                 keep_postprocessed_files=a["keep_postprocessed_files"])
    ppj = load_json(join(pred, "postprocessing.json"))
    names = [f.__name__ for f in pp_fns]
    keep = a["keep_postprocessed_files"]
    return {
        "postprocessing_functions": names,
        "postprocessing_kwargs": pp_kwargs,
        "n_postprocessing_steps": len(names),
        "decision": ("no postprocessing step improved the Dice; postprocessing.pkl holds an empty list"
                     if not names else "; ".join(f"{n}({kw})" for n, kw in zip(names, pp_kwargs))),
        "foreground_dice_before": ppj["input_folder"]["foreground_mean"]["Dice"],
        "foreground_dice_after": ppj["postprocessed"]["foreground_mean"]["Dice"],
        "per_label_dice_before": {k: v["Dice"] for k, v in ppj["input_folder"]["mean"].items()},
        "per_label_dice_after": {k: v["Dice"] for k, v in ppj["postprocessed"]["mean"].items()},
        "input_folder_metrics": ppj["input_folder"],
        "postprocessed_metrics": ppj["postprocessed"],
        "postprocessing_pkl": join(pred, "postprocessing.pkl"),
        "postprocessing_json": join(pred, "postprocessing.json"),
        "input_summary_json": join(pred, "summary.json"),
        "postprocessed_folder": join(pred, "postprocessed") if keep else None,
        "postprocessed_summary_json": join(pred, "postprocessed", "summary.json") if keep else None,
        "plans_json": plans_json, "dataset_json": dataset_json, "file_ending": file_ending,
        "n_prediction_files": len(pred_files), "n_reference_files": len(ref_files),
        "n_reference_cases_without_prediction": len(missing_pred),
        "baseline_summary_reused": baseline_summary_reused,
    }


def op_find_best_configuration(a):
    from batchgenerators.utilities.file_and_folder_operations import join, isdir, isfile, subfiles, load_pickle, load_json
    from nnunetv2.evaluation.find_best_configuration import (find_best_configuration,
                                                             dumb_trainer_config_plans_to_trained_models_dict)
    from nnunetv2.utilities.file_path_utilities import (maybe_convert_to_dataset_name, get_output_folder,
                                                        folds_tuple_to_string)
    from nnunetv2.utilities.plans_handling.plans_handler import PlansManager
    from nnunetv2.paths import nnUNet_preprocessed, nnUNet_results
    ds = a["dataset"].strip()
    ds_arg = int(ds) if ds.isdigit() else ds
    dataset_name = maybe_convert_to_dataset_name(ds_arg)
    folds = tuple(int(f) for f in a["folds"])
    models = dumb_trainer_config_plans_to_trained_models_dict(a["trainers"], a["configurations"], a["plans_identifiers"])
    gt_folder = join(nnUNet_preprocessed, dataset_name, "gt_segmentations")
    if not isdir(gt_folder):
        raise FileNotFoundError(f"{gt_folder} missing (needed to evaluate ensembles and to determine postprocessing); "
                                f"run plan_and_preprocess for {dataset_name} first")
    for p in dict.fromkeys(a["plans_identifiers"]):
        pf = join(nnUNet_preprocessed, dataset_name, p + ".json")
        if not isfile(pf):
            raise FileNotFoundError(f"Plans file {pf} missing for plans identifier '{p}'")
    available, skipped = [], []
    for m in models:
        pm = PlansManager(join(nnUNet_preprocessed, dataset_name, m["plans"] + ".json"))
        if m["configuration"] not in pm.available_configurations:  # upstream filter_available_models skips these
            skipped.append({**m, "reason": f"configuration not in plans {m['plans']} "
                                           f"(available: {list(pm.available_configurations)})"})
            continue
        out = get_output_folder(ds_arg, m["trainer"], m["plans"], m["configuration"], fold=None)
        if not isdir(out):
            raise FileNotFoundError(f"Trained model folder missing: {out}. Train this model for all requested folds "
                                    f"(with export_validation_probabilities/--npz if ensembling is wanted)")
        for f in folds:
            vf = join(out, f"fold_{f}", "validation")
            if not isdir(vf):
                raise FileNotFoundError(f"fold {f} of {out} has no validation folder; train it (or run validation)")
        available.append(m)
    if not available:
        raise ValueError(f"None of the requested configurations {a['configurations']} exist in the plans "
                         f"{a['plans_identifiers']} of {dataset_name}")
    if a["allow_ensembling"] and len(available) > 1:
        for m in available:
            out = get_output_folder(ds_arg, m["trainer"], m["plans"], m["configuration"], fold=None)
            for f in folds:
                vf = join(out, f"fold_{f}", "validation")
                if not subfiles(vf, suffix=".npz", join=False):
                    raise FileNotFoundError(
                        f"No .npz validation probabilities in {vf}; ensembling needs them. Rerun the validation with "
                        f"export_validation_probabilities=True (nnUNetv2_train ... --val --npz) or set "
                        f"allow_ensembling=False")
    ret = find_best_configuration(ds_arg, models, allow_ensembling=a["allow_ensembling"],
                                  num_processes=a["num_processes"], overwrite=a["overwrite"], folds=folds,
                                  strict=a["strict"])
    best = ret["best_model_or_ensemble"]
    all_results = dict(ret["all_results"])
    best_score = max(all_results.values())
    best_key = [k for k in all_results if all_results[k] == best_score][0]  # upstream tie rule: first inserted
    source = os.path.dirname(best["postprocessing_file"])
    pp_fns, pp_kwargs = load_pickle(best["postprocessing_file"])
    ppj_file = join(source, "postprocessing.json")
    ppj = load_json(ppj_file) if isfile(ppj_file) else None
    info_file = join(nnUNet_results, dataset_name, "inference_information.json")
    instr_file = join(nnUNet_results, dataset_name, "inference_instructions.txt")
    with open(instr_file) as fh:
        instructions = fh.read()
    fstr = folds_tuple_to_string(folds)
    crossval_folders = {}
    for m in ret["considered_models"]:
        out = get_output_folder(ds_arg, m["trainer"], m["plans"], m["configuration"], fold=None)
        crossval_folders[os.path.basename(out)] = join(out, f"crossval_results_folds_{fstr}")
    ensemble_folders = {k: join(nnUNet_results, dataset_name, "ensembles", k)
                        for k in all_results if k.startswith("ensemble___")}
    return {
        "dataset_name": dataset_name, "folds": list(folds),
        "considered_models": list(ret["considered_models"]), "skipped_models": skipped,
        "ensembling_allowed": ret["ensembling_allowed"],
        "all_results": all_results,
        "ranking": sorted(all_results.items(), key=lambda kv: kv[1], reverse=True),
        "best_key": best_key, "best_is_ensemble": best_key.startswith("ensemble___"),
        "selected_model_or_models": best["selected_model_or_models"],
        "result_on_crossval_pre_pp": best["result_on_crossval_pre_pp"],
        "result_on_crossval_post_pp": best["result_on_crossval_post_pp"],
        "postprocessing_functions": [f.__name__ for f in pp_fns],
        "postprocessing_kwargs": pp_kwargs,
        "postprocessing_per_label_dice_before": ({k: v["Dice"] for k, v in ppj["input_folder"]["mean"].items()}
                                                if ppj else None),
        "postprocessing_per_label_dice_after": ({k: v["Dice"] for k, v in ppj["postprocessed"]["mean"].items()}
                                               if ppj else None),
        "postprocessing_file": best["postprocessing_file"],
        "postprocessing_json": ppj_file if ppj else None,
        "some_plans_file": best["some_plans_file"],
        "best_source_folder": source,
        "crossval_folders": crossval_folders, "ensemble_folders": ensemble_folders,
        "inference_information_file": info_file, "inference_instructions_file": instr_file,
        "inference_instructions": instructions,
        "return_dict": ret,
    }


OPS = {"evaluate": op_evaluate, "determine_postprocessing": op_determine_postprocessing,
       "find_best_configuration": op_find_best_configuration}


def main():
    op, args_file, result_file = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(args_file) as fh:
        a = json.load(fh)
    try:
        out = {"ok": True, "result": _json_safe(OPS[op](a))}
    except BaseException as exc:  # noqa: BLE001 - everything is reported to the parent through the result file
        out = {"ok": False, "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}
    tmp_file = result_file + ".part"
    with open(tmp_file, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    os.replace(tmp_file, result_file)  # atomic: the parent never sees a partially written result
    sys.stdout.flush()
    sys.exit(0 if out["ok"] else 1)


if __name__ == "__main__":
    main()
