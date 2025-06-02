"""
MedScript Pro - Chart Components
This file contains chart components for analytics and data visualization.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from config.settings import CHART_CONFIG, ANALYTICS_CONFIG
from utils.formatters import format_date_display, format_currency, format_percentage

class BaseChart:
    """Base class for all chart components"""
    
    def __init__(self, title: str = "", subtitle: str = "", 
                 height: int = None, colors: List[str] = None):
        self.title = title
        self.subtitle = subtitle
        self.height = height or CHART_CONFIG['HEIGHT']
        self.colors = colors or ANALYTICS_CONFIG['CHART_COLORS']
        self.config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
        }
    
    def _apply_theme(self, fig):
        """Apply consistent theming to charts"""
        fig.update_layout(
            title={
                'text': self.title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'family': CHART_CONFIG['FONTS']['FAMILY']}
            },
            font={'family': CHART_CONFIG['FONTS']['FAMILY'], 'size': CHART_CONFIG['FONTS']['SIZE']},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=self.height,
            margin={'l': 50, 'r': 50, 't': 80, 'b': 50}
        )
        
        # Update grid
        fig.update_xaxes(gridcolor='rgba(128,128,128,0.2)', showline=True, linecolor='rgba(128,128,128,0.3)')
        fig.update_yaxes(gridcolor='rgba(128,128,128,0.2)', showline=True, linecolor='rgba(128,128,128,0.3)')
        
        return fig
    
    def render(self):
        """Render the chart"""
        raise NotImplementedError("Subclasses must implement render method")

class TimeSeriesChart(BaseChart):
    """Time series chart for tracking metrics over time"""
    
    def __init__(self, data: List[Dict[str, Any]], x_field: str, y_field: str,
                 date_format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.y_field = y_field
        self.date_format = date_format
    
    def render(self):
        """Render time series chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Convert date column
            df[self.x_field] = pd.to_datetime(df[self.x_field])
            df = df.sort_values(self.x_field)
            
            # Create chart
            fig = px.line(
                df, 
                x=self.x_field, 
                y=self.y_field,
                title=self.title,
                color_discrete_sequence=self.colors
            )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Customize line
            fig.update_traces(
                line={'width': 3},
                mode='lines+markers',
                marker={'size': 6},
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering time series chart: {str(e)}")

class BarChart(BaseChart):
    """Bar chart for categorical data"""
    
    def __init__(self, data: List[Dict[str, Any]], x_field: str, y_field: str,
                 orientation: str = 'v', **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.y_field = y_field
        self.orientation = orientation
    
    def render(self):
        """Render bar chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Sort by value
            df = df.sort_values(self.y_field, ascending=False)
            
            # Create chart
            if self.orientation == 'h':
                fig = px.bar(
                    df, 
                    x=self.y_field, 
                    y=self.x_field,
                    orientation='h',
                    title=self.title,
                    color_discrete_sequence=self.colors
                )
            else:
                fig = px.bar(
                    df, 
                    x=self.x_field, 
                    y=self.y_field,
                    title=self.title,
                    color_discrete_sequence=self.colors
                )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Customize bars
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>' if self.orientation == 'v' 
                else '<b>%{y}</b><br>%{x}<extra></extra>'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering bar chart: {str(e)}")

class PieChart(BaseChart):
    """Pie chart for distribution data"""
    
    def __init__(self, data: List[Dict[str, Any]], labels_field: str, values_field: str,
                 show_percentages: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.labels_field = labels_field
        self.values_field = values_field
        self.show_percentages = show_percentages
    
    def render(self):
        """Render pie chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Filter out zero values
            df = df[df[self.values_field] > 0]
            
            if df.empty:
                st.info("No data with positive values found")
                return
            
            # Create chart
            fig = px.pie(
                df, 
                names=self.labels_field, 
                values=self.values_field,
                title=self.title,
                color_discrete_sequence=self.colors
            )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Customize pie
            textinfo = 'label+percent' if self.show_percentages else 'label+value'
            fig.update_traces(
                textinfo=textinfo,
                textposition='inside',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering pie chart: {str(e)}")

class DonutChart(BaseChart):
    """Donut chart for distribution data with center metric"""
    
    def __init__(self, data: List[Dict[str, Any]], labels_field: str, values_field: str,
                 center_metric: Dict[str, Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.labels_field = labels_field
        self.values_field = values_field
        self.center_metric = center_metric or {}
    
    def render(self):
        """Render donut chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Filter out zero values
            df = df[df[self.values_field] > 0]
            
            if df.empty:
                st.info("No data with positive values found")
                return
            
            # Create donut chart
            fig = go.Figure(data=[go.Pie(
                labels=df[self.labels_field],
                values=df[self.values_field],
                hole=0.4,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                marker_colors=self.colors[:len(df)]
            )])
            
            # Add center annotation
            if self.center_metric:
                fig.add_annotation(
                    text=f"<b>{self.center_metric.get('value', '')}</b><br>{self.center_metric.get('label', '')}",
                    x=0.5, y=0.5,
                    font_size=16,
                    showarrow=False
                )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering donut chart: {str(e)}")

class AreaChart(BaseChart):
    """Area chart for cumulative data"""
    
    def __init__(self, data: List[Dict[str, Any]], x_field: str, y_field: str,
                 fill_color: str = None, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.y_field = y_field
        self.fill_color = fill_color or self.colors[0]
    
    def render(self):
        """Render area chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Convert date column
            df[self.x_field] = pd.to_datetime(df[self.x_field])
            df = df.sort_values(self.x_field)
            
            # Create chart
            fig = px.area(
                df, 
                x=self.x_field, 
                y=self.y_field,
                title=self.title,
                color_discrete_sequence=[self.fill_color]
            )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Customize area
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering area chart: {str(e)}")

class MultiSeriesChart(BaseChart):
    """Multi-series chart for comparing multiple metrics"""
    
    def __init__(self, data: List[Dict[str, Any]], x_field: str, series_configs: List[Dict[str, str]],
                 chart_type: str = 'line', **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.series_configs = series_configs  # [{'field': 'y1', 'name': 'Series 1'}, ...]
        self.chart_type = chart_type
    
    def render(self):
        """Render multi-series chart"""
        if not self.data or not self.series_configs:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Convert date column if needed
            if df[self.x_field].dtype == 'object':
                try:
                    df[self.x_field] = pd.to_datetime(df[self.x_field])
                except:
                    pass
            
            df = df.sort_values(self.x_field)
            
            # Create figure
            fig = go.Figure()
            
            # Add series
            for i, series_config in enumerate(self.series_configs):
                y_field = series_config['field']
                series_name = series_config.get('name', y_field)
                color = self.colors[i % len(self.colors)]
                
                if self.chart_type == 'line':
                    fig.add_trace(go.Scatter(
                        x=df[self.x_field],
                        y=df[y_field],
                        mode='lines+markers',
                        name=series_name,
                        line={'color': color, 'width': 3},
                        marker={'size': 6},
                        hovertemplate=f'<b>{series_name}</b><br>%{{x}}<br>%{{y}}<extra></extra>'
                    ))
                elif self.chart_type == 'bar':
                    fig.add_trace(go.Bar(
                        x=df[self.x_field],
                        y=df[y_field],
                        name=series_name,
                        marker_color=color,
                        hovertemplate=f'<b>{series_name}</b><br>%{{x}}<br>%{{y}}<extra></extra>'
                    ))
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering multi-series chart: {str(e)}")

class HeatmapChart(BaseChart):
    """Heatmap chart for correlation or intensity data"""
    
    def __init__(self, data: List[Dict[str, Any]], x_field: str, y_field: str, z_field: str,
                 colorscale: str = 'Blues', **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.y_field = y_field
        self.z_field = z_field
        self.colorscale = colorscale
    
    def render(self):
        """Render heatmap chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.data)
            
            # Pivot for heatmap
            pivot_df = df.pivot(index=self.y_field, columns=self.x_field, values=self.z_field)
            
            # Create heatmap
            fig = px.imshow(
                pivot_df,
                title=self.title,
                color_continuous_scale=self.colorscale,
                aspect='auto'
            )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering heatmap chart: {str(e)}")

class GaugeChart(BaseChart):
    """Gauge chart for KPI visualization"""
    
    def __init__(self, value: float, max_value: float, title: str = "",
                 thresholds: Dict[str, float] = None, **kwargs):
        super().__init__(title=title, **kwargs)
        self.value = value
        self.max_value = max_value
        self.thresholds = thresholds or {'red': 0.3, 'yellow': 0.7, 'green': 1.0}
    
    def render(self):
        """Render gauge chart"""
        try:
            # Determine color based on thresholds
            percentage = self.value / self.max_value
            if percentage <= self.thresholds.get('red', 0.3):
                color = 'red'
            elif percentage <= self.thresholds.get('yellow', 0.7):
                color = 'yellow'
            else:
                color = 'green'
            
            # Create gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=self.value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': self.title},
                delta={'reference': self.max_value * 0.8},
                gauge={
                    'axis': {'range': [None, self.max_value]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, self.max_value * 0.3], 'color': "lightgray"},
                        {'range': [self.max_value * 0.3, self.max_value * 0.7], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': self.max_value * 0.9
                    }
                }
            ))
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering gauge chart: {str(e)}")

class HistogramChart(BaseChart):
    """Histogram chart for distribution analysis"""
    
    def __init__(self, data: List[float], bins: int = 20, **kwargs):
        super().__init__(**kwargs)
        self.data = data
        self.bins = bins
    
    def render(self):
        """Render histogram chart"""
        if not self.data:
            st.info("No data available for chart")
            return
        
        try:
            # Create histogram
            fig = px.histogram(
                x=self.data,
                nbins=self.bins,
                title=self.title,
                color_discrete_sequence=self.colors
            )
            
            # Apply theme
            fig = self._apply_theme(fig)
            
            # Customize histogram
            fig.update_traces(
                hovertemplate='<b>Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
            )
            
            # Display chart
            st.plotly_chart(fig, use_container_width=True, config=self.config)
        
        except Exception as e:
            st.error(f"Error rendering histogram chart: {str(e)}")

# Specialized medical charts
class PrescriptionTrendChart(TimeSeriesChart):
    """Specialized chart for prescription trends"""
    
    def __init__(self, prescription_data: List[Dict[str, Any]], **kwargs):
        kwargs.setdefault('title', 'Prescription Trends Over Time')
        kwargs.setdefault('height', 400)
        super().__init__(
            data=prescription_data,
            x_field='date',
            y_field='count',
            **kwargs
        )

class PatientDemographicsChart(PieChart):
    """Specialized chart for patient demographics"""
    
    def __init__(self, demographic_data: List[Dict[str, Any]], demographic_type: str, **kwargs):
        kwargs.setdefault('title', f'Patient Distribution by {demographic_type.title()}')
        kwargs.setdefault('height', 400)
        super().__init__(
            data=demographic_data,
            labels_field=demographic_type,
            values_field='count',
            **kwargs
        )

class MedicationUsageChart(BarChart):
    """Specialized chart for medication usage"""
    
    def __init__(self, medication_data: List[Dict[str, Any]], **kwargs):
        kwargs.setdefault('title', 'Most Prescribed Medications')
        kwargs.setdefault('orientation', 'h')
        kwargs.setdefault('height', 500)
        super().__init__(
            data=medication_data,
            x_field='name',
            y_field='count',
            **kwargs
        )

class AnalyticsDashboard:
    """Complete analytics dashboard with multiple charts"""
    
    def __init__(self, analytics_data: Dict[str, Any]):
        self.analytics_data = analytics_data
    
    def render_prescription_analytics(self):
        """Render prescription analytics section"""
        st.subheader("📊 Prescription Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Prescription trends
            timeline_data = self.analytics_data.get('prescriptions_timeline', [])
            if timeline_data:
                chart = PrescriptionTrendChart(timeline_data)
                chart.render()
        
        with col2:
            # Status distribution
            status_data = self.analytics_data.get('status_distribution', [])
            if status_data:
                chart = DonutChart(
                    data=status_data,
                    labels_field='status',
                    values_field='count',
                    title='Prescription Status Distribution',
                    center_metric={'value': sum(item['count'] for item in status_data), 'label': 'Total'}
                )
                chart.render()
        
        # Top medications
        medication_data = self.analytics_data.get('top_medications', [])
        if medication_data:
            chart = MedicationUsageChart(medication_data)
            chart.render()
    
    def render_patient_analytics(self):
        """Render patient analytics section"""
        st.subheader("👥 Patient Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age distribution
            age_data = self.analytics_data.get('age_distribution', [])
            if age_data:
                chart = PatientDemographicsChart(age_data, 'age_group')
                chart.render()
        
        with col2:
            # Gender distribution
            gender_data = self.analytics_data.get('gender_distribution', [])
            if gender_data:
                chart = PatientDemographicsChart(gender_data, 'gender')
                chart.render()
        
        # Patient registrations over time
        registration_data = self.analytics_data.get('patient_registrations', [])
        if registration_data:
            chart = TimeSeriesChart(
                data=registration_data,
                x_field='date',
                y_field='count',
                title='Patient Registrations Over Time'
            )
            chart.render()

# Utility functions for chart components
def create_chart_from_config(chart_config: Dict[str, Any], data: List[Dict[str, Any]]):
    """Create chart from configuration"""
    chart_type = chart_config.get('type', 'line')
    
    if chart_type == 'line':
        return TimeSeriesChart(
            data=data,
            x_field=chart_config['x_field'],
            y_field=chart_config['y_field'],
            title=chart_config.get('title', '')
        )
    elif chart_type == 'bar':
        return BarChart(
            data=data,
            x_field=chart_config['x_field'],
            y_field=chart_config['y_field'],
            title=chart_config.get('title', ''),
            orientation=chart_config.get('orientation', 'v')
        )
    elif chart_type == 'pie':
        return PieChart(
            data=data,
            labels_field=chart_config['x_field'],
            values_field=chart_config['y_field'],
            title=chart_config.get('title', '')
        )
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

def render_chart_grid(charts: List[BaseChart], columns: int = 2):
    """Render multiple charts in a grid"""
    chart_cols = st.columns(columns)
    
    for i, chart in enumerate(charts):
        with chart_cols[i % columns]:
            chart.render()

def export_chart_data(chart_data: List[Dict[str, Any]], filename: str = "chart_data.csv"):
    """Export chart data as CSV"""
    if not chart_data:
        st.warning("No data to export")
        return
    
    try:
        df = pd.DataFrame(chart_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📄 Download Chart Data",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error exporting chart data: {str(e)}")

def create_medical_kpi_dashboard(metrics: Dict[str, Any]):
    """Create medical KPI dashboard with gauges and metrics"""
    st.subheader("🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'patient_satisfaction' in metrics:
            chart = GaugeChart(
                value=metrics['patient_satisfaction'],
                max_value=100,
                title="Patient Satisfaction (%)"
            )
            chart.render()
    
    with col2:
        if 'prescription_accuracy' in metrics:
            chart = GaugeChart(
                value=metrics['prescription_accuracy'],
                max_value=100,
                title="Prescription Accuracy (%)"
            )
            chart.render()
    
    with col3:
        if 'consultation_efficiency' in metrics:
            chart = GaugeChart(
                value=metrics['consultation_efficiency'],
                max_value=100,
                title="Consultation Efficiency (%)"
            )
            chart.render()
    
    with col4:
        if 'system_uptime' in metrics:
            chart = GaugeChart(
                value=metrics['system_uptime'],
                max_value=100,
                title="System Uptime (%)"
            )
            chart.render()