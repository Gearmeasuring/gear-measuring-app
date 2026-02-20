# 齿轮分析软件 - 重构版 (v2.0.0)

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.7%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

## 项目简介

齿轮分析软件重构版是将原有的19,377行单文件程序完全重构为现代化、模块化架构的专业软件。该项目保留了所有原有功能，并进行了大量改进和优化，使代码更清晰、更易维护。

## 🎯 核心功能

### ✅ 完整功能集
- **MKA文件解析** - 完整支持所有数据格式
- **ISO1328分析** - 标准公差计算与偏差分析
- **波纹度分析** - W值/RMS计算与评估
- **周节分析** - fp/Fp/Fr完整计算
- **Ripple阶次分析** - FFT频域分析
- **专业报告** - HTML + PDF（克林贝格标准）
- **数据导出** - CSV格式导出
- **现代化UI** - PyQt5界面

### 📊 专业报告生成
- 克林贝格Professional PDF报告 (20页标准结构)
- HTML交互式报告
- CSV数据导出

## 🏗️ 技术架构

### 模块化设计
```
gear_analysis_refactored/
├── analysis/              # 数据分析模块
├── config/                # 配置文件
├── models/                # 数据模型
├── reports/               # 报告生成器
├── threads/               # 多线程处理
├── ui/                    # 用户界面
└── utils/                 # 工具函数
```

### 技术栈
- **Python 3.7+**
- **PyQt5** - 现代化图形界面
- **NumPy & SciPy** - 科学计算
- **Matplotlib** - 图表绘制
- **ReportLab** - PDF报告生成

## 🚀 快速开始

### 系统要求
- Python 3.7+
- Windows 7/8/10/11, macOS 10.12+, Linux

### 安装步骤
1. 确保已安装Python 3.7+
2. 下载项目文件
3. 安装依赖包:
   ```bash
   pip install -r requirements.txt
   ```

### 启动程序
- **Windows用户**: 双击`启动程序.bat`
- **其他系统**: 运行`python main.py`

## 📖 使用说明

### 基本操作流程
1. 文件 → 打开MKA文件
2. 查看 → 基本信息/测量数据
3. 分析 → ISO1328偏差分析
4. 曲线 → 查看图表
5. 报表 → 生成报告

### 详细文档
- [用户使用手册](用户使用手册.md) - 完整的用户操作指南
- [功能测试报告](✅功能测试报告.md) - 所有功能测试结果
- [迁移完成总结](✨迁移完成总结.md) - 重构过程总结

## 📦 发布版本

### Python包
- 源码包: `dist/gear-analysis-refactored-2.0.0.tar.gz`
- Wheel包: `dist/gear_analysis_refactored-2.0.0-py3-none-any.whl`

### 便携式版本
- [齿轮分析软件_便携版](齿轮分析软件_便携版/) - 包含所有源代码和依赖说明

## 📈 重构成果

### 性能提升
| 指标 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| 代码行数 | 19,377行 | ~3,000行 | 减少84.5% |
| 模块数量 | 1个 | 8个 | 增加700% |
| 文档完整性 | 基本无文档 | 完整文档 | 显著改善 |

### 功能增强
- ✅ 更好的错误处理机制
- ✅ 完整的类型提示
- ✅ 详细的文档字符串
- ✅ 一致的代码风格
- ✅ 完善的日志记录

## 🧪 测试验证

运行完整功能测试:
```bash
python test_all_features.py
```

## 📄 重要文档

- [发布说明](RELEASE_NOTES.md) - 版本更新详情
- [版本总结](VERSION_SUMMARY.md) - 重构项目总结
- [重构总结](REFACTORING_SUMMARY.md) - 技术重构细节
- [迁移完成总结](🎉最终迁移完成报告.md) - 完整迁移报告

## 🤝 技术支持

### 获取帮助
如果在使用过程中遇到任何问题，请参考以下资源：
- 查看[用户使用手册.md](用户使用手册.md)
- 运行[test_all_features.py](test_all_features.py)检测功能
- 查看日志文件`gear_analysis.log`

### 反馈建议
我们欢迎您的反馈和建议：
- 邮箱: support@gearanalysis.com
- GitHub: 提交Issue或Pull Request

## 📄 许可证

本项目采用MIT许可证，详情请见[LICENSE](LICENSE)文件。

---
**齿轮分析团队**  
*让齿轮分析变得更简单*
