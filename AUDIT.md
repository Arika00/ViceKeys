# ViceKey technical audit and implementation plan

## Scope

This audit is based on the files supplied for the ViceKey continuation task. The `audit/chiaki-ng-v1.10.1/` directory in the prepared local package contains selected Chiaki-ng source snapshots, not a complete checkout.

## Existing implementation

The supplied `apply-vickey.py` patcher currently:
- Adds persisted AZERTY/QWERTY, camera-sensitivity, and aim-sensitivity settings.
- Inserts a fixed keyboard mapping during stream-session setup.
- Adds fixed mouse-button handling for fire, aim, stick clicks, and touchpad.
- Converts mouse movement to the right analog stick using a short reset timer.
- Adds controls to the existing Settings dialog.
- Changes Q shortcut handling to avoid one AZERTY conflict.

This is an experimental baseline only. It does not implement dynamic remapping or an in-game overlay.

## Relevant architecture

### StreamView.qml
The supplied file contains existing menu/overlay infrastructure, including `menuController`, `grabInput()`, `releaseInput()`, `updateOverlayInteractionActive()`, `menuView`, and `menuContentComponent`. This is the preferred integration point for a ViceKey panel rendered over the Remote Play view.

### StreamMenuWindow.qml
The supplied file provides a reference for menu navigation, focus, activation, and close behavior. ViceKey should reuse relevant interaction conventions without making a separate top-level settings window its primary interface.

### Stream-session input handling
The patcher targets `StreamSession` keyboard and mouse event handlers, including `HandleKeyboardEvent()`, `HandleMousePressEvent()`, `HandleMouseReleaseEvent()`, and `HandleMouseMoveEvent()`. Controller state is ultimately sent through `SendFeedbackState()`.

### Settings
The existing `Settings` and `QmlSettings` classes are suitable integration points for persistent profiles and QML exposure. The runtime mapping should not be represented as hard-coded `QMap` inserts during session initialization.

## Target architecture

1. Runtime mapping model (C++): represent bindable physical inputs and controller actions as data; support keyboard keys, mouse buttons, wheel directions, and other supported inputs.
2. Input state engine (C++): translate press/release events to controller state, handle simultaneous inputs, prevent stuck buttons, and preserve physical-controller input.
3. Live settings API: update mappings and sensitivity values safely while a session is active.
4. Overlay UI (QML): integrate with `StreamView.qml`, with configurable toggle shortcut, per-action capture, conflict warnings, profile selection, reset, and focus restoration.
5. Persistence: store a default profile and user profiles through existing settings infrastructure.
6. Mouse look: use relative movement robustly, with independent camera and aim sensitivity, and prevent overlay/capture mode from leaking mouse input into gameplay.
7. Validation: test AZERTY/QWERTY, press/release pairs, simultaneous keys, mouse buttons, physical controllers, menu navigation, overlay focus, and live changes.

## Known blockers

- The supplied archive contains selected source files, not a complete Chiaki-ng checkout.
- `build-vickey.ps1` expects `build-vickey.sh`, which was not supplied.
- The prior patcher modifies `SettingsDialog.qml`, not an in-game overlay.
- Sensitivity values are copied into the session at connection time in the prior patch; no live-update path is demonstrated.
- The fixed mappings cannot support arbitrary user remapping.

## Required next input

A complete, clean Chiaki-ng checkout at the intended upstream revision is required to implement and validate the overlay and runtime input engine.

## Verification policy

Do not describe the overlay, dynamic remapping, live sensitivity updates, or Windows build as complete until implemented and verified against a full checkout. Keep build artifacts separate from personal machine configuration.
