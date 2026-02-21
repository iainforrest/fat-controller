#!/usr/bin/env bash
#
# sync-to-root.sh — Sync fat-controller .claude/ content to ~/.claude/ for server-wide use
#
# Copies commands, agents, and skills (top-level .md only) from the fat-controller
# dev directory to the root ~/.claude/ directory. Does NOT delete destination files
# that don't exist in source, preserving root-only content like entities/, review-setup/, etc.
#
# Usage: ./scripts/sync-to-root.sh [--dry-run]

set -euo pipefail

FC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_CLAUDE="$HOME/.claude"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

copied=0
skipped=0
updated=0

sync_dir() {
    local subdir="$1"
    local src="$FC_DIR/.claude/$subdir"
    local dst="$ROOT_CLAUDE/$subdir"

    if [[ ! -d "$src" ]]; then
        echo "  Skip: $src does not exist"
        return
    fi

    mkdir -p "$dst"

    for file in "$src"/*.md; do
        [[ -f "$file" ]] || continue
        local basename
        basename="$(basename "$file")"
        local dst_file="$dst/$basename"

        if [[ ! -f "$dst_file" ]]; then
            if $DRY_RUN; then
                echo "  NEW:     $subdir/$basename"
            else
                cp "$file" "$dst_file"
                echo "  NEW:     $subdir/$basename"
            fi
            copied=$((copied + 1))
        elif ! diff -q "$file" "$dst_file" > /dev/null 2>&1; then
            if $DRY_RUN; then
                echo "  UPDATED: $subdir/$basename"
            else
                cp "$file" "$dst_file"
                echo "  UPDATED: $subdir/$basename"
            fi
            updated=$((updated + 1))
        else
            skipped=$((skipped + 1))
        fi
    done
}

echo "Fat-controller sync → ~/.claude/"
if $DRY_RUN; then
    echo "(dry run — no files will be changed)"
fi
echo "Source: $FC_DIR/.claude/"
echo "Target: $ROOT_CLAUDE/"
echo ""

sync_dir "commands"
sync_dir "agents"
sync_dir "skills"

echo ""
echo "Done: $copied new, $updated updated, $skipped unchanged"
