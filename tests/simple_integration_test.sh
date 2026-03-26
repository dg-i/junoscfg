#!/usr/bin/env bash
#
# simple_integration_test.sh — Minimal live-device test for junoscfg
#
# SSHs to a real Junos device. Every SSH command is visible below.
#
#   SAFETY:  No "commit" anywhere. Every session ends with "rollback 0".
#
# Usage:  ./simple_integration_test.sh [options] <hostname>
#
# Options:
#   --quiet-ssh                       Suppress SSH warnings (post-quantum etc.)
#   --anonymize-salt SALT             Salt for deterministic anonymization
#   --anonymize-networks SPECS        Comma-separated subnet specs (or "auto")
#   --anonymize-network-file FILE     File with one subnet spec per line
#
set -euo pipefail

# ── Options ───────────────────────────────────────────────────────────

usage() {
    cat <<'EOF'
Usage: simple_integration_test.sh [options] <hostname>

Minimal live-device integration test for junoscfg.
SSHs to a real Junos device — no "commit" anywhere, every session ends
with "rollback 0".

Options:
  --quiet-ssh                       Suppress SSH warnings (post-quantum etc.)
  --anonymize-salt SALT             Salt for deterministic anonymization
  --anonymize-networks SPECS        Comma-separated subnet specs (or "auto")
                                    Prevents broadcast/network address collisions
  --anonymize-network-file FILE     File with one subnet spec per line
  -h, -?, --help                    Show this help

Examples:
  ./simple_integration_test.sh myswitch
  ./simple_integration_test.sh --quiet-ssh myswitch
  ./simple_integration_test.sh --anonymize-networks auto myswitch
  ./simple_integration_test.sh --anonymize-network-file subnets.txt myswitch
EOF
    exit 0
}

SSH_OPTS=""
ANON_SALT="integration-test-$$"
ANON_EXTRA=""
while [[ "${1:-}" == --* || "${1:-}" == -h || "${1:-}" == "-?" ]]; do
    case "$1" in
        -h|-\?|--help) usage ;;
        --quiet-ssh) SSH_OPTS="-o LogLevel=ERROR"; shift ;;
        --anonymize-salt) ANON_SALT="$2"; shift 2 ;;
        --anonymize-networks) ANON_EXTRA="$ANON_EXTRA --anonymize-networks $2"; shift 2 ;;
        --anonymize-network-file) ANON_EXTRA="$ANON_EXTRA --anonymize-network-file $2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

DEVICE="${1:?Usage: $0 [options] <hostname>}"
WORKDIR=$(mktemp -d "/tmp/junoscfg_test.XXXXXX")
REMOTE="/var/tmp/junoscfg_test_upload"
PASS=0
FAIL=0
NOTICE=0

# cleanup only removes workdir if all tests pass (or user says so)
trap 'rm -rf "$WORKDIR"' EXIT

echo ""
echo "junoscfg simple integration test"
echo "device:  $DEVICE"
echo "workdir: $WORKDIR"
echo "salt:    $ANON_SALT"
[[ -n "$ANON_EXTRA" ]] && echo "anon:   $ANON_EXTRA"
echo ""


# ── Fetch (read-only) ─────────────────────────────────────────────────

echo "── Fetch ──"

echo "  fetching json from $DEVICE ..."
ssh -T $SSH_OPTS "$DEVICE" "show configuration | display json | no-more" > "$WORKDIR/device.json"
echo "  fetching set from $DEVICE ..."
ssh -T $SSH_OPTS "$DEVICE" "show configuration | display set | no-more"  > "$WORKDIR/device.set"
echo "  fetching conf from $DEVICE ..."
ssh -T $SSH_OPTS "$DEVICE" "show configuration | no-more"                > "$WORKDIR/device.conf"

echo "  json $(wc -l < "$WORKDIR/device.json") lines"
echo "  set  $(wc -l < "$WORKDIR/device.set") lines"
echo "  conf $(wc -l < "$WORKDIR/device.conf") lines"
echo ""


# ── Convert (local, no SSH) ───────────────────────────────────────────

echo "── Convert ──"

echo "  json → conf ..."
junoscfg -i json -e structured "$WORKDIR/device.json" > "$WORKDIR/rt_json.conf"

echo "  json → set ..."
junoscfg -i json -e set "$WORKDIR/device.json" > "$WORKDIR/rt_json.set"

echo "  conf → json ..."
junoscfg -i structured -e json "$WORKDIR/device.conf" > "$WORKDIR/rt_conf.json"

echo "  set → json ..."
junoscfg -i set -e json "$WORKDIR/device.set" > "$WORKDIR/rt_set.json"

echo "  4 round-trip files ready"

echo "  anonymize json → conf ..."
junoscfg -i json -e structured --anonymize-all --anonymize-salt "$ANON_SALT" \
    $ANON_EXTRA "$WORKDIR/device.json" > "$WORKDIR/anon.conf"

echo "  anonymize json → json ..."
junoscfg -i json -e json --anonymize-all --anonymize-salt "$ANON_SALT" \
    $ANON_EXTRA "$WORKDIR/device.json" > "$WORKDIR/anon.json"

echo "  anonymize json → set ..."
junoscfg -i json -e set --anonymize-all --anonymize-salt "$ANON_SALT" \
    $ANON_EXTRA "$WORKDIR/device.json" > "$WORKDIR/anon.set"

