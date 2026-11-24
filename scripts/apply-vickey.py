#!/usr/bin/env python3
"""Apply the ViceKey input/UI patch to a clean chiaki-ng v1.10.1 checkout.

The patcher is deliberately strict: if upstream source has drifted, it stops
instead of silently producing a partially patched build.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor in {path}, found {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8", newline="")


def insert_after(path: Path, anchor: str, addition: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(anchor)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor in {path}, found {count}")
    path.write_text(source.replace(anchor, anchor + addition, 1), encoding="utf-8", newline="")


def replace_section(path: Path, start: str, end: str, replacement: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError(f"{label}: expected unique section boundaries in {path}")
    start_index = source.index(start)
    end_index = source.index(end, start_index + len(start))
    if end_index <= start_index:
        raise RuntimeError(f"{label}: invalid section boundaries in {path}")
    path.write_text(source[:start_index] + replacement + source[end_index:], encoding="utf-8", newline="")


def patch(root: Path) -> None:
    gui = root / "gui"
    # Native wheel events are sent directly to StreamSession while gameplay has focus.
    settings_h = gui / "include/settings.h"
    settings_cpp = gui / "src/settings.cpp"
    qmlsettings_h = gui / "include/qmlsettings.h"
    qmlsettings_cpp = gui / "src/qmlsettings.cpp"
    stream_h = gui / "include/streamsession.h"
    # QWheelEvent is used by the Tab+wheel weapon-cycle layer.
    stream_cpp = gui / "src/streamsession.cpp"
    mainwindow_cpp = gui / "src/qmlmainwindow.cpp"
    settings_qml = gui / "src/qml/SettingsDialog.qml"
    main_cpp = gui / "src/main.cpp"

    # Persistent ViceKey profile and mouse calibration settings.
    insert_after(settings_h,
        "\t\tvoid SetKeyboardEnabled(bool enabled);\n",
        "\t\tQString GetViceKeyLayout() const;\n"
        "\t\tvoid SetViceKeyLayout(const QString &layout);\n"
        "\t\tdouble GetViceKeySensitivity() const;\n"
        "\t\tvoid SetViceKeySensitivity(double value);\n"
        "\t\tdouble GetViceKeyAimSensitivity() const;\n"
        "\t\tvoid SetViceKeyAimSensitivity(double value);\n"
        "\t\tQString GetViceKeyLanguage() const;\n"
        "\t\tvoid SetViceKeyLanguage(const QString &language);\n",
        "settings API")

    insert_after(settings_cpp,
        "void Settings::SetKeyboardEnabled(bool enabled)\n{\n\tsettings.setValue(\"settings/keyboard_enabled\", enabled);\n}\n",
        "\nQString Settings::GetViceKeyLayout() const\n{\n\treturn settings.value(\"vickey/layout\", \"AZERTY\").toString();\n}\n"
        "void Settings::SetViceKeyLayout(const QString &layout)\n{\n\tconst QString normalized = layout.compare(\"QWERTY\", Qt::CaseInsensitive) == 0 ? \"QWERTY\" : \"AZERTY\";\n\tsettings.setValue(\"vickey/layout\", normalized);\n}\n"
        "double Settings::GetViceKeySensitivity() const\n{\n\treturn settings.value(\"vickey/sensitivity\", 1.0).toDouble();\n}\n"
        "void Settings::SetViceKeySensitivity(double value)\n{\n\tsettings.setValue(\"vickey/sensitivity\", qBound(0.01, value, 100.0));\n}\n"
        "double Settings::GetViceKeyAimSensitivity() const\n{\n\treturn settings.value(\"vickey/aim_sensitivity\", 0.7).toDouble();\n}\n"
        "void Settings::SetViceKeyAimSensitivity(double value)\n{\n\tsettings.setValue(\"vickey/aim_sensitivity\", qBound(0.01, value, 100.0));\n}\n"
        "QString Settings::GetViceKeyLanguage() const\n{\n\\treturn settings.value(\\"vickey/language\\", \\"FR\\").toString();\n}\n"
        "void Settings::SetViceKeyLanguage(const QString &language)\n{\n\\tsettings.setValue(\\"vickey/language\\", language.compare(\\"EN\\", Qt::CaseInsensitive) == 0 ? \\"EN\\" : \\"FR\\");\n}\n",
        "settings implementation")

    insert_after(qmlsettings_h,
        "    Q_PROPERTY(bool keyboardEnabled READ keyboardEnabled WRITE setKeyboardEnabled NOTIFY keyboardEnabledChanged)\n",
        "    Q_PROPERTY(QString viceKeyLayout READ viceKeyLayout WRITE setViceKeyLayout NOTIFY viceKeyLayoutChanged)\n"
        "    Q_PROPERTY(double viceKeySensitivity READ viceKeySensitivity WRITE setViceKeySensitivity NOTIFY viceKeySensitivityChanged)\n"
        "    Q_PROPERTY(double viceKeyAimSensitivity READ viceKeyAimSensitivity WRITE setViceKeyAimSensitivity NOTIFY viceKeyAimSensitivityChanged)\n"
        "    Q_PROPERTY(QString viceKeyLanguage READ viceKeyLanguage WRITE setViceKeyLanguage NOTIFY viceKeyLanguageChanged)\n"
        "    Q_PROPERTY(int viceKeyOverlayKey READ viceKeyOverlayKey WRITE setViceKeyOverlayKey NOTIFY viceKeyOverlayKeyChanged)\n",
        "QML properties")
    insert_after(qmlsettings_h,
        "    void setKeyboardEnabled(bool enabled);\n",
        "    QString viceKeyLayout() const;\n"
        "    void setViceKeyLayout(const QString &layout);\n"
        "    double viceKeySensitivity() const;\n"
        "    void setViceKeySensitivity(double value);\n"
        "    double viceKeyAimSensitivity() const;\n"
        "    void setViceKeyAimSensitivity(double value);\n"
        "    QString viceKeyLanguage() const;\n"
        "    void setViceKeyLanguage(const QString &language);\n"
        "    int viceKeyOverlayKey() const;\n"
        "    void setViceKeyOverlayKey(int key);\n",
        "QML settings methods")
    insert_after(qmlsettings_h,
        "    Q_INVOKABLE void importSettings();\n",
        "    Q_INVOKABLE bool exportViceKeyProfile();\n"
        "    Q_INVOKABLE bool importViceKeyProfile();\n",
        "profile import and export invokables")

    insert_after(qmlsettings_h,
        "    void keyboardEnabledChanged();\n",
        "    void viceKeyLayoutChanged();\n"
        "    void viceKeySensitivityChanged();\n"
        "    void viceKeyAimSensitivityChanged();\n"
        "    void viceKeyLanguageChanged();\n"
        "    void viceKeyOverlayKeyChanged();\n",
        "QML settings signals")

    insert_after(qmlsettings_cpp,
        "#include <QProcess>\n",
        "#include <QFile>\n"
        "#include <QJsonDocument>\n"
        "#include <QJsonObject>\n"
        "#include <QJsonParseError>\n",
        "profile JSON includes")

    insert_after(qmlsettings_cpp,
        "void QmlSettings::setKeyboardEnabled(bool enabled)\n{\n    settings->SetKeyboardEnabled(enabled);\n    emit keyboardEnabledChanged();\n}\n",
        "\nQString QmlSettings::viceKeyLayout() const\n{\n    return settings->GetViceKeyLayout();\n}\n"
        "void QmlSettings::setViceKeyLayout(const QString &layout)\n{\n    settings->SetViceKeyLayout(layout);\n    emit viceKeyLayoutChanged();\n}\n"
        "double QmlSettings::viceKeySensitivity() const\n{\n    return settings->GetViceKeySensitivity();\n}\n"
        "void QmlSettings::setViceKeySensitivity(double value)\n{\n    settings->SetViceKeySensitivity(value);\n    emit viceKeySensitivityChanged();\n}\n"
        "double QmlSettings::viceKeyAimSensitivity() const\n{\n    return settings->GetViceKeyAimSensitivity();\n}\n"
        "void QmlSettings::setViceKeyAimSensitivity(double value)\n{\n    settings->SetViceKeyAimSensitivity(value);\n    emit viceKeyAimSensitivityChanged();\n}\n"
        "QString QmlSettings::viceKeyLanguage() const\n{\n    return settings->GetViceKeyLanguage();\n}\n"
        "void QmlSettings::setViceKeyLanguage(const QString &language)\n{\n    settings->SetViceKeyLanguage(language);\n    emit viceKeyLanguageChanged();\n}\n"
        "int QmlSettings::viceKeyOverlayKey() const\n{\n    return settings->GetViceKeyOverlayKey();\n}\n"
        "void QmlSettings::setViceKeyOverlayKey(int key)\n{\n    settings->SetViceKeyOverlayKey(key);\n    emit viceKeyOverlayKeyChanged();\n}\n"
        "bool QmlSettings::exportViceKeyProfile()\n{\n"
        "    const QString path = QFileDialog::getSaveFileName(nullptr, tr(\"Export ViceKey profile\"), QString(), tr(\"ViceKey profile (*.json)\"));\n"
        "    if (path.isEmpty()) return false;\n"
        "    QJsonObject root; root.insert(\"version\", 1); root.insert(\"layout\", settings->GetViceKeyLayout());\n"
        "    root.insert(\"sensitivity\", settings->GetViceKeySensitivity()); root.insert(\"aimSensitivity\", settings->GetViceKeyAimSensitivity()); root.insert(\"overlayKey\", settings->GetViceKeyOverlayKey());\n"
        "    QJsonObject keys; const auto keyMap = settings->GetViceKeyMappings(); for (auto it = keyMap.cbegin(); it != keyMap.cend(); ++it) keys.insert(QString::number(it.key()), it.value()); root.insert(\"keymap\", keys);\n"
        "    QJsonObject mouse; const auto mouseMap = settings->GetViceKeyMouseMappings(); for (auto it = mouseMap.cbegin(); it != mouseMap.cend(); ++it) mouse.insert(QString::number(it.key()), it.value()); root.insert(\"mousemap\", mouse);\n"
        "    QFile file(path); if (!file.open(QIODevice::WriteOnly | QIODevice::Truncate)) return false; file.write(QJsonDocument(root).toJson(QJsonDocument::Indented)); return true;\n"
        "}\n"
        "bool QmlSettings::importViceKeyProfile()\n{\n"
        "    const QString path = QFileDialog::getOpenFileName(nullptr, tr(\"Import ViceKey profile\"), QString(), tr(\"ViceKey profile (*.json)\"));\n"
        "    if (path.isEmpty()) return false;\n"
        "    QFile file(path); if (!file.open(QIODevice::ReadOnly)) return false;\n"
        "    QJsonParseError parseError; const QJsonDocument document = QJsonDocument::fromJson(file.readAll(), &parseError);\n"
        "    if (parseError.error != QJsonParseError::NoError || !document.isObject()) return false;\n"
        "    const QJsonObject root = document.object(); if (root.value(\"version\").toInt() != 1) return false;\n"
        "    const QString layout = root.value(\"layout\").toString(); if (layout != \"AZERTY\" && layout != \"QWERTY\") return false;\n"
        "    if (!root.value(\"keymap\").isObject() || !root.value(\"mousemap\").isObject()) return false;\n"
        "    if (!root.value(\"sensitivity\").isDouble() || !root.value(\"aimSensitivity\").isDouble() || !root.value(\"overlayKey\").isDouble()) return false;\n"
        "    const double sensitivity = root.value(\"sensitivity\").toDouble();\n"
        "    const double aimSensitivity = root.value(\"aimSensitivity\").toDouble();\n"
        "    const int overlayKey = root.value(\"overlayKey\").toInt();\n"
        "    if (sensitivity < 0.01 || sensitivity > 100.0 || aimSensitivity < 0.01 || aimSensitivity > 100.0 || overlayKey <= 0) return false;\n"
        "    QMap<int, int> keysToImport; const QJsonObject keys = root.value(\"keymap\").toObject();\n"
        "    for (auto it = keys.begin(); it != keys.end(); ++it) { bool ok = false; int key = it.key().toInt(&ok); if (!ok || key <= 0 || !it.value().isDouble()) return false; int value = it.value().toInt(-1); if (value < 0 || value > 0x7fffffff) return false; keysToImport.insert(key, value); }\n"
        "    QMap<int, int> mouseToImport; const QJsonObject mouse = root.value(\"mousemap\").toObject();\n"
        "    for (auto it = mouse.begin(); it != mouse.end(); ++it) { bool ok = false; int key = it.key().toInt(&ok); if (!ok || key <= 0 || !it.value().isDouble()) return false; int value = it.value().toInt(-1); if (value < 0 || value > 0x7fffffff) return false; mouseToImport.insert(key, value); }\n"
        "    settings->SetViceKeyLayout(layout); settings->ClearViceKeyMappings(); settings->ClearViceKeyMouseMappings();\n"
        "    for (auto it = keysToImport.cbegin(); it != keysToImport.cend(); ++it) settings->SetViceKeyMapping(it.key(), it.value());\n"
        "    for (auto it = mouseToImport.cbegin(); it != mouseToImport.cend(); ++it) settings->SetViceKeyMouseMapping(it.key(), it.value());\n"
        "    settings->SetViceKeySensitivity(sensitivity); settings->SetViceKeyAimSensitivity(aimSensitivity); settings->SetViceKeyOverlayKey(overlayKey);\n"
        "    emit viceKeyLayoutChanged(); emit viceKeySensitivityChanged(); emit viceKeyAimSensitivityChanged(); emit viceKeyOverlayKeyChanged(); return true;\n"
        "}\n",
        "QML settings implementation")

    # Session state: mouse delta is emitted as a temporary right-stick value.
    insert_after(stream_h,
        "class QKeyEvent;\n",
        "class QWheelEvent;\n",
        "wheel event forward declaration")

    insert_after(stream_h,
        "\t\tbool mouse_touch_enabled;\n\t\tbool dpad_regular;\n",
        "\t\tdouble vice_key_sensitivity = 1.0;\n"
        "\t\tdouble vice_key_aim_sensitivity = 0.7;\n"
        "\t\tbool vice_key_mouse_aiming = false;\n"
        "\t\tbool vice_key_mouse_initialized = false;\n"
        "\t\tbool vice_key_tab_down = false;\n"
        "\t\tbool vice_key_wheel_l2_down = false;\n"
        "\t\tbool vice_key_wheel_r2_down = false;\n"
        "\t\tuint32_t vice_key_wheel_button_mask = 0;\n"
        "\t\tbool vice_key_mouse_capture_enabled = true;\n"
        "\t\tQMap<int, int> vice_key_pressed_keys;\n"
        "\t\tQMap<int, int> vice_key_pressed_mouse_buttons;\n"
        "\t\tQElapsedTimer vice_key_mouse_sample_clock;\n"
        "\t\tQTimer *vice_key_wheel_reset_timer = nullptr;\n"
        "\t\tqint64 vice_key_mouse_delta_x = 0;\n"
        "\t\tqint64 vice_key_mouse_delta_y = 0;\n"
        "\t\tdouble vice_key_mouse_smooth_x = 0.0;\n"
        "\t\tdouble vice_key_mouse_smooth_y = 0.0;\n"
        "\t\tQTimer *vice_key_mouse_reset_timer = nullptr;\n",
        "stream session members")

    # Windows Raw Input: read hardware-relative deltas without cursor warping.
    insert_after(stream_cpp,
        "#include <QKeyEvent>\n",
        """#include <algorithm>
