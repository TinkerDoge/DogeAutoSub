#!/usr/bin/env python3
import re

with open("modules/ui_DogeAutoSub.py", "r") as f:
    content = f.read()

checks = {}

# 1. FramelessWindowHint
checks["FramelessWindowHint"] = "Qt.WindowType.FramelessWindowHint, True" in content

# 2. Required new widgets
new_widgets = [
    "sidebar", "sidebarSubtitlesItem", "sidebarNotesItem", "sidebarTranslateItem",
    "workflowStack", "paletteStripe", "paletteMenuButton", "phaseStrip",
    "logPanelHost", "mascotHost", "statusBar", "statusBarVersion", "statusBarGpu", "statusBarReady",
    "closeBtn", "minBtn", "zoomBtn"
]

for w in new_widgets:
    checks[f"widget_{w}"] = f"self.{w}" in content

# 3. WorkflowStack has 3 panes
checks["workflowStack_is_stacked"] = "self.workflowStack = QStackedWidget()" in content
addwidget_count = len(re.findall(r"self\.workflowStack\.addWidget", content))
checks["workflowStack_3_panes"] = addwidget_count == 3

# 4. Mascot layout
checks["mascotHost_fixedHeight_140"] = "self.mascotHost.setFixedHeight(140)" in content
checks["mascotHost_has_2_stretches"] = "mhLay.addStretch(1)" in content and content.count("mhLay.addStretch") == 2

# 5. Hidden legacy
checks["tabWidget_hidden"] = "self.tabWidget.setVisible(False)" in content
checks["themeBtn_hidden"] = "self.themeBtn.setVisible(False)" in content
checks["openFolderBtn_hidden"] = "self.openFolderBtn.setVisible(False)" in content

# 6. Menu items
checks["menuItems_dict"] = 'self.menuItems = {}' in content
checks["menuItems_populated"] = 'for name in ("File", "Edit", "View", "Help"):' in content

# 7. Boost slider connection
checks["boostSlider_connected"] = "self.boostSlider.valueChanged.connect" in content

# 8. Translate dropdowns
checks["transSrcDropdown"] = "self.transSrcDropdown = QComboBox()" in content
checks["transTgtDropdown"] = "self.transTgtDropdown = QComboBox()" in content

# 9. Window size
checks["window_900x640"] = "MainWindow.resize(900, 640)" in content
checks["window_min_800x580"] = "MainWindow.setMinimumSize(QSize(800, 580))" in content

# 10. Legacy backward compat (sample)
legacy_sample = [
    "startButton", "progressBar", "statusLabel", "etaLabel",
    "filePathLabel", "source_language_dropdown", "target_language_dropdown",
    "target_engine", "boostSlider", "boostLabel", "bearerTokenEdit", "getTokenBtn"
]

for w in legacy_sample:
    checks[f"legacy_{w}"] = f"self.{w}" in content

# Print results
print("\n" + "="*70)
print("SPEC COMPLIANCE CHECK")
print("="*70)

passed = sum(1 for v in checks.values() if v)
failed = sum(1 for v in checks.values() if not v)

print(f"\nResults: {passed}/{len(checks)} checks passed")

if failed > 0:
    print(f"\nFAILED CHECKS:")
    for k, v in checks.items():
        if not v:
            print(f"  ✗ {k}")

# Critical summary
critical = [
    checks.get("FramelessWindowHint", False),
    checks.get("workflowStack_3_panes", False),
    checks.get("mascotHost_fixedHeight_140", False),
    checks.get("mascotHost_has_2_stretches", False),
    checks.get("boostSlider_connected", False),
    checks.get("transSrcDropdown", False),
    checks.get("transTgtDropdown", False),
]

print(f"\n{'='*70}")
print(f"CRITICAL ITEMS: {sum(critical)}/7 passed")
print(f"{'='*70}")
if all(critical):
    print("✓ ALL CRITICAL REQUIREMENTS MET")
else:
    print("✗ CRITICAL ISSUES FOUND")
    
print("\nDETAILS:")
print(f"  FramelessWindowHint: {'✓' if checks['FramelessWindowHint'] else '✗'}")
print(f"  workflowStack (3 panes): {'✓' if checks['workflowStack_3_panes'] else '✗'}")
print(f"  mascotHost fixedHeight=140: {'✓' if checks['mascotHost_fixedHeight_140'] else '✗'}")
print(f"  mascotHost layout (2 stretches): {'✓' if checks['mascotHost_has_2_stretches'] else '✗'}")
print(f"  boostSlider.valueChanged wired: {'✓' if checks['boostSlider_connected'] else '✗'}")
print(f"  transSrcDropdown exists: {'✓' if checks['transSrcDropdown'] else '✗'}")
print(f"  transTgtDropdown exists: {'✓' if checks['transTgtDropdown'] else '✗'}")

