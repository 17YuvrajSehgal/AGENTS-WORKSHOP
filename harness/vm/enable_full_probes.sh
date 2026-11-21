#!/usr/bin/env bash
# Enable the LTTng probes that Ubuntu's trimmed kernel-headers package
# disables (kmem, x86-exceptions = page faults, compaction, ext4, kvm, ...).
# lttng-modules' Kbuild skips a probe when a kernel-internal header is
# missing and says: "Use full kernel source tree to enable it."
# We copy exactly the missing files from the EXACT running kernel's Ubuntu
# source (linux-gcp-7.0 7.0.0-1017.19~24.04.1, downloaded with apt-get
# source into /opt/kernel-src) into the headers tree, then rebuild
# lttng-modules 2.16.0.
set -euo pipefail
K=$(uname -r)
H=/usr/src/linux-headers-$K
SRCDIR=/opt/kernel-src
PROBES=/opt/lttng-src/lttng-modules-2.16.0/src/probes
LOG=/opt/lttng-src/modules-rebuild.log

sudo apt-get install -y -qq dpkg-dev >/dev/null
cd "$SRCDIR"
[ -d linux-gcp-7.0-7.0.0 ] || dpkg-source -x --no-check linux-gcp-7.0_7.0.0-1017.19~24.04.1.dsc linux-gcp-7.0-7.0.0 > extract.log 2>&1
S=$SRCDIR/linux-gcp-7.0-7.0.0

# every "$(srctree)/<path>" the probe Kbuild checks for
mapfile -t deps < <(grep -oE '\$\(srctree\)/[A-Za-z0-9_./-]+' "$PROBES/Kbuild" | sed 's|\$(srctree)/||' | sort -u)
copied=0
for f in "${deps[@]}"; do
  if [ ! -e "$H/$f" ]; then
    if [ -e "$S/$f" ]; then
      sudo mkdir -p "$(dirname "$H/$f")"
      sudo cp "$S/$f" "$H/$f"
      echo "copied $f"; copied=$((copied + 1))
    else
      echo "not in source either: $f"
    fi
  fi
done
echo "copied $copied header files from the exact kernel source"

cd /opt/lttng-src/lttng-modules-2.16.0
make clean >/dev/null 2>&1 || true
make -j"$(nproc)" > "$LOG" 2>&1
sudo make modules_install >> "$LOG" 2>&1
sudo depmod -a
grep -E 'warning File' "$LOG" | sed 's/.*warning //' || true
