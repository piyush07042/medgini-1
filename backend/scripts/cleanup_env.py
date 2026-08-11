import argparse
import os
import shutil
from pathlib import Path


def remove_pycache(root: Path):
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for d in list(dirnames):
            if d == "__pycache__":
                p = Path(dirpath) / d
                shutil.rmtree(p, ignore_errors=True)
                removed += 1
    return removed


def remove_joblib_models(models_root: Path):
    removed = 0
    for p in models_root.rglob('*.joblib'):
        try:
            p.unlink()
            removed += 1
        except Exception:
            pass
    return removed


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Cleanup environment caches and old model artifacts')
    ap.add_argument('--root', default='.', help='Path to project root (default: repo root)')
    ap.add_argument('--remove-models', action='store_true', help='Also remove all .joblib model artifacts under backend/models')
    ap.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompts')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    print(f'Removing __pycache__ under {root} ...')
    n = remove_pycache(root)
    print(f'Removed {n} __pycache__ directories')

    if args.remove_models:
        models_root = root / 'backend' / 'models'
        if not models_root.exists():
            print(f'No models dir at {models_root}')
        else:
            if not args.yes:
                confirm = input(f'Remove all .joblib files under {models_root}? [y/N]: ').strip().lower()
                if confirm not in ('y','yes'):
                    print('Aborted removing models')
                    raise SystemExit(0)
            removed_models = remove_joblib_models(models_root)
            print(f'Removed {removed_models} .joblib files from {models_root}')

    print('Cleanup complete.')
