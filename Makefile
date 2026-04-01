APP_NAME  = RemindApp
DIST_DIR  = dist
BUILD_DIR = build
APP_PATH  = $(DIST_DIR)/$(APP_NAME).app
DMG_PATH  = $(DIST_DIR)/$(APP_NAME).dmg

.PHONY: all app dmg clean run deps

## 默认：构建 .app 和 .dmg
all: dmg

## 仅安装打包依赖
deps:
	pip3 install py2app

## 生成 .icns 图标
icon:
	python3 create_icon.py

## 构建 .app 包
app: deps icon
	@echo "▶ 清理旧构建..."
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	@echo "▶ 打包 .app（py2app）..."
	python3 setup.py py2app
	@echo ""
	@echo "✅ .app 构建完成 →  $(APP_PATH)"
	@du -sh $(APP_PATH)

## 构建 .dmg（依赖 .app）
dmg: app
	@echo ""
	@echo "▶ 创建 .dmg..."
	@# 创建临时目录，放入 .app 和 /Applications 快捷方式
	$(eval TMPDIR := $(shell mktemp -d))
	cp -r "$(APP_PATH)" "$(TMPDIR)/"
	ln -s /Applications "$(TMPDIR)/Applications"
	@# 用 hdiutil 打包成压缩 DMG
	hdiutil create \
		-volname "$(APP_NAME)" \
		-srcfolder "$(TMPDIR)" \
		-ov \
		-format UDZO \
		-fs HFS+ \
		"$(DMG_PATH)"
	rm -rf "$(TMPDIR)"
	@echo ""
	@echo "✅ .dmg 构建完成 →  $(DMG_PATH)"
	@du -sh $(DMG_PATH)

## 清理所有构建产物
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "✅ 清理完成"

## 直接运行（开发模式，不打包）
run:
	python3 main.py
