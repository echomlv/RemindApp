#!/usr/bin/env python3
"""
生成 RemindApp.icns 图标
设计：蓝紫渐变圆角背景 + 金色铃铛 emoji
"""

import os
import shutil
import subprocess

import AppKit
import Foundation


def _draw_icon(size: int) -> AppKit.NSImage:
    """在内存中绘制 size×size 的图标"""
    image = AppKit.NSImage.alloc().initWithSize_(AppKit.NSMakeSize(size, size))
    image.lockFocus()

    ctx = AppKit.NSGraphicsContext.currentContext()
    ctx.setImageInterpolation_(AppKit.NSImageInterpolationHigh)

    bounds = AppKit.NSMakeRect(0, 0, size, size)

    # ── 1. 圆角裁剪（macOS 图标圆角约为 22.5% 的边长）──────────────────
    radius = size * 0.225
    clip_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
        bounds, radius, radius
    )
    clip_path.addClip()

    # ── 2. 渐变背景：左下深蓝 → 右上粉紫 ──────────────────────────────
    color_start = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(
        0.255, 0.341, 0.820, 1.0   # #4157D1
    )
    color_end = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(
        0.784, 0.314, 0.753, 1.0   # #C850C0
    )
    gradient = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(
        color_start, color_end
    )
    gradient.drawInRect_angle_(bounds, 135)

    # ── 3. 铃铛 emoji，居中略上 ─────────────────────────────────────────
    font_size = size * 0.55
    font = AppKit.NSFont.fontWithName_size_("Apple Color Emoji", font_size)
    if font is None:
        # 回退到系统字体（极少情况）
        font = AppKit.NSFont.systemFontOfSize_(font_size)

    attrs = {
        AppKit.NSFontAttributeName: font,
    }
    bell = Foundation.NSString.stringWithString_("🔔")
    text_size = bell.sizeWithAttributes_(attrs)

    draw_x = (size - text_size.width) / 2
    draw_y = (size - text_size.height) / 2 + size * 0.02  # 视觉重心略上移

    bell.drawAtPoint_withAttributes_(
        AppKit.NSMakePoint(draw_x, draw_y),
        attrs,
    )

    image.unlockFocus()
    return image


def _save_png(image: AppKit.NSImage, path: str, size: int):
    """将 NSImage 缩放并保存为 PNG"""
    scaled = AppKit.NSImage.alloc().initWithSize_(AppKit.NSMakeSize(size, size))
    scaled.lockFocus()
    image.drawInRect_fromRect_operation_fraction_(
        AppKit.NSMakeRect(0, 0, size, size),
        AppKit.NSMakeRect(0, 0, 0, 0),  # NSZeroRect → 使用整张图
        2,                               # NSCompositingOperationSourceOver
        1.0,
    )
    scaled.unlockFocus()

    tiff = scaled.TIFFRepresentation()
    rep = AppKit.NSBitmapImageRep.imageRepWithData_(tiff)
    png = rep.representationUsingType_properties_(
        AppKit.NSBitmapImageFileTypePNG,
        {},
    )
    png.writeToFile_atomically_(path, True)


def create_icns(output: str = "RemindApp.icns"):
    iconset = "RemindApp.iconset"
    os.makedirs(iconset, exist_ok=True)

    print("▶ 绘制图标（1024×1024）...")
    base = _draw_icon(1024)

    # iconutil 要求的所有尺寸
    specs = [
        (16,   "icon_16x16.png"),
        (32,   "icon_16x16@2x.png"),
        (32,   "icon_32x32.png"),
        (64,   "icon_32x32@2x.png"),
        (128,  "icon_128x128.png"),
        (256,  "icon_128x128@2x.png"),
        (256,  "icon_256x256.png"),
        (512,  "icon_256x256@2x.png"),
        (512,  "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    for px, filename in specs:
        dst = os.path.join(iconset, filename)
        _save_png(base, dst, px)
        print(f"  ✓ {filename}")

    print("▶ 合成 .icns...")
    result = subprocess.run(
        ["iconutil", "-c", "icns", iconset, "-o", output],
        capture_output=True,
        text=True,
    )
    shutil.rmtree(iconset)

    if result.returncode != 0:
        raise RuntimeError(f"iconutil 失败: {result.stderr}")

    size_kb = os.path.getsize(output) // 1024
    print(f"✅ 图标生成完成: {output}  ({size_kb} KB)")


if __name__ == "__main__":
    create_icns()