#include <cmath>
#include <QWheelEvent>
#include <QAbstractNativeEventFilter>
#include <QCoreApplication>
#include <QDebug>
#include <QPointer>
#include <vector>
#ifdef Q_OS_WIN
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

class ViceKeyRawInputFilter final : public QAbstractNativeEventFilter
{
    QPointer<StreamSession> m_session;
    HWND m_target = nullptr;
    bool m_registered = false;
    bool m_enabled = true;

    void updateClip()
    {
        if (!m_target || !IsWindow(m_target) || IsIconic(m_target)) {
            ClipCursor(nullptr);
            return;
        }
        RECT client{};
        if (!GetClientRect(m_target, &client)) return;
        POINT topLeft{client.left, client.top};
        POINT bottomRight{client.right, client.bottom};
        if (!ClientToScreen(m_target, &topLeft) || !ClientToScreen(m_target, &bottomRight)) return;
        RECT screenRect{topLeft.x, topLeft.y, bottomRight.x, bottomRight.y};
        ClipCursor(&screenRect);
    }

public:
    bool attach(StreamSession *session)
    {
        detach();
        m_session = session;
        m_target = GetForegroundWindow();
        if (!m_target) {
            m_session.clear();
            return false;
        }
        RAWINPUTDEVICE device{};
        device.usUsagePage = 0x01;
        device.usUsage = 0x02;
        device.dwFlags = RIDEV_INPUTSINK;
        device.hwndTarget = m_target;
        if (!RegisterRawInputDevices(&device, 1, sizeof(device))) {
            m_target = nullptr;
            m_session.clear();
            return false;
        }
        m_registered = true;
        m_enabled = true;
        updateClip();
        return true;
    }

    void setEnabled(bool enabled)
    {
        if (m_enabled == enabled) return;
        m_enabled = enabled;
        if (m_enabled) updateClip();
        else ClipCursor(nullptr);
    }

    void detach()
    {
        ClipCursor(nullptr);
        if (m_registered) {
            RAWINPUTDEVICE device{};
            device.usUsagePage = 0x01;
            device.usUsage = 0x02;
            device.dwFlags = RIDEV_REMOVE;
            device.hwndTarget = nullptr;
            RegisterRawInputDevices(&device, 1, sizeof(device));
        }
        m_registered = false;
        m_enabled = false;
        m_target = nullptr;
        m_session.clear();
    }

