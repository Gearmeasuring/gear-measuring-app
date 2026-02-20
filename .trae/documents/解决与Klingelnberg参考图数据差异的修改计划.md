## 修改计划

### 修改内容

1. **修改RC滤波器参数**

   * 文件：`klingelnberg_ripple_spectrum.py`

   * 位置：第4320行

   * 内容：`fc_multiplier: 10.0 → 1.0`

2. **使用ISO 1328高斯滤波器替代RC滤波器**

   * 文件：`klingelnberg_ripple_spectrum.py`

   * 位置：第4312-4320行

   * 内容：使用`_separate_errors_by_iso1328`方法

3. **阶次对齐到ZE倍数**

   * 文件：`klingelnberg_ripple_spectrum.py`

   * 位置：第4359-4361行

   * 内容：`order = ze_multiple * ze`

4. **测试验证修改效果**

   * 运行程序生成新图表

   * 对比Klingelnberg参考图

### 预期效果

* 阶次显示为1ZE, 2ZE, 3ZE...

* 幅值更接近参考图

* 符合ISO 1328标准

