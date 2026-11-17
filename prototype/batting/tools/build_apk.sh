#!/usr/bin/env bash
# 타격 시험판 APK 만들기 (클라우드 컨테이너용). 컨테이너가 새로 뜨면 도구를 다시 받음.
# 사용: bash prototype/batting/tools/build_apk.sh <버전 이름, 예: 0.2>
# 받는 것: Godot 4.7.2(약 60MB), 내보내기 파일(약 1.3GB, GitHub), 안드로이드 SDK 일부(dl.google.com)
# 서명: 시험용 디버그 키를 /home/user/tools/keys 에 만듦 (저장소에 넣지 않음).
#   키가 바뀌면 폰에서 앞 버전을 지우고 설치해야 함.
set -euo pipefail
VER="${1:?버전 이름을 주세요 (예: 0.2)}"
T=/home/user/tools
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
G=$T/godot/Godot_v4.7.2-stable_linux.x86_64
mkdir -p $T/godot $T/dl $T/keys
[ -x "$G" ] || { curl -sSL -o $T/dl/godot.zip https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip && unzip -qo $T/dl/godot.zip -d $T/godot; }
TPL=~/.local/share/godot/export_templates/4.7.2.stable
if [ ! -f $TPL/android_debug.apk ]; then
  curl -sSL -o $T/dl/templates.tpz https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_export_templates.tpz
  mkdir -p $TPL && unzip -qo $T/dl/templates.tpz -d $T/dl/tpl && mv $T/dl/tpl/templates/* $TPL/ && rm -rf $T/dl/tpl
fi
SDK=$T/android-sdk
if [ ! -x $SDK/build-tools/35.0.0/apksigner ]; then
  curl -sSL -o $T/dl/cmdtools.zip https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
  mkdir -p $SDK/cmdline-tools && unzip -qo $T/dl/cmdtools.zip -d $SDK/cmdline-tools && mv $SDK/cmdline-tools/cmdline-tools $SDK/cmdline-tools/latest
  yes | $SDK/cmdline-tools/latest/bin/sdkmanager --sdk_root=$SDK "platform-tools" "build-tools;35.0.0" "platforms;android-35" >/dev/null
fi
KS=$T/keys/debug.keystore
[ -f $KS ] || keytool -genkeypair -keystore $KS -storepass android -alias androiddebugkey -keypass android \
  -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
JH=$(dirname "$(dirname "$(readlink -f "$(which java)")")")
mkdir -p ~/.config/godot
cat > ~/.config/godot/editor_settings-4.7.tres <<EOS
[gd_resource type="EditorSettings" format=3]

[resource]
export/android/android_sdk_path = "$SDK"
export/android/java_sdk_path = "$JH"
EOS
# 버전 이름·번호를 내보내기 설정에 넣음 (번호 = 0.2 → 2, 0.10 → 10)
CODE=$(echo "$VER" | awk -F. '{print $1*100+$2}')
sed -i "s/^version\/name=.*/version\/name=\"$VER\"/; s/^version\/code=.*/version\/code=$CODE/" "$PROJ/export_presets.cfg"
mkdir -p "$PROJ/export" "$PROJ/builds"
GODOT_ANDROID_KEYSTORE_DEBUG_PATH=$KS GODOT_ANDROID_KEYSTORE_DEBUG_USER=androiddebugkey GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD=android \
  "$G" --headless --path "$PROJ" --export-debug "Android" export/batting-prototype.apk
$SDK/build-tools/35.0.0/apksigner verify "$PROJ/export/batting-prototype.apk"
cp "$PROJ/export/batting-prototype.apk" "$PROJ/builds/batting-prototype-$VER.apk"
echo "완성: $PROJ/builds/batting-prototype-$VER.apk"