echo "  3 anonymized files ready"
echo ""


# ── Show | compare (expect no diff) ──────────────────────────────────
#   Nothing is committed. Every session ends with rollback 0.
#
#   Diff lines that only add/remove comments (/* ... */) are treated as
#   warnings, not failures — comments cannot survive format round-trips.

echo "── Show | compare ──"

# check_show_compare LOG FILE — evaluate show|compare output
#   PASS = no diff lines at all
#   NOTICE = only comment diffs (/* ... */)
#   FAIL = real config diffs
check_show_compare() {
    local log="$1" file="$2"
    # any diff lines at all?
    if ! grep -qE '^\[edit .+\]$|^[+-][[:space:]]' "$log"; then
        echo "  PASS  $file"; PASS=$((PASS + 1)); return
    fi
    # are ALL +/- lines just comments?
    if ! grep -E '^[+-][[:space:]]' "$log" | grep -qvE '^[+-][[:space:]]+(\/\*.*\*\/|$)'; then
        echo "  NOTICE  $file  (comment-only diff)"; NOTICE=$((NOTICE + 1)); return
    fi
    echo "  FAIL  $file  (log: $log)"; FAIL=$((FAIL + 1))
}

# -- json files: load override json --
for FILE in rt_conf.json rt_set.json; do
    echo "  show | compare on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.show_compare.log"
    CMD="start shell command \"cli -c 'configure; load override json ${REMOTE}; show | compare; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: show | compare on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    check_show_compare "$LOG" "$FILE"
done

# -- conf files: load override --
for FILE in rt_json.conf; do
    echo "  show | compare on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.show_compare.log"
    CMD="start shell command \"cli -c 'configure; load override ${REMOTE}; show | compare; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: show | compare on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    check_show_compare "$LOG" "$FILE"
done

# -- set files: load set --
for FILE in rt_json.set; do
    echo "  show | compare on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.show_compare.log"
    CMD="start shell command \"cli -c 'configure; delete; load set ${REMOTE}; show | compare; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: show | compare on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    check_show_compare "$LOG" "$FILE"
done

echo ""


# ── Commit check (anonymized files) ──────────────────────────────────
#   Nothing is committed. Every session ends with rollback 0.

echo "── Commit check ──"

# -- json files: load override json --
for FILE in anon.json; do
    echo "  commit check on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.commit_check.log"
    CMD="start shell command \"cli -c 'configure; load override json ${REMOTE}; commit check; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: commit check on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    if grep -qi "commit check succeeds\|configuration check succeeds" "$LOG"; then
        echo "  PASS  $FILE"; PASS=$((PASS + 1))
    else
        echo "  FAIL  $FILE  (log: $LOG)"; FAIL=$((FAIL + 1))
    fi
done

# -- conf files: load override --
for FILE in anon.conf; do
    echo "  commit check on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.commit_check.log"
    CMD="start shell command \"cli -c 'configure; load override ${REMOTE}; commit check; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: commit check on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    if grep -qi "commit check succeeds\|configuration check succeeds" "$LOG"; then
        echo "  PASS  $FILE"; PASS=$((PASS + 1))
    else
        echo "  FAIL  $FILE  (log: $LOG)"; FAIL=$((FAIL + 1))
    fi
done

# -- set files: load set --
for FILE in anon.set; do
    echo "  commit check on $DEVICE for $FILE ..."
    LOG="$WORKDIR/${FILE}.commit_check.log"
    CMD="start shell command \"cli -c 'configure; delete; load set ${REMOTE}; commit check; rollback 0; exit; file delete ${REMOTE}'\""
    echo "# test: commit check on $DEVICE for $FILE" > "$LOG"
    echo "# scp $FILE ${DEVICE}:${REMOTE}" >> "$LOG"
    echo "# ssh -T $SSH_OPTS $DEVICE $CMD" >> "$LOG"
    echo "# ---" >> "$LOG"
    scp -q $SSH_OPTS "$WORKDIR/$FILE" "${DEVICE}:${REMOTE}"
    ssh -T $SSH_OPTS "$DEVICE" "$CMD" >> "$LOG" 2>&1 || true
    if grep -qi "commit check succeeds\|configuration check succeeds" "$LOG"; then
        echo "  PASS  $FILE"; PASS=$((PASS + 1))
    else
        echo "  FAIL  $FILE  (log: $LOG)"; FAIL=$((FAIL + 1))
    fi
done

echo ""


# ── Summary ───────────────────────────────────────────────────────────

echo "passed: $PASS  failed: $FAIL  warnings: $NOTICE"
echo ""

echo "  All logs:"
for f in "$WORKDIR"/*.log; do
    [[ -f "$f" ]] && echo "    $f"
done

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "  Failed logs:"
    for f in "$WORKDIR"/*.log; do
        [[ -f "$f" ]] && grep -qE '^\[edit .+\]$|^[+-][[:space:]]|error:' "$f" && echo "    $f"
    done
    echo ""
    read -rp "  Keep workdir for debugging? [Y/n] " keep
    if [[ "${keep,,}" == "n" ]]; then
        echo "  cleaning up $WORKDIR"
    else
        # disable the cleanup trap
        trap - EXIT
        echo "  files kept in $WORKDIR"
        echo "  to clean up:  rm -rf $WORKDIR"
    fi
    exit 1
fi
