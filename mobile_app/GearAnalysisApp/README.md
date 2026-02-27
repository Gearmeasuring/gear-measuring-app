# 齿轮测量分析 - Android 应用

## 项目概述

这是一个基于 WebView 的 Android 应用，封装了 Streamlit 网页应用，提供齿轮测量分析功能。

## 技术方案

**方案A：WebView 封装**
- 使用 Android WebView 加载 Streamlit Cloud 应用
- 支持文件上传（MKA 格式）
- 支持 PDF 报告下载
- 响应式设计，适配手机屏幕

## 功能特性

### 核心功能
1. **AI 综合分析报告** - 默认页面，综合评估齿轮质量
2. **专业报告** - 齿形/齿向分析图表和数据表
3. **三截面扭曲数据** - 齿号1a/1b/1c的偏差报表
4. **周节详细报表** - 周节偏差 fp/Fp/Fr 分析
5. **单齿分析** - 单个齿的偏差曲线
6. **合并曲线** - 0-360°合并曲线分析
7. **频谱分析** - 阶次振幅相位分析

### 移动端优化
- 支持文件上传（MKA格式）
- 支持 PDF 报告下载
- 响应式布局，适配各种屏幕尺寸
- 加载进度条显示
- 返回键支持页面后退

## 构建说明

### 环境要求
- Android Studio 4.0+
- Android SDK 21+
- Gradle 6.0+

### 构建步骤

1. **打开项目**
   ```bash
   使用 Android Studio 打开 mobile_app/GearAnalysisApp/android 目录
   ```

2. **同步 Gradle**
   ```bash
   点击 "Sync Project with Gradle Files"
   ```

3. **构建 APK**
   ```bash
   Build -> Build Bundle(s) / APK(s) -> Build APK(s)
   ```

4. **安装测试**
   ```bash
   将生成的 APK 安装到 Android 设备上进行测试
   ```

## 应用配置

### Streamlit 应用 URL
在 `MainActivity.java` 中修改：
```java
private static final String APP_URL = "https://gear-measuring-app.streamlit.app";
```

### 权限说明
应用需要以下权限：
- `INTERNET` - 访问网络
- `READ_EXTERNAL_STORAGE` - 读取文件
- `WRITE_EXTERNAL_STORAGE` - 保存文件
- `CAMERA` - 拍照（可选）

## 目录结构

```
mobile_app/
└── GearAnalysisApp/
    └── android/
        └── app/
            └── src/
                └── main/
                    ├── java/com/gearanalysis/
                    │   └── MainActivity.java    # 主Activity
                    ├── res/
                    │   ├── layout/
                    │   │   └── activity_main.xml    # 主布局
                    │   ├── values/
                    │   │   ├── strings.xml    # 字符串资源
                    │   │   └── colors.xml     # 颜色资源
                    │   └── xml/
                    │       └── file_paths.xml     # 文件路径配置
                    └── AndroidManifest.xml    # 应用配置
```

## 使用说明

1. **安装应用**
   - 下载 APK 文件
   - 在 Android 设备上安装
   - 授予必要的权限

2. **上传数据**
   - 打开应用
   - 点击"选择文件"按钮
   - 选择 MKA 格式的齿轮测量数据文件
   - 等待分析完成

3. **查看报告**
   - 默认显示 AI 综合分析报告
   - 在左侧导航栏切换不同功能
   - 可以下载 PDF 报告

## 注意事项

1. **网络要求**
   - 应用需要网络连接才能使用
   - 建议在 WiFi 环境下使用

2. **文件格式**
   - 仅支持 Klingelnberg MKA 格式
   - 文件大小建议不超过 50MB

3. **兼容性**
   - 支持 Android 5.0 (API 21) 及以上版本
   - 推荐使用 Android 8.0 及以上版本

## 技术支持

如有问题，请联系开发团队。

## 版本历史

### v1.0.0 (2024-02-27)
- 初始版本发布
- 基于 WebView 封装 Streamlit 应用
- 支持文件上传和报告下载
