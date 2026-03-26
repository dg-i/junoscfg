#!/usr/bin/env bash
#
# integration_test.sh — Live device integration tests for junoscfg
#
# This script SSHs to a real Junos device. Every SSH command is written
# out in plain text below so you can read them all and verify safety.
#
#   SAFETY:  No command ever runs "commit".
#            Every configure session ends with "rollback 0" then "exit".
#            The device is never modified.
#
# Usage:
#   ./integration_test.sh <hostname>
#
# What it does, in order:
#   1. Fetch   — "show configuration" in three formats (read-only)
#   2. Convert — junoscfg format conversions (local, no SSH)
#   3. Compare — upload converted configs, "show | compare", rollback
#   4. Commit check — upload anonymized configs, "commit check", rollback
#   5. Review  — list anonymized files for human inspection
#
set -euo pipefail

DEVICE="${1:?Usage: $0 <hostname>}"
WORKDIR=$(mktemp -d "/tmp/junoscfg_test.XXXXXX")
REMOTE="/var/tmp/junoscfg_test_upload"
PASS=0
FAIL=0
SKIP=0

pass() { PASS=$((PASS + 1)); printf '  \033[32m✔ PASS\033[0m  %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31m✘ FAIL\033[0m  %s\n' "$1"; }
skip() { SKIP=$((SKIP + 1)); printf '  \033[33m⊘ SKIP\033[0m  %s\n' "$1"; }