    bool nativeEventFilter(const QByteArray &, void *message, qintptr *result) override
    {
        auto *msg = static_cast<MSG *>(message);
        if (!msg) return false;

        if (msg->hwnd == m_target && msg->message == WM_ACTIVATEAPP) {
            if (msg->wParam && m_enabled) updateClip();
            else if (!msg->wParam) {
                ClipCursor(nullptr);
                if (m_session) m_session->ResetRawMouseInput();
            }
            return false;
        }
        if (msg->hwnd == m_target && (msg->message == WM_SIZE || msg->message == WM_MOVE)) {
            if (m_enabled) updateClip();
            return false;
        }
        if (msg->message != WM_INPUT || msg->hwnd != m_target) return false;

        if (m_enabled && m_session && GetForegroundWindow() == m_target) {
            const HRAWINPUT input = reinterpret_cast<HRAWINPUT>(msg->lParam);
            UINT size = 0;
            if (GetRawInputData(input, RID_INPUT, nullptr, &size, sizeof(RAWINPUTHEADER)) == 0 &&
                size >= sizeof(RAWINPUTHEADER)) {
                std::vector<BYTE> bytes(size);
                if (GetRawInputData(input, RID_INPUT, bytes.data(), &size, sizeof(RAWINPUTHEADER)) == size) {
                    const auto *raw = reinterpret_cast<const RAWINPUT *>(bytes.data());
                    if (raw->header.dwType == RIM_TYPEMOUSE &&
                        !(raw->data.mouse.usFlags & MOUSE_MOVE_ABSOLUTE)) {
                        const LONG dx = raw->data.mouse.lLastX;
                        const LONG dy = raw->data.mouse.lLastY;
                        if (dx || dy) m_session->HandleRawMouseDelta(static_cast<int>(dx), static_cast<int>(dy));
                    }
                }
            }
        }

        if (msg->wParam == RIM_INPUT)
            DefWindowProcW(msg->hwnd, msg->message, msg->wParam, msg->lParam);
        if (result) *result = 0;
        return true;
    }
};
static ViceKeyRawInputFilter *g_viceKeyRawInputFilter = nullptr;
#endif
""",
        "Windows Raw Input support")

    # Add default GTA VI keyboard bindings after reading Chiaki's saved mapping.
    mapping = "\tkey_map = settings->GetControllerMappingForDecoding();\n"
    mapped = mapping + (
        "\tconst bool vickey_qwerty = settings->GetViceKeyLayout().compare(\"QWERTY\", Qt::CaseInsensitive) == 0;\n"
        "\tkey_map.insert(vickey_qwerty ? Qt::Key_W : Qt::Key_Z, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP));\n"
        "\tkey_map.insert(Qt::Key_S, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN));\n"
        "\tkey_map.insert(vickey_qwerty ? Qt::Key_A : Qt::Key_Q, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN));\n"
        "\tkey_map.insert(Qt::Key_D, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP));\n"
        "\tkey_map.insert(Qt::Key_Space, CHIAKI_CONTROLLER_BUTTON_CROSS);\n"
        "\tkey_map.insert(Qt::Key_F, CHIAKI_CONTROLLER_BUTTON_MOON);\n"
        "\tkey_map.insert(Qt::Key_R, CHIAKI_CONTROLLER_BUTTON_BOX);\n"
        "\tkey_map.insert(Qt::Key_E, CHIAKI_CONTROLLER_BUTTON_PYRAMID);\n"
        "\tkey_map.insert(Qt::Key_Tab, CHIAKI_CONTROLLER_BUTTON_R1);\n"
        "\tkey_map.insert(Qt::Key_Shift, CHIAKI_CONTROLLER_BUTTON_L3);\n"
        "\tkey_map.insert(Qt::Key_C, CHIAKI_CONTROLLER_BUTTON_R3);\n"
        "\tkey_map.insert(Qt::Key_T, CHIAKI_CONTROLLER_BUTTON_DPAD_UP);\n"
        "\tkey_map.insert(Qt::Key_V, CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN);\n"
        "\tkey_map.insert(Qt::Key_Left, CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT);\n"
        "\tkey_map.insert(Qt::Key_Right, CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT);\n"
        "\tkey_map.insert(Qt::Key_Comma, CHIAKI_CONTROLLER_BUTTON_TOUCHPAD);\n"
        "\tkey_map.insert(Qt::Key_Escape, CHIAKI_CONTROLLER_BUTTON_OPTIONS);\n"
        "\tkey_map.insert(Qt::Key_CapsLock, CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3);\n"
    )
    replace_once(stream_cpp, mapping, mapped, "GTA VI key map")

    # ViceKey is a keyboard-first controller layer; do not require users to enable
    # Chiaki-ng's optional legacy keyboard controller toggle manually.
    replace_once(stream_cpp,
        "\tthis->keyboard_controller_enabled = keyboard_controller_enabled_setting;\n",
        "\tthis->keyboard_controller_enabled = true; // ViceKey keyboard input\n",
        "enable ViceKey keyboard controller")

    # Capture settings and create a short reset timer so mouse movement acts as a stick,
    # not as a permanent deflection.
    insert_after(stream_cpp,
        "\tkey_map = connect_info.key_map;\n",
        "\tif (connect_info.settings) {\n"
        "\t\tvice_key_sensitivity = connect_info.settings->GetViceKeySensitivity();\n"
        "\t\tvice_key_aim_sensitivity = connect_info.settings->GetViceKeyAimSensitivity();\n"
        "\t}\n"
        "\tvice_key_mouse_sample_clock.start();\n"
        "\tvice_key_wheel_reset_timer = new QTimer(this);\n"
        "\tvice_key_wheel_reset_timer->setSingleShot(true);\n"
        "\tconnect(vice_key_wheel_reset_timer, &QTimer::timeout, this, [this] {\n"
        "\t\tvice_key_wheel_l2_down = false; vice_key_wheel_r2_down = false; vice_key_wheel_button_mask = 0;\n"
        "\t\tRefreshViceKeyInputState(); SendFeedbackState();\n"
        "\t});\n"
        "\tvice_key_mouse_reset_timer = new QTimer(this);\n"
        "#ifdef Q_OS_WIN\n"
        "\tvice_key_mouse_reset_timer->setTimerType(Qt::PreciseTimer);\n"
        "\tvice_key_mouse_reset_timer->setInterval(4);\n"
        "\tconnect(vice_key_mouse_reset_timer, &QTimer::timeout, this, [this] {\n"
        "\t\tconst qint64 dx = vice_key_mouse_delta_x;\n"
        "\t\tconst qint64 dy = vice_key_mouse_delta_y;\n"
        "\t\tvice_key_mouse_delta_x = 0;\n"
        "\t\tvice_key_mouse_delta_y = 0;\n"
        "\t\tconst qint64 sampleMs = qMax<qint64>(1, vice_key_mouse_sample_clock.restart());\n"
        "\t\tconst double aim = vice_key_mouse_aiming ? vice_key_aim_sensitivity : 1.0;\n"
        "\t\tconst double intervalScale = std::clamp(4.0 / static_cast<double>(sampleMs), 0.5, 2.0);\n"
        "\t\tconst double gain = vice_key_sensitivity * aim * 2200.0 * intervalScale;\n"
        "\t\tauto shapeDelta = [gain](qint64 delta) -> int16_t {\n"
        "\t\t\tif (delta == 0) return 0;\n"
        "\t\t\tconst double normalized = std::clamp(std::abs(static_cast<double>(delta)) * gain / 32767.0, 0.0, 1.0);\n"
        "\t\t\tconst double curved = (0.10 * normalized + 0.90 * std::pow(normalized, 1.70));\n"
        "\t\t\tconst double signedValue = std::copysign(curved * 32767.0, static_cast<double>(delta));\n"
        "\t\t\treturn static_cast<int16_t>(qBound(-32767, qRound(signedValue), 32767));\n"
        "\t\t};\n"
        "\t\tconst double smoothing = 1.0 - std::exp(-4.0 / 22.0);\n"
        "\t\tvice_key_mouse_smooth_x += (shapeDelta(dx) - vice_key_mouse_smooth_x) * smoothing;\n"
        "\t\tvice_key_mouse_smooth_y += (shapeDelta(dy) - vice_key_mouse_smooth_y) * smoothing;\n"
        "\t\tconst int16_t nextX = static_cast<int16_t>(qBound(-32767, qRound(vice_key_mouse_smooth_x), 32767));\n"
        "\t\tconst int16_t nextY = static_cast<int16_t>(qBound(-32767, qRound(vice_key_mouse_smooth_y), 32767));\n"
        "\t\tif (keyboard_state.right_x != nextX || keyboard_state.right_y != nextY) {\n"
        "\t\t\tkeyboard_state.right_x = nextX;\n"
        "\t\t\tkeyboard_state.right_y = nextY;\n"
        "\t\t\tSendFeedbackState();\n"
        "\t\t}\n"
        "\t});\n"
        "#else\n"
        "\tvice_key_mouse_reset_timer->setSingleShot(true);\n"
        "\tconnect(vice_key_mouse_reset_timer, &QTimer::timeout, this, [this] {\n"
        "\t\tif (keyboard_state.right_x || keyboard_state.right_y) {\n"
        "\t\t\tkeyboard_state.right_x = 0;\n"
        "\t\t\tkeyboard_state.right_y = 0;\n"
        "\t\t\tSendFeedbackState();\n"
        "\t\t}\n"
        "\t});\n"
        "#endif\n"
        "#ifdef Q_OS_WIN\n"
        "\tif (!g_viceKeyRawInputFilter) {\n"
        "\t\tg_viceKeyRawInputFilter = new ViceKeyRawInputFilter();\n"
        "\t\tif (QCoreApplication::instance()) QCoreApplication::instance()->installNativeEventFilter(g_viceKeyRawInputFilter);\n"
        "\t}\n"
        "\tif (!g_viceKeyRawInputFilter->attach(this)) qWarning() << \"ViceKey: Windows Raw Input registration failed\";\n"
        "\tQObject::connect(this, &QObject::destroyed, [] { if (g_viceKeyRawInputFilter) g_viceKeyRawInputFilter->detach(); });\n"
        "#endif\n"
        "\tvice_key_mouse_reset_timer->start();\n",
        "mouse look timer")

    old_mouse = (
        "void StreamSession::HandleMousePressEvent(QMouseEvent *event)\n{\n"
        "\tif(!mouse_touch_enabled)\n\t\treturn;\n"
        "\t// left button for touchpad gestures, others => touchpad click\n"
        "\tif (event->button() != Qt::MouseButton::LeftButton)\n\t\tkeyboard_state.buttons |= CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\tSendFeedbackState();\n}\n\n"
        "void StreamSession::HandleMouseReleaseEvent(QMouseEvent *event)\n{\n"
        "\tif(!mouse_touch_enabled)\n\t\treturn;\n"
        "\t// left button => end of touchpad gesture\n"
        "\tif (event->button() == Qt::LeftButton)\n\t{\n"
        "\t\tif(mouse_touch_id >= 0)\n\t\t{\n"
        "\t\t\tchiaki_controller_state_stop_touch(&keyboard_state, (uint8_t)mouse_touch_id);\n"
        "\t\t\tmouse_touch_id = -1;\n"
        "\t\t}\n"
        "\t}\n"
        "\tkeyboard_state.buttons &= ~CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\tSendFeedbackState();\n}\n\n"
        "void StreamSession::HandleMouseMoveEvent(QMouseEvent *event, qreal width, qreal height)\n{\n"
        "\tif(!mouse_touch_enabled)\n\t\treturn;\n"
        "\t// left button with move => touchpad gesture, otherwise ignore\n"
        "\tif (event->buttons() == Qt::LeftButton)\n\t{\n"
        "\t\tfloat x = std::clamp(0.0, event->scenePosition().x(), width);\n"
        "\t\tfloat y = std::clamp(0.0, event->scenePosition().y(), height);\n"
        "\t\tfloat psx = x * (PS_TOUCHPAD_MAX_X / width);\n"
        "\t\tfloat psy = y * (PS_TOUCHPAD_MAX_Y / height);\n"
        "\t\t// if touch id is set, move, otherwise start\n"
        "\t\tif(mouse_touch_id >= 0)\n\t\t\tchiaki_controller_state_set_touch_pos(&keyboard_state, (uint8_t)mouse_touch_id, (uint16_t)psx, (uint16_t)psy);\n"
        "\t\telse\n\t\t\tmouse_touch_id=chiaki_controller_state_start_touch(&keyboard_state, (uint16_t)psx, (uint16_t)psy);\t\n"
        "\t}\n"
        "\tSendFeedbackState();\n}\n"
    )
    new_mouse = (
        "void StreamSession::HandleMousePressEvent(QMouseEvent *event)\n{\n"
        "\tif (!event) return;\n"
        "\tconst int input = static_cast<int>(event->button());\n"
        "\tconst int action = vice_key_mouse_map.value(input, 0);\n"
        "\tif (!action) return;\n"
        "\tvice_key_pressed_mouse_buttons.insert(input, action);\n"
        "\tRefreshViceKeyInputState(); SendFeedbackState();\n"
        "}\n\n"
        "void StreamSession::HandleMouseReleaseEvent(QMouseEvent *event)\n{\n"
        "\tif (!event) return;\n"
        "\tvice_key_pressed_mouse_buttons.remove(static_cast<int>(event->button()));\n"
        "\tRefreshViceKeyInputState(); SendFeedbackState();\n"
        "}\n\n"
        "void StreamSession::HandleMouseMoveEvent(QMouseEvent *event, qreal width, qreal height)\n{\n"
        "#ifdef Q_OS_WIN\n"
        "\tQ_UNUSED(event); Q_UNUSED(width); Q_UNUSED(height);\n"
        "#else\n"
        "\tif (width <= 0 || height <= 0) return;\n"
        "\tconst QPointF center(width * 0.5, height * 0.5);\n"
        "\tconst QPointF delta = event->position() - center;\n"
        "\tif (qAbs(delta.x()) < 0.01 && qAbs(delta.y()) < 0.01) return;\n"
        "\tconst double aim = vice_key_mouse_aiming ? vice_key_aim_sensitivity : 1.0;\n"
        "\tconst double gain = vice_key_sensitivity * aim * 2200.0;\n"
        "\tkeyboard_state.right_x = static_cast<int16_t>(qBound(-32767, qRound(delta.x() * gain), 32767));\n"
        "\tkeyboard_state.right_y = static_cast<int16_t>(qBound(-32767, qRound(delta.y() * gain), 32767));\n"
        "\tif (vice_key_mouse_reset_timer) vice_key_mouse_reset_timer->start(12);\n"
        "\tSendFeedbackState();\n"
        "#endif\n"
        "}\n"
        "\nvoid StreamSession::HandleRawMouseDelta(int dx, int dy)\n{\n"
        "\tvice_key_mouse_delta_x = std::clamp<qint64>(vice_key_mouse_delta_x + dx, -1000000, 1000000);\n"
        "\tvice_key_mouse_delta_y = std::clamp<qint64>(vice_key_mouse_delta_y + dy, -1000000, 1000000);\n"
        "}\n"
        "\nvoid StreamSession::ResetRawMouseInput()\n{\n"
        "\tvice_key_mouse_delta_x = 0;\n"
        "\tvice_key_mouse_delta_y = 0;\n"
        "\tvice_key_mouse_aiming = false;\n"
        "\tif (keyboard_state.right_x || keyboard_state.right_y) {\n"
        "\t\tkeyboard_state.right_x = 0;\n"
        "\t\tkeyboard_state.right_y = 0;\n"
        "\t\tSendFeedbackState();\n"
        "\t}\n"
        "}\n"
    )
    replace_section(stream_cpp,
        "void StreamSession::HandleMousePressEvent(QMouseEvent *event)\n",
        "void StreamSession::HandleKeyboardEvent(QKeyEvent *event)\n",
        new_mouse + "\n", "mouse-to-right-stick input")

    old_keyboard = (
        "void StreamSession::HandleKeyboardEvent(QKeyEvent *event)\n{\n"
        "\tif(!keyboard_controller_enabled)\n"
        "\t\treturn;\n"
        "\tif(key_map.contains(Qt::Key(event->key())) == false)\n"
        "\t\treturn;\n"
        "\n"
        "\tif(event->isAutoRepeat())\n"
        "\t\treturn;\n"
        "\n"
        "\tint button = key_map[Qt::Key(event->key())];\n"
        "\tbool press_event = event->type() == QEvent::Type::KeyPress;\n"
        "\n"
        "\tswitch(button)\n\t{\n"
        "\t\tcase CHIAKI_CONTROLLER_ANALOG_BUTTON_L2:\n"
        "\t\t\tkeyboard_state.l2_state = press_event ? 0xff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase CHIAKI_CONTROLLER_ANALOG_BUTTON_R2:\n"
        "\t\t\tkeyboard_state.r2_state = press_event ? 0xff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_RIGHT_Y_UP):\n"
        "\t\t\tkeyboard_state.right_y = press_event ? -0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_RIGHT_Y_DOWN):\n"
        "\t\t\tkeyboard_state.right_y = press_event ? 0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_RIGHT_X_UP):\n"
        "\t\t\tkeyboard_state.right_x = press_event ? 0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_RIGHT_X_DOWN):\n"
        "\t\t\tkeyboard_state.right_x = press_event ? -0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP):\n"
        "\t\t\tkeyboard_state.left_y = press_event ? -0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN):\n"
        "\t\t\tkeyboard_state.left_y = press_event ? 0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP):\n"
        "\t\t\tkeyboard_state.left_x = press_event ? 0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tcase static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN):\n"
        "\t\t\tkeyboard_state.left_x = press_event ? -0x7fff : 0;\n"
        "\t\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tif(press_event)\n"
        "\t\t\t\tkeyboard_state.buttons |= button;\n"
        "\t\t\telse\n"
        "\t\t\t\tkeyboard_state.buttons &= ~button;\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "\n"
        "\tSendFeedbackState();\n"
        "}\n"
    )
    new_keyboard = (
        "void StreamSession::HandleKeyboardEvent(QKeyEvent *event)\n{\n"
        "\tif (!keyboard_controller_enabled || !event || event->isAutoRepeat()) return;\n"
        "\tconst int key = event->key();\n"
        "\tconst bool pressed = event->type() == QEvent::Type::KeyPress;\n"
        "\tif (pressed) {\n"
        "\t\tauto it = key_map.find(static_cast<Qt::Key>(key));\n"
        "\t\tif (it == key_map.end()) return;\n"
        "\t\tvice_key_pressed_keys.insert(key, it.value());\n"
        "\t} else {\n"
        "\t\tif (!vice_key_pressed_keys.contains(key)) return;\n"
        "\t\tvice_key_pressed_keys.remove(key);\n"
        "\t}\n"
        "\tif (key == Qt::Key_Tab) vice_key_tab_down = pressed;\n"
        "\tRefreshViceKeyInputState();\n"
        "\tSendFeedbackState();\n"
        "}\n"
    )
    replace_section(stream_cpp,
        "void StreamSession::HandleKeyboardEvent(QKeyEvent *event)\n",
        "void StreamSession::HandleTouchEvent(QTouchEvent *event, qreal width, qreal height)\n",
        new_keyboard + "\n", "alias-safe keyboard input")

    # Keep Chiaki-ng global shortcuts intact; AZERTY Q is only interpreted during the stream.
    insert_after(mainwindow_cpp,
        "#include <QGuiApplication>\n",
        "#include <QCursor>\n#include <QWheelEvent>\n",
        "cursor and wheel event includes")

    old_event = (
        "            if (event->type() == QEvent::MouseMove)\n"
        "                session->HandleMouseMoveEvent(static_cast<QMouseEvent*>(event), width(), height());\n"
        "            else if (event->type() == QEvent::MouseButtonPress)\n"
        "                session->HandleMousePressEvent(static_cast<QMouseEvent*>(event));\n"
        "            else if (event->type() == QEvent::MouseButtonRelease)\n"
        "                session->HandleMouseReleaseEvent(static_cast<QMouseEvent*>(event));\n"
        "            return true;\n"
    )
    new_event = (
        "            if (event->type() == QEvent::MouseMove) {\n"
        "                session->HandleMouseMoveEvent(static_cast<QMouseEvent*>(event), width(), height());\n"
        "                if (width() > 0 && height() > 0) {\n"
        "                    setCursor(Qt::BlankCursor);\n"
        "                }\n"
        "            } else if (event->type() == QEvent::MouseButtonPress)\n"
        "                session->HandleMousePressEvent(static_cast<QMouseEvent*>(event));\n"
        "            else if (event->type() == QEvent::MouseButtonRelease)\n"
        "                session->HandleMouseReleaseEvent(static_cast<QMouseEvent*>(event));\n"
        "            return true;\n"
    )
    replace_once(mainwindow_cpp, old_event, new_event, "captured mouse recenter")

    # Add live controls to the existing in-app Keys page.
    qml_anchor = (
        "                        columnSpacing: 10\n\n"
        "                        Button {\n"
        "                            id: resetAllKeys\n"
    )
    qml_addition = (
        "                        GroupBox {\n"
        "                            Layout.columnSpan: 3\n"
        "                            Layout.fillWidth: true\n"
        "                            title: \"ViceKey · GTA VI\"\n"
        "                            ColumnLayout {\n"
        "                                anchors.fill: parent\n"
        "                                RowLayout {\n"
        "                                    Label { text: qsTr(view.vt(\"Disposition du clavier\", \"Keyboard layout\")) }\n"
        "                                    ComboBox {\n"
        "                                        model: [\"AZERTY\", \"QWERTY\"]\n"
        "                                        currentIndex: Chiaki.settings.viceKeyLayout === \"QWERTY\" ? 1 : 0\n"
        "                                        onActivated: index => { Chiaki.settings.viceKeyLayout = model[index]; if (Chiaki.session) Chiaki.session.setViceKeyLayout(model[index]); }\n"
        "                                    }\n"
        "                                }\n"
        "                                Label { text: qsTr(\"Camera sensitivity: \" + Number(Chiaki.settings.viceKeySensitivity).toFixed(2)) }\n"
        "                                Slider {\n"
        "                                    Layout.fillWidth: true\n"
        "                                    from: 0.01; to: 100.00; stepSize: 0.05\n"
        "                                    value: Chiaki.settings.viceKeySensitivity\n"
        "                                    onMoved: { Chiaki.settings.viceKeySensitivity = value; if (Chiaki.session) Chiaki.session.setViceKeySensitivity(value); }\n"
        "                                }\n"
        "                                Label { text: qsTr(\"Aim sensitivity: \" + Number(Chiaki.settings.viceKeyAimSensitivity).toFixed(2)) }\n"
        "                                Slider {\n"
        "                                    Layout.fillWidth: true\n"
        "                                    from: 0.01; to: 100.00; stepSize: 0.05\n"
        "                                    value: Chiaki.settings.viceKeyAimSensitivity\n"
        "                                    onMoved: { Chiaki.settings.viceKeyAimSensitivity = value; if (Chiaki.session) Chiaki.session.setViceKeyAimSensitivity(value); }\n"
        "                                }\n"
        "                                Label {\n"
        "                                    Layout.fillWidth: true\n"
        "                                    wrapMode: Text.WordWrap\n"
        "                                    text: qsTr(\"Mouse look is active while a Remote Play session has focus. Right-click aims; left-click fires. Sensitivity changes apply immediately. Press F1 in a stream to open the ViceKey overlay.\")\n"
        "                                }\n"
        "                            }\n"
        "                        }\n\n"
    )
    replace_once(settings_qml, qml_anchor, qml_anchor.replace("                        Button {\n                            id: resetAllKeys\n", qml_addition + "                        Button {\n                            id: resetAllKeys\n"), "ViceKey settings panel")

    # Persist user-selected mappings and expose live session controls.
    insert_after(settings_h,
        "\t\tvoid SetViceKeyAimSensitivity(double value);\n",
        "\t\tQMap<int, int> GetViceKeyMappings() const;\n"
        "\t\tvoid SetViceKeyMapping(int key, int button);\n"
        "\t\tQMap<int, int> GetViceKeyMouseMappings() const;\n"
        "\t\tvoid SetViceKeyMouseMapping(int key, int button);\n"
        "\t\tint GetViceKeyOverlayKey() const;\n"
        "\t\tvoid SetViceKeyOverlayKey(int key);\n"
        "\t\tvoid ClearViceKeyMappings();\n"
        "\t\tvoid ClearViceKeyMouseMappings();\n",
        "persistent key map API")
    insert_after(settings_cpp,
        "void Settings::SetViceKeyAimSensitivity(double value)\n{\n\tsettings.setValue(\"vickey/aim_sensitivity\", qBound(0.01, value, 100.0));\n}\n",
        "\nQMap<int, int> Settings::GetViceKeyMappings() const\n{\n"
        "\tQMap<int, int> result;\n"
        "\tconst QString prefix = QStringLiteral(\"vickey/profiles/%1/keymap/\").arg(GetViceKeyLayout().toLower());\n"
        "\tfor (const QString &name : settings.allKeys()) {\n"
        "\t\tif (!name.startsWith(prefix)) continue;\n"
        "\t\tbool ok = false;\n"
        "\t\tconst int key = name.mid(prefix.size()).toInt(&ok);\n"
        "\t\tif (ok) result.insert(key, settings.value(name).toInt());\n"
        "\t}\n"
        "\treturn result;\n}\n"
        "void Settings::SetViceKeyMapping(int key, int button)\n{\n"
        "\tsettings.setValue(QStringLiteral(\"vickey/profiles/%1/keymap/%2\").arg(GetViceKeyLayout().toLower()).arg(key), button);\n}\n"
        "QMap<int, int> Settings::GetViceKeyMouseMappings() const\n{\n"
        "\tQMap<int, int> result;\n"
        "\tconst QString prefix = QStringLiteral(\"vickey/profiles/%1/mousemap/\").arg(GetViceKeyLayout().toLower());\n"
        "\tfor (const QString &name : settings.allKeys()) {\n"
        "\t\tif (!name.startsWith(prefix)) continue;\n"
        "\t\tbool ok = false; const int key = name.mid(prefix.size()).toInt(&ok);\n"
        "\t\tif (ok) result.insert(key, settings.value(name).toInt());\n"
        "\t}\n"
        "\treturn result;\n}\n"
        "void Settings::SetViceKeyMouseMapping(int key, int button)\n{\n"
        "\tsettings.setValue(QStringLiteral(\"vickey/profiles/%1/mousemap/%2\").arg(GetViceKeyLayout().toLower()).arg(key), button);\n}\n"
        "int Settings::GetViceKeyOverlayKey() const\n{\n"
        "\treturn settings.value(\"vickey/overlay_key\", static_cast<int>(Qt::Key_F1)).toInt();\n"
        "}\n"
        "void Settings::SetViceKeyOverlayKey(int key)\n{\n"
        "\tsettings.setValue(\"vickey/overlay_key\", key);\n"
        "}\n"
        "void Settings::ClearViceKeyMappings()\n{\n"
        "\tsettings.remove(QStringLiteral(\"vickey/profiles/%1/keymap\").arg(GetViceKeyLayout().toLower()));\n"
        "}\n"
        "void Settings::ClearViceKeyMouseMappings()\n{\n"
        "\tsettings.remove(QStringLiteral(\"vickey/profiles/%1/mousemap\").arg(GetViceKeyLayout().toLower()));\n"
        "}\n",
        "persistent key map implementation")

    insert_after(stream_h,
        "\t\tQMap<Qt::Key, int> key_map;\n\t\tQElapsedTimer connect_timer;\n",
        "\t\tSettings *vice_key_settings = nullptr;\n"
        "\t\tQMap<int, int> vice_key_mouse_map;\n",
        "session settings pointer")
    insert_after(stream_h,
        "\t\tvoid GoHome();\n",
        "\t\tvoid HandleRawMouseDelta(int dx, int dy);\n"
        "\t\tvoid ResetRawMouseInput();\n"
        "\t\tvoid RefreshViceKeyInputState();\n"
        "\t\tbool HandleMouseWheelEvent(QWheelEvent *event);\n"
        "\t\tQ_INVOKABLE void setViceKeyButton(int key, const QString &action);\n"
        "\t\tQ_INVOKABLE QString viceKeyActionForKey(int key) const;\n"
        "\t\tQ_INVOKABLE void setViceKeyMouseInput(int input, const QString &action);\n"
        "\t\tQ_INVOKABLE QString viceKeyActionForMouseInput(int input) const;\n"
        "\t\tQ_INVOKABLE void setViceKeyMouseCaptureEnabled(bool enabled);\n"
        "\t\tQ_INVOKABLE void setViceKeyMapping(int old_key, int new_key, const QString &action);\n"
        "\t\tQ_INVOKABLE void setViceKeyLayout(const QString &layout);\n"
        "\t\tQ_INVOKABLE void setViceKeySensitivity(double value);\n"
        "\t\tQ_INVOKABLE void setViceKeyAimSensitivity(double value);\n"
        "\t\tQ_INVOKABLE void setViceKeyMouseMapping(int old_button, int new_button, const QString &action);\n"
        "\t\tQ_INVOKABLE int viceKeyMappedKey(const QString &action, int occurrence, int fallback) const;\n"
        "\t\tQ_INVOKABLE int viceKeyCurrentMouseButton(const QString &action, int fallback) const;\n"
        "\t\tvoid ReleaseKeyboardInput();\n",
        "live session invokables")

    # Apply persistent user overrides after built-in AZERTY/QWERTY defaults.
    insert_after(stream_cpp,
        "\tkey_map.insert(Qt::Key_CapsLock, CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3);\n",
        "\tconst auto vice_key_overrides = settings->GetViceKeyMappings();\n"
        "\tfor (auto it = vice_key_overrides.cbegin(); it != vice_key_overrides.cend(); ++it) {\n"
        "\t\tconst Qt::Key key = static_cast<Qt::Key>(it.key());\n"
        "\t\tif (it.value() <= 0) key_map.remove(key);\n"
        "\t\telse key_map.insert(key, it.value());\n"
        "\t}\n",
        "load persistent key overrides")
    insert_after(stream_cpp,
        "\tkey_map = connect_info.key_map;\n",
        "\tvice_key_settings = connect_info.settings;\n"
        "\tvice_key_mouse_map.insert(static_cast<int>(Qt::LeftButton), CHIAKI_CONTROLLER_ANALOG_BUTTON_R2);\n"
        "\tvice_key_mouse_map.insert(static_cast<int>(Qt::RightButton), CHIAKI_CONTROLLER_ANALOG_BUTTON_L2);\n"
        "\tvice_key_mouse_map.insert(1001, CHIAKI_CONTROLLER_ANALOG_BUTTON_L2); // wheel up while Tab is held\n"
        "\tvice_key_mouse_map.insert(1002, CHIAKI_CONTROLLER_ANALOG_BUTTON_R2); // wheel down while Tab is held\n"
        "\tif (vice_key_settings) {\n"
        "\t\tconst auto mouse_overrides = vice_key_settings->GetViceKeyMouseMappings();\n"
        "\t\tfor (auto it = mouse_overrides.cbegin(); it != mouse_overrides.cend(); ++it) {\n"
        "\t\t\tif (it.value() <= 0) vice_key_mouse_map.remove(it.key()); else vice_key_mouse_map.insert(it.key(), it.value());\n"
        "\t\t}\n"
        "\t}\n",
        "keep settings pointer and initialize mouse map")

    # Add live mapping and sensitivity setters to StreamSession. Button names are
    # stable profile IDs rather than Qt/Chiaki enum values exposed to QML.
    session_methods = (
        "void StreamSession::setViceKeyMapping(int old_key, int new_key, const QString &action)\n{\n"
        "\tint button = 0;\n"
        "\tif (action == \"left_y_up\") button = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP);\n"
        "\telse if (action == \"left_y_down\") button = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN);\n"
        "\telse if (action == \"left_x_up\") button = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP);\n"
        "\telse if (action == \"left_x_down\") button = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN);\n"
        "\telse if (action == \"cross\") button = CHIAKI_CONTROLLER_BUTTON_CROSS;\n"
        "\telse if (action == \"circle\") button = CHIAKI_CONTROLLER_BUTTON_MOON;\n"
        "\telse if (action == \"square\") button = CHIAKI_CONTROLLER_BUTTON_BOX;\n"
        "\telse if (action == \"triangle\") button = CHIAKI_CONTROLLER_BUTTON_PYRAMID;\n"
        "\telse if (action == \"r1\") button = CHIAKI_CONTROLLER_BUTTON_R1;\n"
        "\telse if (action == \"l1\") button = CHIAKI_CONTROLLER_BUTTON_L1;\n"
        "\telse if (action == \"r3\") button = CHIAKI_CONTROLLER_BUTTON_R3;\n"
        "\telse if (action == \"l3\") button = CHIAKI_CONTROLLER_BUTTON_L3;\n"
        "\telse if (action == \"touchpad\") button = CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\telse if (action == \"options\") button = CHIAKI_CONTROLLER_BUTTON_OPTIONS;\n"
        "\tif (!button) return;\n"
        "\tconst Qt::Key previous = static_cast<Qt::Key>(old_key);\n"
        "\tconst Qt::Key next = static_cast<Qt::Key>(new_key);\n"
        "\tif (old_key != new_key && key_map.value(previous, 0) == button) key_map.remove(previous);\n"
        "\tkey_map.insert(next, button);\n"
        "\tif (vice_key_settings) {\n"
        "\t\tif (old_key != new_key) vice_key_settings->SetViceKeyMapping(old_key, 0);\n"
        "\t\tvice_key_settings->SetViceKeyMapping(new_key, button);\n"
        "\t}\n"
        "}\n\n"
        """static int ViceKeyActionValue(const QString &action)
{
    if (action == "left_y_up") return static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP);
    if (action == "left_y_down") return static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN);
    if (action == "left_x_up") return static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP);
    if (action == "left_x_down") return static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN);
    if (action == "cross") return CHIAKI_CONTROLLER_BUTTON_CROSS;
    if (action == "circle") return CHIAKI_CONTROLLER_BUTTON_MOON;
    if (action == "square") return CHIAKI_CONTROLLER_BUTTON_BOX;
    if (action == "triangle") return CHIAKI_CONTROLLER_BUTTON_PYRAMID;
    if (action == "l1") return CHIAKI_CONTROLLER_BUTTON_L1;
    if (action == "r1") return CHIAKI_CONTROLLER_BUTTON_R1;
    if (action == "l2") return CHIAKI_CONTROLLER_ANALOG_BUTTON_L2;
    if (action == "r2") return CHIAKI_CONTROLLER_ANALOG_BUTTON_R2;
    if (action == "l3") return CHIAKI_CONTROLLER_BUTTON_L3;
    if (action == "r3") return CHIAKI_CONTROLLER_BUTTON_R3;
    if (action == "focus") return CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3;
    if (action == "dpad_up") return CHIAKI_CONTROLLER_BUTTON_DPAD_UP;
    if (action == "dpad_down") return CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN;
    if (action == "dpad_left") return CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT;
    if (action == "dpad_right") return CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT;
    if (action == "touchpad") return CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;
    if (action == "options") return CHIAKI_CONTROLLER_BUTTON_OPTIONS;
    return 0;
}

