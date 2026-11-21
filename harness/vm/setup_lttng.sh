#!/usr/bin/env bash
# Build LTTng 2.16.0 (modules, UST, tools) from source on the measurement VM.
# Ubuntu 24.04's lttng-modules-dkms 2.14.0 does not build on the GCP kernels
# we tried (7.0.0-1017-gcp and 6.8.0-1074-gcp): trace_hrtimer_start type clash.
# UST 2.16 needs liburcu >= 0.15; Ubuntu 24.04 ships 0.14.0, so urcu is built too.
# lttng-tools 2.16 needs libbabeltrace2 >= 2.1.0; Ubuntu ships 2.0.x, so
# babeltrace2 is built too, with Python bindings (bt2) for offline counting.
set -euo pipefail
V=2.16.0
URCU=0.15.7
BT=2.1.2
SRC=/opt/lttng-src
export DEBIAN_FRONTEND=noninteractive

# remove the distro LTTng packages so versions cannot mix
sudo apt-get purge -y -qq lttng-modules-dkms lttng-tools liblttng-ctl0 liblttng-ust1t64 2>/dev/null || true
sudo dkms remove lttng-modules/2.14.0 --all 2>/dev/null || true

sudo apt-get install -y -qq build-essential pkg-config libtool autoconf automake bison flex \
  libpopt-dev libxml2-dev uuid-dev libnuma-dev libzstd-dev \
  linux-headers-"$(uname -r)" curl bzip2 libglib2.0-dev libdw-dev libelf-dev \
  python3-dev python3-setuptools swig

sudo apt-get purge -y -qq liburcu-dev babeltrace2 python3-bt2 libbabeltrace2-0 2>/dev/null || true

sudo mkdir -p "$SRC"; sudo chown "$USER" "$SRC"; cd "$SRC"
f=userspace-rcu-$URCU.tar.bz2
[ -f "$f" ] || curl -sfLO "https://lttng.org/files/urcu/$f"
[ -f "$f.sha256" ] || curl -sfLO "https://lttng.org/files/urcu/$f.sha256"
sha256sum -c "$f.sha256"
rm -rf "userspace-rcu-$URCU"; tar xjf "$f"
cd "userspace-rcu-$URCU"
./configure >"$SRC/urcu-build.log" 2>&1
make -j"$(nproc)" >>"$SRC/urcu-build.log" 2>&1
sudo make install >>"$SRC/urcu-build.log" 2>&1
sudo ldconfig
cd "$SRC"

f=babeltrace2-$BT.tar.bz2
[ -f "$f" ] || curl -sfLO "https://www.efficios.com/files/babeltrace/$f"
[ -f "$f.sha256" ] || curl -sfLO "https://www.efficios.com/files/babeltrace/$f.sha256"
sha256sum -c "$f.sha256"
rm -rf "babeltrace2-$BT"; tar xjf "$f"
cd "babeltrace2-$BT"
./configure --enable-python-bindings --disable-man-pages >"$SRC/bt2-build.log" 2>&1
make -j"$(nproc)" >>"$SRC/bt2-build.log" 2>&1
sudo make install >>"$SRC/bt2-build.log" 2>&1
sudo ldconfig
cd "$SRC"

for p in modules ust tools; do
  f=lttng-$p-$V.tar.bz2
  [ -f "$f" ] || curl -sfLO "https://lttng.org/files/lttng-$p/$f"
  [ -f "$f.sha256" ] || curl -sfLO "https://lttng.org/files/lttng-$p/$f.sha256"
  sha256sum -c "$f.sha256"
  rm -rf "lttng-$p-$V"; tar xjf "$f"
done

cd "$SRC/lttng-modules-$V"
make -j"$(nproc)" >"$SRC/modules-build.log" 2>&1
sudo make modules_install >>"$SRC/modules-build.log" 2>&1
sudo depmod -a

cd "$SRC/lttng-ust-$V"
./configure --disable-man-pages >"$SRC/ust-build.log" 2>&1
make -j"$(nproc)" >>"$SRC/ust-build.log" 2>&1
sudo make install >>"$SRC/ust-build.log" 2>&1
sudo ldconfig

cd "$SRC/lttng-tools-$V"
./configure --disable-man-pages >"$SRC/tools-build.log" 2>&1
make -j"$(nproc)" >>"$SRC/tools-build.log" 2>&1
sudo make install >>"$SRC/tools-build.log" 2>&1
sudo ldconfig

sudo modprobe lttng-tracer
lttng --version
modinfo -F version lttng-tracer
babeltrace2 --version | head -1
python3 -c "import bt2; print('bt2', bt2.__version__)"
