"""Child driver written by src/tools/nnunet_dataset.py: runs one upstream nnunetv2 2.8.1 call.
Usage: python driver.py <args.json> <result.json>   (nnU-Net paths come from the environment)."""
import json
import sys
import traceback


def _run(op, a):
    if op == "convert_msd":
        from nnunetv2.dataset_conversion.convert_MSD_dataset import convert_msd_dataset
        convert_msd_dataset(a["source_folder"], overwrite_target_id=a["overwrite_target_id"],
                            num_processes=a["num_processes"])
        return {}
    if op == "generate_dataset_json":
        from nnunetv2.dataset_conversion.generate_dataset_json import generate_dataset_json
        generate_dataset_json(a["output_folder"], a["channel_names"], a["labels"], a["num_training_cases"],
                              a["file_ending"], **a["kwargs"])
        return {}
    if op == "verify":
        from nnunetv2.experiment_planning.verify_dataset_integrity import verify_dataset_integrity
        verify_dataset_integrity(a["folder"], a["num_processes"])
        return {}
    if op == "overlays_raw":
        from nnunetv2.utilities.overlay_plots import generate_overlays_from_raw
        generate_overlays_from_raw(a["dataset"], a["output_folder"], num_processes=a["num_processes"],
                                   channel_idx=a["channel_idx"], overlay_intensity=a["overlay_intensity"])
        return {}
    if op == "overlays_preprocessed":
        from nnunetv2.utilities.overlay_plots import generate_overlays_from_preprocessed
        generate_overlays_from_preprocessed(a["dataset"], a["output_folder"], num_processes=a["num_processes"],
                                            channel_idx=a["channel_idx"], configuration=a["configuration"],
                                            plans_identifier=a["plans_identifier"],
                                            overlay_intensity=a["overlay_intensity"])
        return {}
    raise ValueError("unknown op %r" % op)


def main():
    args_file, result_file = sys.argv[1], sys.argv[2]
    with open(args_file) as fh:
        a = json.load(fh)
    try:
        res = {"ok": True}
        res.update(_run(a["op"], a))
    except BaseException as e:  # upstream signals problems with AssertionError / RuntimeError / FileNotFoundError
        res = {"ok": False, "exception_type": type(e).__name__, "message": str(e),
               "traceback": traceback.format_exc()}
    sys.stdout.flush()
    with open(result_file, "w") as fh:
        json.dump(res, fh, indent=2)
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