static QString ViceKeyActionName(int value)
{
    if (!value) return QStringLiteral("none");
    if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP)) return QStringLiteral("left_y_up");
    if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN)) return QStringLiteral("left_y_down");
    if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP)) return QStringLiteral("left_x_up");
    if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN)) return QStringLiteral("left_x_down");
    if (value == CHIAKI_CONTROLLER_BUTTON_CROSS) return QStringLiteral("cross");
    if (value == CHIAKI_CONTROLLER_BUTTON_MOON) return QStringLiteral("circle");
    if (value == CHIAKI_CONTROLLER_BUTTON_BOX) return QStringLiteral("square");
    if (value == CHIAKI_CONTROLLER_BUTTON_PYRAMID) return QStringLiteral("triangle");
    if (value == CHIAKI_CONTROLLER_BUTTON_L1) return QStringLiteral("l1");
    if (value == CHIAKI_CONTROLLER_BUTTON_R1) return QStringLiteral("r1");
    if (value == CHIAKI_CONTROLLER_ANALOG_BUTTON_L2) return QStringLiteral("l2");
    if (value == CHIAKI_CONTROLLER_ANALOG_BUTTON_R2) return QStringLiteral("r2");
    if (value == CHIAKI_CONTROLLER_BUTTON_L3) return QStringLiteral("l3");
    if (value == CHIAKI_CONTROLLER_BUTTON_R3) return QStringLiteral("r3");
    if (value == (CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3)) return QStringLiteral("focus");
    if (value == CHIAKI_CONTROLLER_BUTTON_DPAD_UP) return QStringLiteral("dpad_up");
    if (value == CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN) return QStringLiteral("dpad_down");
    if (value == CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT) return QStringLiteral("dpad_left");
    if (value == CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT) return QStringLiteral("dpad_right");
    if (value == CHIAKI_CONTROLLER_BUTTON_TOUCHPAD) return QStringLiteral("touchpad");
    if (value == CHIAKI_CONTROLLER_BUTTON_OPTIONS) return QStringLiteral("options");
    return QStringLiteral("none");
}

