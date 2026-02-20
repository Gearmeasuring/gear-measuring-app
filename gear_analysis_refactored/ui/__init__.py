"""UI模块"""
from .dialogs import ToleranceCalculatorDialog, RippleAnalysisDialog, AnalysisSettingsDialog, QualityGradeDialog, ProcessingStepsDialog
from .main_window import GearDataViewer
from .main_window import GearDataViewer as MainWindow  # 别名，便于导入
from .custom_canvas import CustomFigureCanvas
from .advanced_charts import WaterfallChartWidget, OrderSpectrumChartWidget, UndulationDistributionChartWidget
from .ripple_page import RippleAnalysisPage
from .pitch_page import PitchAnalysisPage

__all__ = [
    'GearDataViewer', 
    'MainWindow',
    'ToleranceCalculatorDialog',
    'RippleAnalysisDialog',
    'AnalysisSettingsDialog',
    'QualityGradeDialog',
    'ProcessingStepsDialog',
    'CustomFigureCanvas',
    'WaterfallChartWidget',
    'OrderSpectrumChartWidget',
    'UndulationDistributionChartWidget',
    'RippleAnalysisPage',
    'PitchAnalysisPage'
]

