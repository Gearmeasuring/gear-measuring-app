# 计算结果与Klingelnberg报告差异分析

## 数据对比

| 曲线组 | Klingelnberg 87阶幅值 | 我们的87阶幅值 | 比率 |
|--------|----------------------|---------------|------|
| Profile left | 0.14 μm | 1.25 μm | **8.9x** |
| Profile right | 0.15 μm | 0.93 μm | **6.2x** |
| Helix left | 0.12 μm | 0.18 μm | **1.5x** |
| Helix right | 0.09 μm | 0.16 μm | **1.8x** |

## 可能的原因

### 1. 低通滤波器 (最可能的原因)
Klingelnberg报告中提到 **"Low-pass filter RC 100000:1"**

这意味着Klingelnberg在分析前应用了低通滤波器，可能：
- 滤除了高频成分
- 只保留了低频的波纹度信息
- 导致幅值显著降低

### 2. 数据预处理差异
- **鼓形剔除**：Klingelnberg可能使用了不同的鼓形计算方法
- **斜率剔除**：可能使用了不同的斜率补偿方法
- **异常值处理**：可能使用了不同的异常值替换策略

### 3. 频谱分析方法差异
- **FFT vs 最小二乘法**：Klingelnberg可能使用FFT而不是迭代最小二乘法
- **窗口函数**：可能使用了汉宁窗、汉明窗等窗口函数
- **频谱分辨率**：可能使用了不同的频率分辨率

### 4. 高阶定义差异
- Klingelnberg可能只考虑特定的阶次（如ZE的整数倍）
- 可能排除了某些"伪高阶"成分

### 5. 闭合曲线构建差异
- ep和el的使用方式可能不同
- 角度映射公式可能有差异
- 重叠区域处理方式可能不同

## 建议的修正方向

### 1. 添加低通滤波
```python
from scipy.signal import butter, filtfilt

def lowpass_filter(data, cutoff_order, teeth_count, sampling_rate):
    """应用低通滤波器"""
    nyquist = sampling_rate / 2
    cutoff_freq = cutoff_order * teeth_count / 360  # 转换为频率
    normalized_cutoff = cutoff_freq / nyquist
    b, a = butter(4, normalized_cutoff, btype='low')
    return filtfilt(b, a, data)
```

### 2. 使用FFT代替最小二乘法
```python
def fft_spectrum(angles, values, teeth_count):
    """使用FFT计算频谱"""
    # 插值到均匀角度
    num_pts = 4096  # 2的幂次
    interp_angles = np.linspace(0, 360, num_pts, endpoint=False)
    interp_values = np.interp(interp_angles, angles, values, period=360)
    
    # 加窗
    window = np.hanning(num_pts)
    windowed = interp_values * window
    
    # FFT
    fft_result = np.fft.fft(windowed)
    amplitudes = 2 * np.abs(fft_result) / num_pts
    
    return amplitudes[:num_pts//2]
```

### 3. 检查数据缩放
可能需要将数据除以一个缩放因子（如10或100）

## 下一步行动

1. 实现低通滤波器，参考Klingelnberg的RC滤波器参数
2. 尝试使用FFT方法计算频谱
3. 检查MKA文件解析时是否有缩放因子
4. 对比鼓形和斜率剔除的方法