void StreamSession::setViceKeyButton(int key, const QString &action)
{
    const int value = ViceKeyActionValue(action);
    const Qt::Key qtKey = static_cast<Qt::Key>(key);
    if (value == 0) key_map.remove(qtKey); else key_map.insert(qtKey, value);
    if (vice_key_settings) vice_key_settings->SetViceKeyMapping(key, value);
}

QString StreamSession::viceKeyActionForKey(int key) const
{
    return ViceKeyActionName(key_map.value(static_cast<Qt::Key>(key), 0));
}

void StreamSession::setViceKeyMouseInput(int input, const QString &action)
{
    const int value = ViceKeyActionValue(action);
    if (value == 0) vice_key_mouse_map.remove(input); else vice_key_mouse_map.insert(input, value);
    if (vice_key_settings) vice_key_settings->SetViceKeyMouseMapping(input, value);
}

QString StreamSession::viceKeyActionForMouseInput(int input) const
{
    return ViceKeyActionName(vice_key_mouse_map.value(input, 0));
}

void StreamSession::setViceKeyMouseCaptureEnabled(bool enabled)
{
    vice_key_mouse_capture_enabled = enabled;
#ifdef Q_OS_WIN
    if (g_viceKeyRawInputFilter) g_viceKeyRawInputFilter->setEnabled(enabled);
#endif
    if (!enabled) ResetRawMouseInput();
    if (vice_key_mouse_reset_timer && !vice_key_mouse_reset_timer->isActive()) vice_key_mouse_reset_timer->start();
}

void StreamSession::RefreshViceKeyInputState()
{
    uint32_t buttons = vice_key_wheel_button_mask;
    bool l2 = vice_key_wheel_l2_down;
    bool r2 = vice_key_wheel_r2_down;
    bool leftUp = false, leftDown = false, leftLeft = false, leftRight = false;
    auto apply = [&](int value) {
        if (value == CHIAKI_CONTROLLER_ANALOG_BUTTON_L2) { l2 = true; return; }
        if (value == CHIAKI_CONTROLLER_ANALOG_BUTTON_R2) { r2 = true; return; }
        if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP)) { leftUp = true; return; }
        if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN)) { leftDown = true; return; }
        if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN)) { leftLeft = true; return; }
        if (value == static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP)) { leftRight = true; return; }
        buttons |= static_cast<uint32_t>(value);
    };
    for (auto it = vice_key_pressed_keys.cbegin(); it != vice_key_pressed_keys.cend(); ++it) apply(it.value());
    for (auto it = vice_key_pressed_mouse_buttons.cbegin(); it != vice_key_pressed_mouse_buttons.cend(); ++it) apply(it.value());
    keyboard_state.buttons = buttons;
    keyboard_state.l2_state = l2 ? 0xff : 0;
    keyboard_state.r2_state = r2 ? 0xff : 0;
    keyboard_state.left_y = leftUp == leftDown ? 0 : (leftUp ? -0x7fff : 0x7fff);
    keyboard_state.left_x = leftRight == leftLeft ? 0 : (leftRight ? 0x7fff : -0x7fff);
    vice_key_mouse_aiming = l2;
}

bool StreamSession::HandleMouseWheelEvent(QWheelEvent *event)
{
    if (!event || !vice_key_tab_down || event->angleDelta().y() == 0) return false;
    const int input = event->angleDelta().y() > 0 ? 1001 : 1002;
    const int action = vice_key_mouse_map.value(input, 0);
    if (action == CHIAKI_CONTROLLER_ANALOG_BUTTON_L2) vice_key_wheel_l2_down = true;
    else if (action == CHIAKI_CONTROLLER_ANALOG_BUTTON_R2) vice_key_wheel_r2_down = true;
    else vice_key_wheel_button_mask |= static_cast<uint32_t>(action);
    if (vice_key_wheel_reset_timer) vice_key_wheel_reset_timer->start(80);
    RefreshViceKeyInputState();
    SendFeedbackState();
    return true;
}

