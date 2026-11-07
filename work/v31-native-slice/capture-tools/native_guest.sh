#!/system/bin/sh
# Run an ARM64 Linux tool directly on Android's kernel, without FEX or proot.
# All mounts exist only in this process's private mount namespace.
set -eu
ROOT=/data/user/0/com.droiddeck.launcher/files/linuxfs
if [ "${OA_PRIVATE_NAMESPACE:-}" != 1 ]; then
    exec unshare -m /system/bin/env OA_PRIVATE_NAMESPACE=1 /system/bin/sh "$0" "$@"
fi
/data/adb/ksu/bin/busybox mount --make-rprivate /
mount --bind /dev "$ROOT/dev"
mount --bind /proc "$ROOT/proc"
mount --bind /sys "$ROOT/sys"
mount --bind "$ROOT/root/oa-native-tools/empty-preload" "$ROOT/etc/ld.so.preload"
# No game launch options, installed drivers, or persistent mounts are changed.
exec /system/bin/env -i HOME=/root PATH=/usr/bin:/bin \
    VK_DRIVER_FILES=/root/oa-native-tools/driver.json \
    VK_ICD_FILENAMES=/root/oa-native-tools/driver.json \
    DISPLAY=:1 /system/bin/chroot "$ROOT" "$@"