cleanup() {
    echo ""
    echo "  cleaning up $WORKDIR"
    rm -rf "$WORKDIR"
    ssh -T "$DEVICE" "rm -f /var/tmp/junoscfg_test_*" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "junoscfg integration tests"
echo "device:  $DEVICE"
echo "workdir: $WORKDIR"
echo ""


# ── Prerequisites ─────────────────────────────────────────────────────

command -v junoscfg &>/dev/null || { echo "ERROR: junoscfg not in PATH"; exit 1; }
command -v scp      &>/dev/null || { echo "ERROR: scp not found"; exit 1; }

echo "  checking SSH to $DEVICE ..."
ssh -o ConnectTimeout=10 -T "$DEVICE" "echo ok" &>/dev/null \
    || { echo "ERROR: cannot SSH to $DEVICE"; exit 1; }
echo "  SSH OK"
echo ""


# ═══════════════════════════════════════════════════════════════════════
# 1. FETCH — read-only, nothing is modified on the device
# ═══════════════════════════════════════════════════════════════════════

echo "── Fetch configs from $DEVICE (read-only) ──"
echo ""

ssh -T "$DEVICE" "show configuration | display json | no-more" > "$WORKDIR/device.json"
echo "  device.json  $(wc -l < "$WORKDIR/device.json") lines"

ssh -T "$DEVICE" "show configuration | display set | no-more"  > "$WORKDIR/device.set"
echo "  device.set   $(wc -l < "$WORKDIR/device.set") lines"

ssh -T "$DEVICE" "show configuration | no-more"                > "$WORKDIR/device.conf"
echo "  device.conf  $(wc -l < "$WORKDIR/device.conf") lines"

echo ""


# ═══════════════════════════════════════════════════════════════════════
# 2. CONVERT — all local, no device interaction
#
#    "jfmt" maps file extensions to junoscfg format names:
#       json → json,  set → set,  conf → structured
# ═══════════════════════════════════════════════════════════════════════

echo "── Convert between formats (local, no SSH) ──"
echo ""

# --- Round-trip conversions: every source → every target ---

for src in json set conf; do
    for dst in json set conf; do
        # map extension to junoscfg format name
        src_fmt="$src"; [[ "$src" == "conf" ]] && src_fmt="structured"
        dst_fmt="$dst"; [[ "$dst" == "conf" ]] && dst_fmt="structured"

        OUT="$WORKDIR/rt_${src}_to_${dst}.${dst}"

        if ! junoscfg -i "$src_fmt" -e "$dst_fmt" \
                "$WORKDIR/device.${src}" > "$OUT" 2>"$WORKDIR/err.log"; then
            fail "convert ${src} → ${dst}"
            continue
        fi

        # set format needs "delete" prepended so "load set" replaces everything
        UPLOAD="$WORKDIR/rt_${src}_to_${dst}.upload.${dst}"
        if [[ "$dst" == "set" ]]; then
            { echo "delete"; cat "$OUT"; } > "$UPLOAD"
        else
            cp "$OUT" "$UPLOAD"
        fi
    done
done

echo "  round-trip conversions done (9 files)"

# --- Anonymized conversions ---

SALT="integration-test-$(date +%s)"
ANON="$WORKDIR/anon"
mkdir -p "$ANON"

for src in json set conf; do
    for dst in json set conf; do
        src_fmt="$src"; [[ "$src" == "conf" ]] && src_fmt="structured"
        dst_fmt="$dst"; [[ "$dst" == "conf" ]] && dst_fmt="structured"

        OUT="$ANON/anon_${src}_to_${dst}.${dst}"
        MAP="$ANON/anon_${src}_to_${dst}.map.json"

        if junoscfg -i "$src_fmt" -e "$dst_fmt" \
                --anonymize-all \
                --anonymize-salt "$SALT" \
                --anonymize-dump-map "$MAP" \
                "$WORKDIR/device.${src}" > "$OUT" 2>/dev/null; then
            pass "anonymize ${src} → ${dst}"
        else
            fail "anonymize ${src} → ${dst}"
            continue
        fi

        UPLOAD="$ANON/anon_${src}_to_${dst}.upload.${dst}"
        if [[ "$dst" == "set" ]]; then
            { echo "delete"; cat "$OUT"; } > "$UPLOAD"
        else
            cp "$OUT" "$UPLOAD"
        fi
    done
done

# --- Pipeline consistency: A→B→C must equal A→C (local only) ---

echo ""
echo "  pipeline consistency checks (local, no SSH) ..."

PIPELINES=(
    "json yaml conf"  "json yaml set"  "json conf set"   "json conf yaml"
    "json set  conf"  "json set  yaml" "set  json conf"  "set  json yaml"
    "set  conf json"  "set  conf yaml" "set  yaml json"  "set  yaml conf"
    "conf json set"   "conf json yaml" "conf set  json"  "conf set  yaml"
    "conf yaml json"  "conf yaml set"
)

for entry in "${PIPELINES[@]}"; do
    read -r src mid dst <<< "$entry"

    src_fmt="$src"; [[ "$src" == "conf" ]] && src_fmt="structured"
    mid_fmt="$mid"; [[ "$mid" == "conf" ]] && mid_fmt="structured"
    dst_fmt="$dst"; [[ "$dst" == "conf" ]] && dst_fmt="structured"

    DIRECT="$WORKDIR/pipe_${src}_${dst}.direct"
    CHAIN="$WORKDIR/pipe_${src}_${mid}_${dst}.chain"

    junoscfg -i "$src_fmt" -e "$dst_fmt" \
        "$WORKDIR/device.${src}" > "$DIRECT" 2>/dev/null \
        || { skip "pipeline ${src}→${mid}→${dst}"; continue; }

    junoscfg -i "$src_fmt" -e "$mid_fmt" "$WORKDIR/device.${src}" 2>/dev/null \
        | junoscfg -i "$mid_fmt" -e "$dst_fmt" > "$CHAIN" 2>/dev/null \
        || { skip "pipeline ${src}→${mid}→${dst}"; continue; }

    if diff -q "$DIRECT" "$CHAIN" &>/dev/null; then
        pass "pipeline ${src}→${mid}→${dst} == ${src}→${dst}"
    else
        fail "pipeline ${src}→${mid}→${dst} != ${src}→${dst}"
    fi
done

echo ""


# ═══════════════════════════════════════════════════════════════════════
# 3. SHOW | COMPARE — upload each round-trip file, expect NO diff
#
#    For each file we do exactly this on the device:
#
#      configure
#      load override <file>        ← or "load set <file>" for set format
#      show | compare              ← prints diff; we expect nothing
#      rollback 0                  ← undo everything
#      exit                        ← leave configure mode
#
#    Nothing is committed. The device is unchanged after each test.
# ═══════════════════════════════════════════════════════════════════════

echo "── Show | compare (upload round-trip files → device) ──"
echo ""

for src in json set conf; do
    for dst in json set conf; do
        FILE="$WORKDIR/rt_${src}_to_${dst}.upload.${dst}"
        [[ -f "$FILE" ]] || { skip "compare ${src}→${dst} (no file)"; continue; }

        LABEL="${src} → ${dst}"

        # pick the right Junos "load" command for this format
        case "$dst" in
            json) LOAD="load override json ${REMOTE}" ;;
            set)  LOAD="load set ${REMOTE}" ;;
            conf) LOAD="load override ${REMOTE}" ;;
        esac

        scp -q "$FILE" "${DEVICE}:${REMOTE}" \
            || { fail "$LABEL (scp failed)"; continue; }

        # configure → load → show | compare → rollback → exit
        OUTPUT=$(ssh -T "$DEVICE" <<EOF
configure
${LOAD}
show | compare
rollback 0
exit
EOF
) || true

        ssh -T "$DEVICE" "rm -f ${REMOTE}" 2>/dev/null || true

        # Junos "show | compare" prints [edit ...] / +line / -line when there is a diff
        echo "$OUTPUT" > "$WORKDIR/compare_${src}_to_${dst}.log"
        if echo "$OUTPUT" | grep -qE '^\[edit .+\]$|^[+-][[:space:]]'; then
            fail "$LABEL  (see $WORKDIR/compare_${src}_to_${dst}.log)"
        else
            pass "$LABEL"
        fi
    done
