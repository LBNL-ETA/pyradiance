import os
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path

# --- Configuration ---
RADIANCE_REPO_URL = "https://github.com/LBNL-ETA/Radiance.git"
RADIANCE_TOP_SRC_DIR_IN_REPO = "src"
PYRADIANCE_TOP_TARGET_DIR_IN_PROJECT = "src/radiance"
SUBDIRS_TO_SYNC_NAMES = ["common", "px", "rt", "gen", "cv", "util"]
GLOBAL_FILE_PATTERNS = ["*.c", "*.h", "*.cpp"]
RECURSIVE_SEARCH_IN_SUBDIRS_GLOBALLY = False # Set True if source subdirs have nested structure to copy
# --- End Configuration ---

def run_command(command, cwd=None, check=True):
    """Helper to run a shell command."""
    print(f"Running: {' '.join(command)}" + (f" in {cwd}" if cwd else ""))
    process = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if check and process.returncode != 0:
        print("Error running command:")
        print("STDOUT:", process.stdout)
        print("STDERR:", process.stderr)
        raise subprocess.CalledProcessError(process.returncode, command, process.stdout, process.stderr)
    return process

def perform_sync_operations(
    pyradiance_root_dir,
    radiance_clone_root_dir,
    subdirectories_to_sync,
    radiance_base_src_rel_path,
    pyradiance_base_target_rel_path,
    file_patterns_global,
    recursive_search_global,
    dry_run=False
):
    """
    Syncs files for each listed subdirectory, updating matched files
    and leaving other files in the target untouched.
    """
    pyradiance_root = Path(pyradiance_root_dir).resolve()
    radiance_clone_root = Path(radiance_clone_root_dir).resolve()

    print("\n--- Starting Non-Destructive Sync Operations ---")

    for subdir_name in subdirectories_to_sync:
        radiance_src_subdir_rel_path = Path(radiance_base_src_rel_path) / subdir_name
        pyradiance_target_subdir_rel_path = Path(pyradiance_base_target_rel_path) / subdir_name

        radiance_src_full_path = radiance_clone_root / radiance_src_subdir_rel_path
        pyradiance_target_full_path = pyradiance_root / pyradiance_target_subdir_rel_path

        print(f"\nProcessing subdirectory: '{subdir_name}'")
        print(f"  Radiance source      : {radiance_src_full_path} (relative to clone: {radiance_src_subdir_rel_path})")
        print(f"  PyRadiance target    : {pyradiance_target_full_path} (relative to project: {pyradiance_target_subdir_rel_path})")
        print(f"  File patterns        : {', '.join(file_patterns_global)}")
        print(f"  Recursive search     : {recursive_search_global}")

        if not radiance_src_full_path.is_dir():
            print(f"  WARNING: Radiance source path '{radiance_src_full_path}' does not exist or is not a directory. Skipping this subdirectory.")
            # (Dry run / path checking logic as before)
            if dry_run and not radiance_clone_root.exists():
                 print(f"    (This might be expected in dry_run if clone was skipped)")
            elif radiance_clone_root.exists() and not radiance_src_full_path.exists():
                 print(f"    Please check if '{radiance_src_subdir_rel_path}' is a valid path in the Radiance repo structure.")
            continue
        
        # --- MODIFICATION START ---
        # Ensure the target base directory for the current subdir_name exists.
        # DO NOT remove it if it already exists.
        if not dry_run:
            pyradiance_target_full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Ensured target directory exists: {pyradiance_target_full_path}")
        else:
            print(f"  DRY RUN: Would ensure target directory exists: {pyradiance_target_full_path}")
        # --- MODIFICATION END ---

        # Find and copy matching files
        copied_files_count = 0
        updated_files_count = 0 # Keep track of updates vs new
        source_file_paths_to_copy = set()

        for pattern in file_patterns_global:
            if recursive_search_global:
                found_paths = radiance_src_full_path.rglob(pattern)
            else:
                found_paths = radiance_src_full_path.glob(pattern)
            
            for p in found_paths:
                if p.is_file():
                    source_file_paths_to_copy.add(p)
        
        sorted_source_files = sorted(list(source_file_paths_to_copy))

        if not sorted_source_files:
            print(f"  No files matched the patterns for '{subdir_name}' in source '{radiance_src_full_path}'. Target directory untouched.")
            continue

        for src_file_path in sorted_source_files:
            relative_path_in_source_subdir = src_file_path.relative_to(radiance_src_full_path)
            dest_file_path = pyradiance_target_full_path / relative_path_in_source_subdir

            action = "Copied (new)"
            if dest_file_path.exists():
                action = "Updated (overwrite)"
                updated_files_count +=1
            else:
                copied_files_count +=1


            if not dry_run:
                # Ensure parent directory of the destination file exists (for recursive copies)
                dest_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file_path, dest_file_path) # copy2 preserves metadata and overwrites
            else:
                dry_run_src_display = src_file_path.relative_to(radiance_clone_root)
                dry_run_dest_display = dest_file_path.relative_to(pyradiance_root)
                print(f"    DRY RUN: Would {action.lower().split(' ')[0]}: {dry_run_src_display} -> {dry_run_dest_display}")
        
        total_processed = copied_files_count + updated_files_count
        if total_processed > 0:
            print(f"  Processed {total_processed} files for '{subdir_name}': {copied_files_count} new, {updated_files_count} updated.")
        else: # Should not happen if sorted_source_files was not empty, but good guard.
            print(f"  No files were processed for '{subdir_name}' (unexpected).")


    print("\n--- Non-Destructive Sync Operations Finished ---")


