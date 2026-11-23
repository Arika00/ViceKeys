#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
WORK="$ROOT/work"
SRC="$WORK/chiaki-ng"
OUT="$ROOT/out"
mkdir -p "$WORK" "$OUT"

# MSYS2 packages for the upstream Windows x64 build.
pacman -S --needed --noconfirm git diffutils make unzip zip pactoys
pacboy -S --needed --noconfirm \
  ca-certificates:p cc:p cmake:p curl:p fast_float:p fftw:p json-c:p \
  libevent:p lcms2:p libdovi:p meson:p miniupnpc:p gcc:p nasm:p ninja:p \
  openssl:p opus:p pkgconf:p protobuf:p python:p python-psutil:p \
  python-glad:p python-jinja:p python-protobuf:p qt6-base:p qt6-declarative:p \
  qt6-svg:p shaderc:p speexdsp:p spirv-cross:p vulkan:p vulkan-headers:p

if [[ ! -d "$SRC/.git" ]]; then
  git clone --branch v1.10.1 --depth 1 --recurse-submodules https://github.com/chiaki-ng/chiaki-ng.git "$SRC"
else
  git -C "$SRC" fetch --tags --force
  git -C "$SRC" checkout --detach v1.10.1
  git -C "$SRC" submodule update --init --recursive
  # Keep the upstream working tree pristine before reapplying the patch.
  git -C "$SRC" reset --hard v1.10.1
  git -C "$SRC" clean -fd
  rm -f "$SRC/.vickey-patched"
fi

python "$ROOT/scripts/apply-vickey.py" "$SRC"
cd "$SRC"

# Match the upstream Windows build pipeline so the Remote Play engine remains intact.
LIBPLACEBO_VERSION=3be579e6c7f6b421d9ac3ab4860edc437c50b3eb scripts/build-libplacebo-windows.sh
curl -fL -o ffmpeg-win64.zip https://github.com/streetpea/FFmpeg-Builds/releases/download/latest/ffmpeg-n9.0-latest-win64-gpl-shared-9.0.zip
unzip -oq ffmpeg-win64.zip
cp -a ffmpeg-n9.0-latest-win64-gpl-shared-9.0/bin/. /mingw64/bin/
cp -a ffmpeg-n9.0-latest-win64-gpl-shared-9.0/include/. /mingw64/include/
cp -a ffmpeg-n9.0-latest-win64-gpl-shared-9.0/lib/. /mingw64/lib/
INSTALL_PREFIX=/mingw64 scripts/build-sdl2-compat.sh .
INSTALL_PREFIX=/mingw64 scripts/build-hidapi.sh .
cp /mingw64/lib/pkgconfig/sdl2-compat.pc /mingw64/lib/pkgconfig/sdl2.pc

cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCHIAKI_ENABLE_CLI=OFF
cmake --build build --config Release --clean-first --target chiaki

rm -rf "$OUT/ViceKey-Windows"
./scripts/deploy-windows-msys2.sh "$OUT/ViceKey-Windows" build/gui/chiaki.exe \
  "$SRC/build/third-party/cpp-steam-tools" /mingw64 gui/src/qml
cp "$OUT/ViceKey-Windows/chiaki.exe" "$OUT/ViceKey-Windows/ViceKey.exe"
cp "$ROOT/README.md" "$OUT/ViceKey-Windows/README.txt"
cp "$ROOT/LICENCE-NOTICE.txt" "$OUT/ViceKey-Windows/LICENCE-NOTICE.txt"
if [[ -f "$SRC/LICENSE" ]]; then cp "$SRC/LICENSE" "$OUT/ViceKey-Windows/LICENSE.txt"; fi
cp "$ROOT/profiles/gta6_azerty.json" "$OUT/ViceKey-Windows/"
cp "$ROOT/profiles/gta6_qwerty.json" "$OUT/ViceKey-Windows/"
cd "$OUT"
rm -f ViceKey-Windows.zip
zip -qr ViceKey-Windows.zip ViceKey-Windows
printf '\nBuild complete: %s\n' "$OUT/ViceKey-Windows.zip"