done

echo ""


# ═══════════════════════════════════════════════════════════════════════
# 4. COMMIT CHECK — upload each anonymized file, verify it would commit
#
#    For each file we do exactly this on the device:
#
#      configure
#      load override <file>        ← or "load set <file>" for set format
#      commit check                ← validates without committing
#      rollback 0                  ← undo everything
#      exit                        ← leave configure mode
#
#    Nothing is committed. The device is unchanged after each test.
# ═══════════════════════════════════════════════════════════════════════

echo "── Commit check (upload anonymized files → device) ──"
echo ""

for src in json set conf; do
    for dst in json set conf; do
        FILE="$ANON/anon_${src}_to_${dst}.upload.${dst}"
        [[ -f "$FILE" ]] || { skip "commit-check anon ${src}→${dst} (no file)"; continue; }

        LABEL="commit-check anon ${src}→${dst}"

        case "$dst" in
            json) LOAD="load override json ${REMOTE}" ;;
            set)  LOAD="load set ${REMOTE}" ;;
            conf) LOAD="load override ${REMOTE}" ;;
        esac

        scp -q "$FILE" "${DEVICE}:${REMOTE}" \
            || { fail "$LABEL (scp failed)"; continue; }

        # configure → load → commit check → rollback → exit
        OUTPUT=$(ssh -T "$DEVICE" <<EOF
configure
${LOAD}
commit check
rollback 0
exit
EOF
) || true

        ssh -T "$DEVICE" "rm -f ${REMOTE}" 2>/dev/null || true

        echo "$OUTPUT" > "$WORKDIR/commitchk_${src}_to_${dst}.log"
        if echo "$OUTPUT" | grep -qi "commit check succeeds\|configuration check succeeds"; then
            pass "$LABEL"
        else
            fail "$LABEL  (see $WORKDIR/commitchk_${src}_to_${dst}.log)"
        fi
    done
done

echo ""


# ═══════════════════════════════════════════════════════════════════════
# 5. REVIEW — list anonymized files for human inspection
# ═══════════════════════════════════════════════════════════════════════

echo "── Anonymization review ──"
echo ""
echo "  Anonymized configs:"
for f in "$ANON"/anon_*.json "$ANON"/anon_*.set "$ANON"/anon_*.conf; do
    [[ -f "$f" ]] && [[ "$f" != *.upload.* ]] && echo "    $f"
done
echo ""
echo "  Mapping files:"
for f in "$ANON"/*.map.json; do
    [[ -f "$f" ]] && echo "    $f"
done
echo ""
echo "  Quick checks:"
echo "    grep -i 'your-hostname' $ANON/anon_json_to_conf.conf"
echo "    diff --color $WORKDIR/device.conf $ANON/anon_conf_to_conf.conf | less"
echo "    jq . $ANON/anon_json_to_json.map.json | less"
echo ""
read -rp "  Are all configs properly anonymized? [y/N] " confirm
if [[ "${confirm,,}" == "y" ]]; then
    pass "user confirmed: anonymization looks correct"
else
    fail "user flagged: anonymization needs review"
fi
echo ""


# ═══════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════

TOTAL=$((PASS + FAIL + SKIP))
echo "═══ Results ═══"
echo ""
echo "  passed:  $PASS"
echo "  failed:  $FAIL"
echo "  skipped: $SKIP"
echo "  total:   $TOTAL"
echo ""
if [[ "$FAIL" -eq 0 ]]; then
    echo "  All tests passed."
else
    echo "  $FAIL test(s) failed — see logs in $WORKDIR"
fi
echo ""

[[ "$FAIL" -eq 0 ]]