def main_sync_orchestrator(pyradiance_root_arg, radiance_branch="master", dry_run=False):
    """
    Main orchestrator for cloning/updating Radiance and performing the sync.
    """
    pyradiance_root_path = Path(pyradiance_root_arg).resolve()

    print(f"PyRadiance root: {pyradiance_root_path}")
    print(f"Radiance repository: {RADIANCE_REPO_URL} (branch/tag: {radiance_branch})")
    if dry_run:
        print("\n--- DRY RUN MODE ENABLED ---")

    if not SUBDIRS_TO_SYNC_NAMES:
        print("No subdirectories listed in SUBDIRS_TO_SYNC_NAMES. Exiting.")
        return

    with tempfile.TemporaryDirectory(prefix="radiance_clone_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        radiance_clone_target_dir = temp_dir / "Radiance" 

        print(f"\n1. Cloning Radiance repository into temporary location: {radiance_clone_target_dir}")
        if not dry_run:
            run_command([
                "git", "clone", "--depth", "1",
                "--branch", radiance_branch,
                RADIANCE_REPO_URL, str(radiance_clone_target_dir)
            ])
        else:
            print(f"  DRY RUN: Would clone {RADIANCE_REPO_URL} (branch {radiance_branch}) to {radiance_clone_target_dir}")

        perform_sync_operations(
            pyradiance_root_dir=pyradiance_root_path,
            radiance_clone_root_dir=radiance_clone_target_dir,
            subdirectories_to_sync=SUBDIRS_TO_SYNC_NAMES,
            radiance_base_src_rel_path=RADIANCE_TOP_SRC_DIR_IN_REPO,
            pyradiance_base_target_rel_path=PYRADIANCE_TOP_TARGET_DIR_IN_PROJECT,
            file_patterns_global=GLOBAL_FILE_PATTERNS,
            recursive_search_global=RECURSIVE_SEARCH_IN_SUBDIRS_GLOBALLY,
            dry_run=dry_run
        )

    print("\nSync process finished.")
    if not dry_run:
        print("  Please review the changes in your pyradiance repository.")
        print(f"  Consider running 'git status' and 'git diff' in '{pyradiance_root_path}'.")
        print("  Remember: Files in target directories not matching source patterns,")
        print("  or files from older Radiance versions removed in the current source, were NOT deleted.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Non-destructively syncs specific Radiance source files into the pyradiance project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--pyradiance-root",
        default=os.getcwd(),
        help="Path to the root of your pyradiance repository."
    )
    parser.add_argument(
        "--branch",
        default="master",
        help="Radiance repository branch or tag to sync from."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the sync process without making any file system changes."
    )
    args = parser.parse_args()

    try:
        main_sync_orchestrator(args.pyradiance_root, args.branch, args.dry_run)
        print("\nSync script completed.")
    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during a git command: {e}")
        if e.stdout: print(f"STDOUT: {e.stdout}")
        if e.stderr: print(f"STDERR: {e.stderr}")
        exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