"""
        "void StreamSession::setViceKeyLayout(const QString &layout)\n{\n"
        "\tconst bool qwerty = layout.compare(\"QWERTY\", Qt::CaseInsensitive) == 0;\n"
        "\tif (vice_key_settings) {\n"
        "\t\tvice_key_settings->SetViceKeyLayout(qwerty ? \"QWERTY\" : \"AZERTY\");\n"
        "\t\tkey_map = vice_key_settings->GetControllerMappingForDecoding();\n"
        "\t}\n"
        "\tkey_map.insert(qwerty ? Qt::Key_W : Qt::Key_Z, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP));\n"
        "\tkey_map.insert(Qt::Key_S, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN));\n"
        "\tkey_map.insert(qwerty ? Qt::Key_A : Qt::Key_Q, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN));\n"
        "\tkey_map.insert(Qt::Key_D, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP));\n"
        "\tkey_map.insert(Qt::Key_Space, CHIAKI_CONTROLLER_BUTTON_CROSS);\n"
        "\tkey_map.insert(Qt::Key_F, CHIAKI_CONTROLLER_BUTTON_MOON);\n"
        "\tkey_map.insert(Qt::Key_R, CHIAKI_CONTROLLER_BUTTON_BOX);\n"
        "\tkey_map.insert(Qt::Key_E, CHIAKI_CONTROLLER_BUTTON_PYRAMID);\n"
        "\tkey_map.insert(Qt::Key_Tab, CHIAKI_CONTROLLER_BUTTON_R1);\n"
        "\tkey_map.insert(Qt::Key_Shift, CHIAKI_CONTROLLER_BUTTON_L3);\n"
        "\tkey_map.insert(Qt::Key_C, CHIAKI_CONTROLLER_BUTTON_R3);\n"
        "\tkey_map.insert(Qt::Key_T, CHIAKI_CONTROLLER_BUTTON_DPAD_UP);\n"
        "\tkey_map.insert(Qt::Key_V, CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN);\n"
        "\tkey_map.insert(Qt::Key_Left, CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT);\n"
        "\tkey_map.insert(Qt::Key_Right, CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT);\n"
        "\tkey_map.insert(Qt::Key_Comma, CHIAKI_CONTROLLER_BUTTON_TOUCHPAD);\n"
        "\tkey_map.insert(Qt::Key_Escape, CHIAKI_CONTROLLER_BUTTON_OPTIONS);\n"
        "\tkey_map.insert(Qt::Key_CapsLock, CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3);\n"
        "\tif (vice_key_settings) {\n"
        "\t\tconst auto overrides = vice_key_settings->GetViceKeyMappings();\n"
        "\t\tfor (auto it = overrides.cbegin(); it != overrides.cend(); ++it) {\n"
        "\t\t\tconst Qt::Key key = static_cast<Qt::Key>(it.key());\n"
        "\t\t\tif (it.value() <= 0) key_map.remove(key); else key_map.insert(key, it.value());\n"
        "\t\t}\n"
        "\t\tvice_key_mouse_map.clear();\n"
        "\t\tvice_key_mouse_map.insert(static_cast<int>(Qt::LeftButton), CHIAKI_CONTROLLER_ANALOG_BUTTON_R2);\n"
        "\t\tvice_key_mouse_map.insert(static_cast<int>(Qt::RightButton), CHIAKI_CONTROLLER_ANALOG_BUTTON_L2);\n"
        "\t\tvice_key_mouse_map.insert(1001, CHIAKI_CONTROLLER_ANALOG_BUTTON_L2);\n"
        "\t\tvice_key_mouse_map.insert(1002, CHIAKI_CONTROLLER_ANALOG_BUTTON_R2);\n"
        "\t\tconst auto mouseOverrides = vice_key_settings->GetViceKeyMouseMappings();\n"
        "\t\tfor (auto it = mouseOverrides.cbegin(); it != mouseOverrides.cend(); ++it) { if (it.value() <= 0) vice_key_mouse_map.remove(it.key()); else vice_key_mouse_map.insert(it.key(), it.value()); }\n"
        "\t}\n"
        "}\n\n"
        "void StreamSession::setViceKeySensitivity(double value)\n{\n"
        "\tvice_key_sensitivity = qBound(0.01, value, 100.0);\n"
        "\tif (vice_key_settings) vice_key_settings->SetViceKeySensitivity(vice_key_sensitivity);\n"
        "\tif (vice_key_mouse_reset_timer && !vice_key_mouse_reset_timer->isActive()) vice_key_mouse_reset_timer->start();\n"
        "}\n\n"
        "void StreamSession::setViceKeyAimSensitivity(double value)\n{\n"
        "\tvice_key_aim_sensitivity = qBound(0.01, value, 100.0);\n"
        "\tif (vice_key_settings) vice_key_settings->SetViceKeyAimSensitivity(vice_key_aim_sensitivity);\n"
        "\tif (vice_key_mouse_reset_timer && !vice_key_mouse_reset_timer->isActive()) vice_key_mouse_reset_timer->start();\n"
        "}\n\n"
        "void StreamSession::setViceKeyMouseMapping(int old_button, int new_button, const QString &action)\n{\n"
        "\tint value = 0;\n"
        "\tif (action == \"fire\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_R2;\n"
        "\telse if (action == \"aim\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_L2;\n"
        "\telse if (action == \"l3\") value = CHIAKI_CONTROLLER_BUTTON_L3;\n"
        "\telse if (action == \"r3\") value = CHIAKI_CONTROLLER_BUTTON_R3;\n"
        "\telse if (action == \"touchpad\") value = CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\tif (!value) return;\n"
        "\tif (old_button != new_button) vice_key_mouse_map.remove(old_button);\n"
        "\tvice_key_mouse_map.insert(new_button, value);\n"
        "\tif (vice_key_settings) { if (old_button != new_button) vice_key_settings->SetViceKeyMouseMapping(old_button, 0); vice_key_settings->SetViceKeyMouseMapping(new_button, value); }\n"
        "}\n\n"
        "int StreamSession::viceKeyMappedKey(const QString &action, int occurrence, int fallback) const\n{\n"
        "\tint value = 0;\n"
        "\tif (action == \"left_y_up\") value = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP);\n"
        "\telse if (action == \"left_y_down\") value = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN);\n"
        "\telse if (action == \"left_x_up\") value = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP);\n"
        "\telse if (action == \"left_x_down\") value = static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN);\n"
        "\telse if (action == \"cross\") value = CHIAKI_CONTROLLER_BUTTON_CROSS;\n"
        "\telse if (action == \"circle\") value = CHIAKI_CONTROLLER_BUTTON_MOON;\n"
        "\telse if (action == \"square\") value = CHIAKI_CONTROLLER_BUTTON_BOX;\n"
        "\telse if (action == \"triangle\") value = CHIAKI_CONTROLLER_BUTTON_PYRAMID;\n"
        "\telse if (action == \"r1\") value = CHIAKI_CONTROLLER_BUTTON_R1;\n"
        "\telse if (action == \"l1\") value = CHIAKI_CONTROLLER_BUTTON_L1;\n"
        "\telse if (action == \"r3\") value = CHIAKI_CONTROLLER_BUTTON_R3;\n"
        "\telse if (action == \"l3\") value = CHIAKI_CONTROLLER_BUTTON_L3;\n"
        "\telse if (action == \"l2\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_L2;\n"
        "\telse if (action == \"r2\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_R2;\n"
        "\telse if (action == \"focus\") value = CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3;\n"
        "\telse if (action == \"dpad_up\") value = CHIAKI_CONTROLLER_BUTTON_DPAD_UP;\n"
        "\telse if (action == \"dpad_down\") value = CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN;\n"
        "\telse if (action == \"dpad_left\") value = CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT;\n"
        "\telse if (action == \"dpad_right\") value = CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT;\n"
        "\telse if (action == \"touchpad\") value = CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\telse if (action == \"options\") value = CHIAKI_CONTROLLER_BUTTON_OPTIONS;\n"
        "\tQMap<int, int> profile;\n"
        "\tconst bool qwerty = vice_key_settings && vice_key_settings->GetViceKeyLayout().compare(\"QWERTY\", Qt::CaseInsensitive) == 0;\n"
        "\tprofile.insert(qwerty ? Qt::Key_W : Qt::Key_Z, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_UP));\n"
        "\tprofile.insert(Qt::Key_S, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_Y_DOWN));\n"
        "\tprofile.insert(qwerty ? Qt::Key_A : Qt::Key_Q, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_DOWN));\n"
        "\tprofile.insert(Qt::Key_D, static_cast<int>(ControllerButtonExt::ANALOG_STICK_LEFT_X_UP));\n"
        "\tprofile.insert(Qt::Key_Space, CHIAKI_CONTROLLER_BUTTON_CROSS);\n"
        "\tprofile.insert(Qt::Key_F, CHIAKI_CONTROLLER_BUTTON_MOON);\n"
        "\tprofile.insert(Qt::Key_R, CHIAKI_CONTROLLER_BUTTON_BOX);\n"
        "\tprofile.insert(Qt::Key_E, CHIAKI_CONTROLLER_BUTTON_PYRAMID);\n"
        "\tprofile.insert(Qt::Key_Tab, CHIAKI_CONTROLLER_BUTTON_R1);\n"
        "\tprofile.insert(Qt::Key_Shift, CHIAKI_CONTROLLER_BUTTON_L3);\n"
        "\tprofile.insert(Qt::Key_C, CHIAKI_CONTROLLER_BUTTON_R3);\n"
        "\tprofile.insert(Qt::Key_T, CHIAKI_CONTROLLER_BUTTON_DPAD_UP);\n"
        "\tprofile.insert(Qt::Key_V, CHIAKI_CONTROLLER_BUTTON_DPAD_DOWN);\n"
        "\tprofile.insert(Qt::Key_Left, CHIAKI_CONTROLLER_BUTTON_DPAD_LEFT);\n"
        "\tprofile.insert(Qt::Key_Right, CHIAKI_CONTROLLER_BUTTON_DPAD_RIGHT);\n"
        "\tprofile.insert(Qt::Key_Comma, CHIAKI_CONTROLLER_BUTTON_TOUCHPAD);\n"
        "\tprofile.insert(Qt::Key_Escape, CHIAKI_CONTROLLER_BUTTON_OPTIONS);\n"
        "\tprofile.insert(Qt::Key_CapsLock, CHIAKI_CONTROLLER_BUTTON_L3 | CHIAKI_CONTROLLER_BUTTON_R3);\n"
        "\tif (vice_key_settings) { const auto overrides = vice_key_settings->GetViceKeyMappings(); for (auto it = overrides.cbegin(); it != overrides.cend(); ++it) { if (it.value() <= 0) profile.remove(it.key()); else profile.insert(it.key(), it.value()); } }\n"
        "\tif (action == \"square\") {\n"
        "\t\tif (profile.value(fallback, 0) == value) return fallback;\n"
        "\t\tconst int otherDefault = fallback == Qt::Key_F ? Qt::Key_R : Qt::Key_F;\n"
        "\t\tconst bool otherStillMapped = profile.value(otherDefault, 0) == value;\n"
        "\t\tconst int desired = otherStillMapped ? 0 : occurrence;\n"
        "\t\tint foundSquare = 0;\n"
        "\t\tfor (auto it = profile.cbegin(); it != profile.cend(); ++it) {\n"
        "\t\t\tif (it.value() != value || (otherStillMapped && it.key() == otherDefault)) continue;\n"
        "\t\t\tif (foundSquare++ == desired) return it.key();\n"
        "\t\t}\n"
        "\t\treturn fallback;\n"
        "\t}\n"
        "\tint found = 0;\n"
        "\tfor (auto it = profile.cbegin(); it != profile.cend(); ++it) if (it.value() == value && found++ == occurrence) return it.key();\n"
        "\treturn fallback;\n"
        "}\n\n"
        "int StreamSession::viceKeyCurrentMouseButton(const QString &action, int fallback) const\n{\n"
        "\tint value = 0;\n"
        "\tif (action == \"fire\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_R2;\n"
        "\telse if (action == \"aim\") value = CHIAKI_CONTROLLER_ANALOG_BUTTON_L2;\n"
        "\telse if (action == \"l3\") value = CHIAKI_CONTROLLER_BUTTON_L3;\n"
        "\telse if (action == \"r3\") value = CHIAKI_CONTROLLER_BUTTON_R3;\n"
        "\telse if (action == \"touchpad\") value = CHIAKI_CONTROLLER_BUTTON_TOUCHPAD;\n"
        "\tfor (auto it = vice_key_mouse_map.cbegin(); it != vice_key_mouse_map.cend(); ++it) if (it.value() == value) return it.key();\n"
        "\treturn fallback;\n"
        "}\n\n"
        "void StreamSession::ReleaseKeyboardInput()\n{\n"
        "\tchiaki_controller_state_set_idle(&keyboard_state);\n"
        "\tvice_key_mouse_aiming = false;\n"
        "\tvice_key_mouse_initialized = false;\n"
        "\tvice_key_tab_down = false;\n"
        "\tvice_key_wheel_l2_down = false; vice_key_wheel_r2_down = false; vice_key_wheel_button_mask = 0;\n"
        "\tvice_key_pressed_keys.clear(); vice_key_pressed_mouse_buttons.clear();\n"
        "\tif (vice_key_wheel_reset_timer) vice_key_wheel_reset_timer->stop();\n"
        "\tif (vice_key_mouse_reset_timer && !vice_key_mouse_reset_timer->isActive()) vice_key_mouse_reset_timer->start();\n"
        "\tSendFeedbackState();\n"
        "}\n\n"
    )
    replace_once(stream_cpp,
        "void StreamSession::HandleMousePressEvent(QMouseEvent *event)\n",
        session_methods + "void StreamSession::HandleMousePressEvent(QMouseEvent *event)\n",
        "live session controls")

    # F1 opens the ViceKey in-stream overlay. Overlay interaction must suppress
    # global shortcuts so keys such as Q and F1 can be rebound safely.
    insert_after(root / "gui/include/qmlmainwindow.h",
        "    void menuRequested();\n",
        "    void viceKeyOverlayRequested();\n",
        "F1 overlay signal")
    replace_once(mainwindow_cpp,
        "    if (event->modifiers() == Qt::NoModifier) {\n        switch (event->key()) {\n        case Qt::Key_F11:\n",
        "    if (event->modifiers() == Qt::NoModifier && session && settings && event->key() == settings->GetViceKeyOverlayKey()) {\n        session->ReleaseKeyboardInput();\n        emit viceKeyOverlayRequested();\n        return true;\n    }\n"
        "    if (event->modifiers() == Qt::NoModifier) {\n        switch (event->key()) {\n        case Qt::Key_F11:\n",
        "F1 shortcut")
    replace_once(mainwindow_cpp,
        "    case QEvent::KeyPress:\n        if (handleShortcut(static_cast<QKeyEvent*>(event)))\n            return true;\n",
        "    case QEvent::Wheel:\n        if (session && !grab_input && session->HandleMouseWheelEvent(static_cast<QWheelEvent*>(event)))\n            return true;\n        QGuiApplication::sendEvent(quick_window, event);\n        break;\n    case QEvent::KeyPress:\n        if (!grab_input && handleShortcut(static_cast<QKeyEvent*>(event)))\n            return true;\n",
        "route Tab + wheel and suppress game shortcuts while overlay captures input")

    # Native QML overlay: F1, editable keyboard bindings, live mouse sensitivity,
    # and persistent AZERTY/QWERTY selection. It sits above the live stream.
    replace_once(root / "gui/src/qml/StreamView.qml",
        "            menuController.closing ||\n"
        "            sessionStopDialogActive ||\n",
        "            menuController.closing ||\n"
        "            viceKeyOverlay.visible ||\n"
        "            sessionStopDialogActive ||\n",
        "mark ViceKey as an interactive overlay")

    insert_after(root / "gui/src/qml/StreamView.qml",
        "    property bool sessionPinDialogActive: false\n",
        """    property int viceKeyCaptureIndex: -1
    property int viceKeyMouseCaptureIndex: -1
    property string viceKeyNotice: ""
    property int viceKeyActiveTab: 0
    property string viceKeyLanguage: Chiaki.settings.viceKeyLanguage
    function vt(fr, en) { return viceKeyLanguage === "EN" ? en : fr; }
    property bool viceKeyHotkeyCapture: false
    property var viceKeyRows: [
        { label: "Avancer", action: "left_y_up", key: Qt.Key_Z, display: "Z" },
        { label: "Gauche", action: "left_x_down", key: Qt.Key_Q, display: "Q" },
        { label: "Reculer", action: "left_y_down", key: Qt.Key_S, display: "S" },
        { label: "Droite", action: "left_x_up", key: Qt.Key_D, display: "D" },
        { label: "Croix", action: "cross", key: Qt.Key_Space, display: "Space" },
        { label: "Rond", action: "circle", key: Qt.Key_F, display: "F" },
        { label: "Carré", action: "square", key: Qt.Key_R, display: "R" },
        { label: "Triangle", action: "triangle", key: Qt.Key_E, display: "E" },
        { label: "R1", action: "r1", key: Qt.Key_Tab, display: "Tab" },
        { label: "L3", action: "l3", key: Qt.Key_Shift, display: "Shift" },
        { label: "R3", action: "r3", key: Qt.Key_C, display: "C" },
        { label: "D-Pad Haut", action: "dpad_up", key: Qt.Key_T, display: "T" },
        { label: "D-Pad Bas", action: "dpad_down", key: Qt.Key_V, display: "V" },
        { label: "D-Pad Gauche", action: "dpad_left", key: Qt.Key_Left, display: "Left" },
        { label: "D-Pad Droite", action: "dpad_right", key: Qt.Key_Right, display: "Right" },
        { label: "Touchpad / carte", action: "touchpad", key: Qt.Key_Comma, display: "," },
        { label: "Options", action: "options", key: Qt.Key_Escape, display: "Esc" },
        { label: "Concentration", action: "focus", key: Qt.Key_CapsLock, display: "Caps" }
    ]
    property var viceKeyKeyboardRows: []
    property var viceKeyControllerButtons: [
        { label: "✕ Croix", action: "cross" }, { label: "○ Rond", action: "circle" },
        { label: "□ Carré", action: "square" }, { label: "△ Triangle", action: "triangle" },
        { label: "L1", action: "l1" }, { label: "R1", action: "r1" },
        { label: "L2", action: "l2" }, { label: "R2", action: "r2" },
        { label: "L3", action: "l3" }, { label: "R3", action: "r3" },
        { label: "L3 + R3", action: "focus" },
        { label: "D-Pad ↑", action: "dpad_up" }, { label: "D-Pad ↓", action: "dpad_down" },
        { label: "D-Pad ←", action: "dpad_left" }, { label: "D-Pad →", action: "dpad_right" },
        { label: "Touchpad", action: "touchpad" }, { label: "Options", action: "options" },
        { label: "Stick G ↑", action: "left_y_up" }, { label: "Stick G ↓", action: "left_y_down" },
        { label: "Stick G ←", action: "left_x_down" }, { label: "Stick G →", action: "left_x_up" },
        { label: "Aucune", action: "none" }
    ]
    property var viceKeyMouseTargets: [
        { label: "Clic gauche", input: Qt.LeftButton }, { label: "Clic droit", input: Qt.RightButton },
        { label: "Clic molette", input: Qt.MiddleButton }, { label: "Molette ↑ (Tab)", input: 1001 },
        { label: "Molette ↓ (Tab)", input: 1002 }, { label: "Bouton 4", input: Qt.XButton1 },
        { label: "Bouton 5", input: Qt.XButton2 }
    ]
    function viceKeyKey(label, key, width) {
        return { label: label, key: key, width: width || 39 };
    }
    function viceKeyBuildKeyboardRows(layout) {
        var q = layout === "QWERTY";
        return [
            [viceKeyKey("Esc", Qt.Key_Escape, 50), viceKeyKey("1", Qt.Key_1), viceKeyKey("2", Qt.Key_2), viceKeyKey("3", Qt.Key_3), viceKeyKey("4", Qt.Key_4), viceKeyKey("5", Qt.Key_5), viceKeyKey("6", Qt.Key_6), viceKeyKey("7", Qt.Key_7), viceKeyKey("8", Qt.Key_8), viceKeyKey("9", Qt.Key_9), viceKeyKey("0", Qt.Key_0), viceKeyKey("-", Qt.Key_Minus), viceKeyKey("=", Qt.Key_Equal), viceKeyKey("⌫", Qt.Key_Backspace, 66)],
            q ? [viceKeyKey("Tab", Qt.Key_Tab, 56), viceKeyKey("Q", Qt.Key_Q), viceKeyKey("W", Qt.Key_W), viceKeyKey("E", Qt.Key_E), viceKeyKey("R", Qt.Key_R), viceKeyKey("T", Qt.Key_T), viceKeyKey("Y", Qt.Key_Y), viceKeyKey("U", Qt.Key_U), viceKeyKey("I", Qt.Key_I), viceKeyKey("O", Qt.Key_O), viceKeyKey("P", Qt.Key_P), viceKeyKey("[", Qt.Key_BracketLeft), viceKeyKey("]", Qt.Key_BracketRight)] :
               [viceKeyKey("Tab", Qt.Key_Tab, 56), viceKeyKey("A", Qt.Key_A), viceKeyKey("Z", Qt.Key_Z), viceKeyKey("E", Qt.Key_E), viceKeyKey("R", Qt.Key_R), viceKeyKey("T", Qt.Key_T), viceKeyKey("Y", Qt.Key_Y), viceKeyKey("U", Qt.Key_U), viceKeyKey("I", Qt.Key_I), viceKeyKey("O", Qt.Key_O), viceKeyKey("P", Qt.Key_P), viceKeyKey("^", Qt.Key_Dead_Circumflex), viceKeyKey("$", Qt.Key_Dollar)],
            q ? [viceKeyKey("Caps", Qt.Key_CapsLock, 66), viceKeyKey("A", Qt.Key_A), viceKeyKey("S", Qt.Key_S), viceKeyKey("D", Qt.Key_D), viceKeyKey("F", Qt.Key_F), viceKeyKey("G", Qt.Key_G), viceKeyKey("H", Qt.Key_H), viceKeyKey("J", Qt.Key_J), viceKeyKey("K", Qt.Key_K), viceKeyKey("L", Qt.Key_L), viceKeyKey(";", Qt.Key_Semicolon), viceKeyKey("'", Qt.Key_Apostrophe), viceKeyKey("↵", Qt.Key_Return, 62)] :
               [viceKeyKey("Caps", Qt.Key_CapsLock, 66), viceKeyKey("Q", Qt.Key_Q), viceKeyKey("S", Qt.Key_S), viceKeyKey("D", Qt.Key_D), viceKeyKey("F", Qt.Key_F), viceKeyKey("G", Qt.Key_G), viceKeyKey("H", Qt.Key_H), viceKeyKey("J", Qt.Key_J), viceKeyKey("K", Qt.Key_K), viceKeyKey("L", Qt.Key_L), viceKeyKey("M", Qt.Key_M), viceKeyKey("'", Qt.Key_Apostrophe), viceKeyKey("↵", Qt.Key_Return, 62)],
            q ? [viceKeyKey("Shift", Qt.Key_Shift, 78), viceKeyKey("Z", Qt.Key_Z), viceKeyKey("X", Qt.Key_X), viceKeyKey("C", Qt.Key_C), viceKeyKey("V", Qt.Key_V), viceKeyKey("B", Qt.Key_B), viceKeyKey("N", Qt.Key_N), viceKeyKey("M", Qt.Key_M), viceKeyKey(",", Qt.Key_Comma), viceKeyKey(".", Qt.Key_Period), viceKeyKey("/", Qt.Key_Slash), viceKeyKey("Shift", Qt.Key_Shift, 78)] :
               [viceKeyKey("Shift", Qt.Key_Shift, 78), viceKeyKey("W", Qt.Key_W), viceKeyKey("X", Qt.Key_X), viceKeyKey("C", Qt.Key_C), viceKeyKey("V", Qt.Key_V), viceKeyKey("B", Qt.Key_B), viceKeyKey("N", Qt.Key_N), viceKeyKey(",", Qt.Key_Comma), viceKeyKey(";", Qt.Key_Semicolon), viceKeyKey(":", Qt.Key_Colon), viceKeyKey("!", Qt.Key_Exclam), viceKeyKey("Shift", Qt.Key_Shift, 78)],
            [viceKeyKey("Ctrl", Qt.Key_Control, 62), viceKeyKey("Alt", Qt.Key_Alt, 52), viceKeyKey("Space", Qt.Key_Space, 250), viceKeyKey("Alt", Qt.Key_Alt, 52), viceKeyKey("Ctrl", Qt.Key_Control, 62), viceKeyKey("←", Qt.Key_Left, 38), viceKeyKey("↓", Qt.Key_Down, 38), viceKeyKey("→", Qt.Key_Right, 38)]
        ];
    }
    function viceKeyActionLabel(action) {
        var labels = { none: "—", cross: "✕ Croix", circle: "○ Rond", square: "□ Carré", triangle: "△ Triangle", l1: "L1", r1: "R1", l2: "L2", r2: "R2", l3: "L3", r3: "R3", focus: "L3 + R3", dpad_up: "D-Pad ↑", dpad_down: "D-Pad ↓", dpad_left: "D-Pad ←", dpad_right: "D-Pad →", touchpad: "Touchpad", options: "Options", left_y_up: "Stick G ↑", left_y_down: "Stick G ↓", left_x_down: "Stick G ←", left_x_up: "Stick G →" };
        return labels[action] || "—";
    }
    function viceKeyName(key) {
        if (key >= Qt.Key_A && key <= Qt.Key_Z) return String.fromCharCode(key);
        if (key === Qt.Key_Space) return "Space";
        if (key === Qt.Key_Shift) return "Shift";
        if (key === Qt.Key_Tab) return "Tab";
        if (key === Qt.Key_Control) return "Ctrl";
        if (key === Qt.Key_Alt) return "Alt";
        if (key === Qt.Key_Return || key === Qt.Key_Enter) return "Enter";
        if (key === Qt.Key_Backspace) return "Backspace";
        if (key === Qt.Key_Comma) return ",";
        if (key === Qt.Key_Escape) return "Esc";
        if (key === Qt.Key_Left) return "←";
        if (key === Qt.Key_Right) return "→";
        if (key === Qt.Key_F1) return "F1";
        if (key === Qt.Key_F2) return "F2";
        if (key === Qt.Key_F3) return "F3";
        if (key === Qt.Key_F4) return "F4";
        if (key === Qt.Key_F5) return "F5";
        if (key === Qt.Key_F6) return "F6";
        if (key === Qt.Key_F7) return "F7";
        if (key === Qt.Key_F8) return "F8";
        if (key === Qt.Key_F9) return "F9";
        if (key === Qt.Key_F10) return "F10";
        if (key === Qt.Key_F11) return "F11";
        if (key === Qt.Key_F12) return "F12";
        return "Key " + key;
    }
    function viceKeySyncDisplay() {
        viceKeyKeyboardRows = viceKeyBuildKeyboardRows(Chiaki.settings.viceKeyLayout);
    }
    function viceKeySetLayout(layout) {
        Chiaki.settings.viceKeyLayout = layout;
        if (Chiaki.session) Chiaki.session.setViceKeyLayout(layout);
        viceKeyKeyboardRows = viceKeyBuildKeyboardRows(layout);
        viceKeyNotice = "Keyboard layout: " + layout;
    }
        """,
        "ViceKey keyboard, mouse and DualSense mapping model")

    insert_after(root / "gui/src/qml/StreamView.qml",
        "        Chiaki.settings.viceKeyLayout = layout;\n"
        "        if (Chiaki.session) Chiaki.session.setViceKeyLayout(layout);\n"
        "        viceKeyKeyboardRows = viceKeyBuildKeyboardRows(layout);\n"
        "        viceKeyNotice = \"Keyboard layout: \" + layout;\n"
        "    }\n",
        "    property var viceKeyMouseRows: [\n"
        "        { label: \"Fire\", action: \"fire\", button: Qt.LeftButton, display: \"Left click\" },\n"
        "        { label: \"Aim\", action: \"aim\", button: Qt.RightButton, display: \"Right click\" }\n"
        "    ]\n"
        "    function viceKeyMouseName(button) {\n"
        "        if (button === Qt.LeftButton) return \"Left click\";\n"
        "        if (button === Qt.RightButton) return \"Right click\";\n"
        "        if (button === Qt.MiddleButton) return \"Middle click\";\n"
        "        if (button === Qt.XButton1) return \"Mouse 4\";\n"
        "        if (button === Qt.XButton2) return \"Mouse 5\";\n"
        "        return \"Mouse button \" + button;\n"
        "    }\n",
        "ViceKey mouse binding model")

    insert_after(root / "gui/src/qml/StreamView.qml",
        "    Component.onCompleted: {\n        updateSeparateMenuGeometry();\n        updateOverlayInteractionActive();\n        Chiaki.window.setStatsOverlayActive(streamStatsVisible);\n",
        "        if (Chiaki.settings.viceKeyLayout === \"QWERTY\") viceKeySetLayout(\"QWERTY\");\n"
        "        else viceKeySyncDisplay();\n",
        "initialize current ViceKey layout")

    replace_once(root / "gui/src/qml/StreamView.qml",
        "    Item {\n        id: menuView\n",
        "    Rectangle {\n"
        "        id: viceKeyOverlay\n"
        "        anchors.fill: parent\n"
        "        z: 1000\n"
        "        visible: false\n"
        "        color: \"#d90b0b0b\"\n"
        "        focus: visible\n"
        "        onVisibleChanged: {\n"
        "            if (visible) { if (Chiaki.session) Chiaki.session.setViceKeyMouseCaptureEnabled(false); view.grabInput(viceKeyOverlay); }\n"
        "            else { viceKeyCaptureIndex = -1; viceKeyMouseCaptureIndex = -1; viceKeyHotkeyCapture = false; if (Chiaki.session) Chiaki.session.setViceKeyMouseCaptureEnabled(true); view.releaseInput(); }\n"
        "            view.updateOverlayInteractionActive();\n"
        "        }\n"
        "        MouseArea {\n"
        "            anchors.fill: parent\n"
        "            z: 3\n"
        "            enabled: viceKeyMouseCaptureIndex >= 0\n"
        "            visible: enabled\n"
        "            acceptedButtons: Qt.AllButtons\n"
        "            onPressed: function(mouse) {\n"
        "                var rows = viceKeyMouseRows.slice(0);\n"
        "                var row = rows[viceKeyMouseCaptureIndex];\n"
        "                var collision = rows.findIndex(function(other, i) { return i !== viceKeyMouseCaptureIndex && other.button === mouse.button; });\n"
        "                if (collision >= 0) { viceKeyNotice = \"That mouse button is already assigned to \" + rows[collision].label; mouse.accepted = true; return; }\n"
        "                var oldButton = row.button;\n"
        "                row.button = mouse.button; row.display = view.viceKeyMouseName(mouse.button);\n"
        "                rows[viceKeyMouseCaptureIndex] = row; viceKeyMouseRows = rows;\n"
        "                if (Chiaki.session) Chiaki.session.setViceKeyMouseMapping(oldButton, mouse.button, row.action);\n"
        "                viceKeyNotice = row.label + \" is now \" + row.display;\n"
        "                viceKeyMouseCaptureIndex = -1; mouse.accepted = true;\n"
        "            }\n"
        "        }\n"
        "        Keys.onPressed: function(event) {\n"
        "            if (viceKeyHotkeyCapture) {\n"
        "                if (event.key !== Qt.Key_unknown && event.key !== Qt.Key_Escape) {\n"
        "                    var hotkeyCollision = viceKeyRows.findIndex(function(row) { return row.key === event.key; });\n"
        "                    if (hotkeyCollision >= 0) viceKeyNotice = \"That key is assigned to \" + viceKeyRows[hotkeyCollision].label + \". Unbind it first.\";\n"
        "                    else { Chiaki.settings.viceKeyOverlayKey = event.key; viceKeyNotice = \"Overlay shortcut: \" + view.viceKeyName(event.key); }\n"
        "                }\n"
        "                viceKeyHotkeyCapture = false; event.accepted = true; return;\n"
        "            }\n"
        "            if (viceKeyCaptureIndex >= 0) {\n"
        "                if (event.key === Qt.Key_Escape) { viceKeyCaptureIndex = -1; viceKeyNotice = \"Capture cancelled\"; event.accepted = true; return; }\n"
        "                if (event.key === Qt.Key_unknown) { event.accepted = true; return; }\n"
        "                var rows = viceKeyRows.slice(0);\n"
        "                var row = rows[viceKeyCaptureIndex];\n"
        "                var collision = rows.findIndex(function(other, i) { return i !== viceKeyCaptureIndex && other.key === event.key; });\n"
        "                if (event.key === Chiaki.settings.viceKeyOverlayKey) { viceKeyNotice = \"That key is reserved for the overlay shortcut.\"; event.accepted = true; return; }\n"
        "                if (collision >= 0) { viceKeyNotice = \"That key is already assigned to \" + rows[collision].label + \". Choose another key.\"; event.accepted = true; return; }\n"
        "                var oldKey = row.key;\n"
        "                row.key = event.key; row.display = view.viceKeyName(event.key);\n"
        "                rows[viceKeyCaptureIndex] = row; viceKeyRows = rows;\n"
        "                if (Chiaki.session) Chiaki.session.setViceKeyMapping(oldKey, event.key, row.action);\n"
        "                viceKeyNotice = row.label + \" is now \" + row.display;\n"
        "                viceKeyCaptureIndex = -1; event.accepted = true; return;\n"
        "            }\n"
        "            if (event.key === Qt.Key_Escape || event.key === Chiaki.settings.viceKeyOverlayKey) { visible = false; event.accepted = true; return; }\n"
        "            event.accepted = true;\n"
        "        }\n"
        "        Rectangle {\n"
        "            anchors.centerIn: parent\n"
        "            width: Math.min(parent.width - 36, 1160)\n"
        "            height: Math.min(parent.height - 36, 780)\n"
        "            radius: 12\n"
        "            color: \"#f0191919\"\n"
        "            border.color: \"#303030\"\n"
        "            border.width: 1\n"
        "            ColumnLayout {\n"
        "                anchors.fill: parent\n"
        "                anchors.margins: 22\n"
        "                spacing: 12\n"
        "                RowLayout {\n"
        "                    Layout.fillWidth: true\n"
        "                    Label { text: \"VICEKEY\"; font.pixelSize: 22; font.bold: true; color: \"#f2f4f7\" }\n"
        "                    Label { text: \"IN-GAME CONTROLS\"; color: \"#94a3b3\" }\n"
        "                    Item { Layout.fillWidth: true }\n"
        "                    Button { text: \"Close  Esc\"; onClicked: viceKeyOverlay.visible = false }\n"
        "                }\n"
        "                TabBar {\n"
        "                    Layout.fillWidth: true\n"
        "                    currentIndex: view.viceKeyActiveTab\n"
        "                    onCurrentIndexChanged: view.viceKeyActiveTab = currentIndex\n"
        "                    TabButton { text: view.vt(\"Souris\", \"Mouse\") }\n"
        "                    TabButton { text: view.vt(\"Clavier\", \"Keyboard\") }\n"
        "                    TabButton { text: view.vt(\"Réglages\", \"Settings\") }\n"
        "                }\n"
        """                RowLayout {\n
                    visible: view.viceKeyActiveTab === 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 14
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        ColumnLayout {
                            width: parent.width
                            Label { text: "CLAVIER " + Chiaki.settings.viceKeyLayout; color: "#e2e8f0"; font.bold: true }
                            Repeater {
                                model: view.viceKeyKeyboardRows
                                delegate: Flow {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    property var rowKeys: modelData
                                    Repeater {
                                        model: rowKeys
                                        delegate: Rectangle {
                                            id: physicalKey
                                            property int keyCode: modelData.key
                                            property string keyLabel: modelData.label
                                            width: modelData.width || 39
                                            height: 55
                                            radius: 5
                                            color: "#292929"
                                            border.color: "#414141"
                                            border.width: 1
                                            Column {
                                                anchors.centerIn: parent
                                                spacing: 3
                                                Text { text: physicalKey.keyLabel; color: "#eef2f6"; font.bold: true; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                                                Text {
                                                    text: Chiaki.session ? view.viceKeyActionLabel(Chiaki.session.viceKeyActionForKey(physicalKey.keyCode)) : "—"
                                                    color: "#9fc3ed"; font.pixelSize: 9; anchors.horizontalCenter: parent.horizontalCenter
                                                }
                                            }
                                            DropArea {
                                                anchors.fill: parent
                                                onDropped: function(drop) {
                                                    if (!drop.source || !drop.source.actionId || !Chiaki.session) return;
                                                    Chiaki.session.setViceKeyButton(physicalKey.keyCode, drop.source.actionId);
                                                    view.viceKeyNotice = physicalKey.keyLabel + " ← " + view.viceKeyActionLabel(drop.source.actionId);
                                                    drop.acceptProposedAction();
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            Label { text: "Glisse un bouton DualSense sur une touche pour l'affecter"; color: "#91a4b8"; wrapMode: Text.WordWrap }
                        }
                    }
                    Rectangle { width: 1; Layout.fillHeight: true; color: "#383838" }
                    ColumnLayout {
                        Layout.preferredWidth: 230
                        Layout.fillHeight: true
                        Label { text: "SOURIS"; color: "#e2e8f0"; font.bold: true }
                        Repeater {
                            model: view.viceKeyMouseTargets
                            delegate: Rectangle {
                                id: mouseTarget
                                property int inputCode: modelData.input
                                property string inputLabel: modelData.label
                                Layout.fillWidth: true
                                height: 49
                                radius: 6
                                color: "#292929"
                                border.color: "#414141"
                                Column {
                                    anchors.centerIn: parent
                                    spacing: 2
                                    Text { text: mouseTarget.inputLabel; color: "#eef2f6"; font.pixelSize: 11; anchors.horizontalCenter: parent.horizontalCenter }
                                    Text {
                                        text: Chiaki.session ? view.viceKeyActionLabel(Chiaki.session.viceKeyActionForMouseInput(mouseTarget.inputCode)) : "—"
                                        color: "#9fc3ed"; font.pixelSize: 10; anchors.horizontalCenter: parent.horizontalCenter
                                    }
                                }
                                DropArea {
                                    anchors.fill: parent
                                    onDropped: function(drop) {
                                        if (!drop.source || !drop.source.actionId || !Chiaki.session) return;
                                        Chiaki.session.setViceKeyMouseInput(mouseTarget.inputCode, drop.source.actionId);
                                        view.viceKeyNotice = mouseTarget.inputLabel + " ← " + view.viceKeyActionLabel(drop.source.actionId);
                                        drop.acceptProposedAction();
                                    }
                                }
                            }
                        }
                    }
                }
                Label { visible: view.viceKeyActiveTab === 1; text: "BOUTONS DUALSENSE À GLISSER"; color: "#e2e8f0"; font.bold: true }
                Flow {
                    visible: view.viceKeyActiveTab === 1
                    Layout.fillWidth: true
                    spacing: 7
                    Repeater {
                        model: view.viceKeyControllerButtons
                        delegate: Rectangle {
                            id: controllerChip
                            property string actionId: modelData.action
                            width: Math.max(64, chipLabel.implicitWidth + 22)
                            height: 34
                            radius: 7
        "                            color: actionId === \\"cross\\" ? \\"#2878ff\\" : actionId === \\"circle\\" ? \\"#f04444\\" : actionId === \\"triangle\\" ? \\"#28b86b\\" : actionId === \\"square\\" ? \\"#b56bff\\" : \\"#292929\\"\\n"
        "                            border.color: actionId === \\"cross\\" ? \\"#70a5ff\\" : actionId === \\"circle\\" ? \\"#ff8a8a\\" : actionId === \\"triangle\\" ? \\"#78e0a3\\" : actionId === \\"square\\" ? \\"#d1a2ff\\" : \\"#414141\\"\\n"
                            Drag.active: chipDrag.active
                            Drag.source: controllerChip
                            Drag.hotSpot.x: width / 2
                            Drag.hotSpot.y: height / 2
                            Drag.supportedActions: Qt.CopyAction
                            Text { id: chipLabel; anchors.centerIn: parent; text: modelData.label; color: "#f0f4f8"; font.pixelSize: 11; font.bold: true }
                            DragHandler { id: chipDrag; target: null }
                        }
                    }
                }
                Label { visible: view.viceKeyActiveTab === 1; text: "Le bouton PS5 choisi est envoyé tel quel au jeu. Les actions contextuelles restent gérées par GTA."; color: "#91a4b8"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
"""
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 2\n"
        "                    Label { text: view.vt(\\"Langue\\", \\"Language\\"); color: \\"#cbd5df\\" }\\n"
        "                    ComboBox { model: [\\"Français\\", \\"English\\"]; currentIndex: view.viceKeyLanguage === \\"EN\\" ? 1 : 0; onActivated: function(index) { Chiaki.settings.viceKeyLanguage = index === 1 ? \\"EN\\" : \\"FR\\"; view.viceKeyLanguage = Chiaki.settings.viceKeyLanguage; } }\\n"
        "                    Button { text: view.vt(\"Exporter le profil…\", \"Export profile…\"); onClicked: { if (Chiaki.settings.exportViceKeyProfile()) view.viceKeyNotice = \"Profile exported\"; } }\n"
        "                    Button { text: view.vt(\"Importer un profil…\", \"Import profile…\"); onClicked: { if (Chiaki.settings.importViceKeyProfile()) { if (Chiaki.session) { Chiaki.session.setViceKeyLayout(Chiaki.settings.viceKeyLayout); Chiaki.session.setViceKeySensitivity(Chiaki.settings.viceKeySensitivity); Chiaki.session.setViceKeyAimSensitivity(Chiaki.settings.viceKeyAimSensitivity); } view.viceKeySetLayout(Chiaki.settings.viceKeyLayout); view.viceKeyNotice = \"Profile imported\"; } } }\n"
        "                    Item { Layout.fillWidth: true }\n"
        "                }\n"
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 2\n"
        "                    Label { text: \"Overlay shortcut\"; color: \"#cbd5df\" }\n"
        "                    Button { text: view.viceKeyHotkeyCapture ? \"Press shortcut…\" : view.viceKeyName(Chiaki.settings.viceKeyOverlayKey); onClicked: { view.viceKeyHotkeyCapture = true; viceKeyOverlay.forceActiveFocus(); view.viceKeyNotice = \"Press a key for the overlay shortcut\"; } }\n"
        "                    Item { Layout.fillWidth: true }\n"
        "                }\n"
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 2\n"
        "                    Label { text: \"Keyboard layout\"; color: \"#cbd5df\" }\n"
        "                    ComboBox {\n"
        "                        id: viceKeyLayoutBox\n"
        "                        model: [\"AZERTY\", \"QWERTY\"]\n"
        "                        currentIndex: Chiaki.settings.viceKeyLayout === \"QWERTY\" ? 1 : 0\n"
        "                        onActivated: function(index) { view.viceKeySetLayout(model[index]); }\n"
        "                    }\n"
        "                    Item { Layout.fillWidth: true }\n"
        "                    Label { text: view.vt(\"Les changements sont enregistrés automatiquement\", \"Changes save automatically\"); color: \"#91a4b8\" }\n"
        "                }\n"
        "                Label { visible: false; text: \"COMMANDES CLAVIER\"; color: \"#e2e8f0\"; font.bold: true }\n"
        "                ComboBox {\n"
        "                    visible: false\n"
        "                    Layout.fillWidth: true\n"
        "                    model: [\"À pied\", \"Combat\", \"Menus\", \"Véhicules\", \"Avions et hélicoptères\", \"Vélos\", \"Natation et plongée\", \"Parachute\"]\n"
        "                    currentIndex: model.indexOf(view.viceKeyKeyboardCategory)\n"
        "                    onActivated: function(index) { view.viceKeyKeyboardCategory = model[index]; }\n"
        "                }\n"
        "                ScrollView {\n"
        "                    visible: false\n"
        "                    Layout.fillWidth: true\n"
        "                    Layout.fillHeight: true\n"
        "                    clip: true\n"
        "                    ColumnLayout {\n"
        "                        width: parent.width\n"
        "                        Repeater {\n"
        "                            model: view.viceKeyRows.filter(function(row) { return row.category === view.viceKeyKeyboardCategory; })\n"
        "                            delegate: RowLayout {\n"
        "                                Layout.fillWidth: true\n"
        "                                Label { text: modelData.label; color: \"#d9e0e8\"; Layout.fillWidth: true }\n"
        "                                Button {\n"
        "                                    Layout.preferredWidth: 130\n"
        "                                    text: view.viceKeyCaptureIndex === view.viceKeyRows.indexOf(modelData) ? \"Press a key…\" : modelData.display\n"
        "                                    highlighted: view.viceKeyCaptureIndex === view.viceKeyRows.indexOf(modelData)\n"
        "                                    onClicked: { view.viceKeyCaptureIndex = view.viceKeyRows.indexOf(modelData); viceKeyOverlay.forceActiveFocus(); view.viceKeyNotice = \"Waiting for key…\"; }\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "                Label { visible: view.viceKeyActiveTab === 0; text: view.vt(\"MOUSE BUTTONS\", \"BOUTONS DE LA SOURIS\"); color: \"#e2e8f0\"; font.bold: true }\n"
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 0\n"
        "                    Layout.fillWidth: true\n"
        "                    Repeater {\n"
        "                        model: view.viceKeyMouseRows\n"
        "                        delegate: ColumnLayout {\n"
        "                            Layout.fillWidth: true\n"
        "                            Label { text: modelData.label; color: \"#cbd5df\" }\n"
        "                            Button { text: view.viceKeyMouseCaptureIndex === index ? \"Press mouse…\" : modelData.display; onClicked: { view.viceKeyMouseCaptureIndex = index; viceKeyOverlay.forceActiveFocus(); view.viceKeyNotice = \"Waiting for mouse button…\"; } }\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "                Label { visible: view.viceKeyActiveTab === 2; text: view.vt(\"MOUSE SENSITIVITY\", \"SENSIBILITÉ SOURIS\"); color: \"#e2e8f0\"; font.bold: true }\n"
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 2\n"
        "                    Layout.fillWidth: true\n"
        "                    Label { text: \"Camera\"; color: \"#cbd5df\"; Layout.preferredWidth: 110 }\n"
        "                    Slider { Layout.fillWidth: true; from: 0.01; to: 100.0; stepSize: 0.05; value: Chiaki.settings.viceKeySensitivity; onMoved: { Chiaki.settings.viceKeySensitivity = value; if (Chiaki.session) Chiaki.session.setViceKeySensitivity(value); } }\n"
        "                    Label { text: Number(Chiaki.settings.viceKeySensitivity).toFixed(2); color: \"#f2f4f7\"; Layout.preferredWidth: 48 }\n"
        "                }\n"
        "                RowLayout {\n"
        "                    visible: view.viceKeyActiveTab === 2\n"
        "                    Layout.fillWidth: true\n"
        "                    Label { text: \"Aim\"; color: \"#cbd5df\"; Layout.preferredWidth: 110 }\n"
        "                    Slider { Layout.fillWidth: true; from: 0.01; to: 100.0; stepSize: 0.05; value: Chiaki.settings.viceKeyAimSensitivity; onMoved: { Chiaki.settings.viceKeyAimSensitivity = value; if (Chiaki.session) Chiaki.session.setViceKeyAimSensitivity(value); } }\n"
        "                    Label { text: Number(Chiaki.settings.viceKeyAimSensitivity).toFixed(2); color: \"#f2f4f7\"; Layout.preferredWidth: 48 }\n"
        "                }\n"
        "                Label { text: view.viceKeyNotice; color: \"#9cc6ff\"; wrapMode: Text.WordWrap; Layout.fillWidth: true }\n"
        "                RowLayout {\n"
        "                    Layout.fillWidth: true\n"
        "                    Label { text: \"Left click = R2 · Right click = L2 · Tab + wheel = L2 / R2 · optional side buttons start unassigned\"; color: \"#9aa8b7\"; wrapMode: Text.WordWrap; Layout.fillWidth: true }\n"
        "                    Button { text: view.vt(\"Terminé\", \"Done\"); onClicked: viceKeyOverlay.visible = false }\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    Item {\n        id: menuView\n",
        "in-stream ViceKey overlay")

    replace_once(root / "gui/src/qml/StreamView.qml",
        "        function onSessionChanged() {\n            if (!Chiaki.session)\n                menuController.close();\n        }\n",
        "        function onSessionChanged() {\n            if (!Chiaki.session) menuController.close();\n            else viceKeySyncDisplay();\n        }\n",
        "refresh ViceKey bindings when session changes")

    insert_after(root / "gui/src/qml/StreamView.qml",
        "        function onMenuRequested() {\n"
        "            if (sessionPinDialog.opened || sessionStopDialog.opened || separateSessionPinWindow.visible || separateSessionStopWindow.visible)\n"
        "                return;\n"
        "            menuController.toggle();\n"
        "            Chiaki.window.requestOverlayUpdate();\n"
        "        }\n",
        "        function onViceKeyOverlayRequested() {\n"
        "            if (sessionPinDialog.opened || sessionStopDialog.opened || separateSessionPinWindow.visible || separateSessionStopWindow.visible) return;\n"
        "            viceKeyOverlay.visible = !viceKeyOverlay.visible;\n"
        "            view.updateOverlayInteractionActive();\n"
        "            Chiaki.window.requestOverlayUpdate();\n"
        "        }\n\n",
        "overlay signal handler")

    # Set the product name in Qt metadata without changing the upstream copyright.
    main_source = main_cpp.read_text(encoding="utf-8")
    if 'QGuiApplication::setApplicationName("Chiaki");' in main_source:
        replace_once(main_cpp, 'QGuiApplication::setApplicationName("Chiaki");',
                     'QGuiApplication::setApplicationName("ViceKey");', "application name")
    if 'QGuiApplication::setApplicationDisplayName("chiaki-ng");' in main_source:
        replace_once(main_cpp, 'QGuiApplication::setApplicationDisplayName("chiaki-ng");',
                     'QGuiApplication::setApplicationDisplayName("ViceKey");', "application display name")

    marker = root / ".vickey-patched"
    marker.write_text("ViceKey patch applied to chiaki-ng v1.10.1\n", encoding="utf-8")
    print("ViceKey patch applied successfully.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path, help="Path to chiaki-ng checkout")
    args = parser.parse_args()
    root = args.checkout.resolve()
    if not (root / "CMakeLists.txt").exists():
        print(f"Not a chiaki-ng source checkout: {root}", file=sys.stderr)
        return 2
    if (root / ".vickey-patched").exists():
        print("ViceKey patch already applied.")
        return 0
    try:
        patch(root)
    except Exception as exc:
        print(f"PATCH FAILED: {exc}", file=sys.stderr)
        print("No build was started. Use a fresh v1.10.1 checkout.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())