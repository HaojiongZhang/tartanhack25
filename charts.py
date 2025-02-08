import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create a canvas and scrollbars
        self.canvas = tk.Canvas(self)
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        # Configure canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Add frame to canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

def create_chart_figure(data, chart_type='candlestick', timeframe='daily'):
    """Create a matplotlib figure with stock data"""
    fig = Figure(figsize=(10, 6), dpi=100)
    ax1 = fig.add_subplot(211)  # Price chart
    ax2 = fig.add_subplot(212)  # RSI chart

    # Get appropriate data based on timeframe
    if timeframe == 'daily':
        df = pd.DataFrame(data['daily']['hist'])
    elif timeframe == 'monthly':
        df = pd.DataFrame(data['monthly'])
    else:  # yearly
        df = pd.DataFrame(data['yearly'])

    df['Date'] = pd.to_datetime(df['Date'])

    # Plot price chart
    if chart_type == 'candlestick':
        for i in range(len(df)):
            color = 'g' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'r'

            # Plot price range line
            ax1.plot([df['Date'].iloc[i], df['Date'].iloc[i]], 
                   [df['Low'].iloc[i], df['High'].iloc[i]], 
                   color=color, linewidth=1)

            # Plot candlestick body
            body_bottom = min(df['Open'].iloc[i], df['Close'].iloc[i])
            body_top = max(df['Open'].iloc[i], df['Close'].iloc[i])
            ax1.bar(df['Date'].iloc[i], body_top - body_bottom, 
                  bottom=body_bottom, color=color, width=pd.Timedelta(days=0.8))

        # Add Moving Averages
        if len(df) >= 20:
            df['MA20'] = df['Close'].rolling(window=20).mean()
            ax1.plot(df['Date'], df['MA20'], label='20-day MA', color='blue', alpha=0.7)
        if len(df) >= 50:
            df['MA50'] = df['Close'].rolling(window=50).mean()
            ax1.plot(df['Date'], df['MA50'], label='50-day MA', color='orange', alpha=0.7)
    else:
        ax1.plot(df['Date'], df['Close'], label='Close Price', color='blue')

        # Add Moving Averages for line chart
        if len(df) >= 20:
            df['MA20'] = df['Close'].rolling(window=20).mean()
            ax1.plot(df['Date'], df['MA20'], label='20-day MA', color='green', alpha=0.7)
        if len(df) >= 50:
            df['MA50'] = df['Close'].rolling(window=50).mean()
            ax1.plot(df['Date'], df['MA50'], label='50-day MA', color='red', alpha=0.7)

    # Plot RSI
    ax2.plot(df['Date'], df['RSI'], color='purple', label='RSI')
    ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
    ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5)
    ax2.set_ylim(0, 100)

    # Customize the charts
    ax1.set_title(f'Stock Price History ({timeframe.capitalize()})')
    ax1.set_ylabel('Price ($)')
    ax1.grid(True)
    ax1.legend()

    ax2.set_title('Relative Strength Index (RSI)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('RSI')
    ax2.grid(True)
    ax2.legend()

    fig.autofmt_xdate()
    fig.tight_layout()

    return fig

def create_volume_figure(data, timeframe='daily'):
    """Create a matplotlib figure for volume data"""
    fig = Figure(figsize=(10, 3), dpi=100)
    ax = fig.add_subplot(111)

    # Get appropriate data based on timeframe
    if timeframe == 'daily':
        df = pd.DataFrame(data['daily']['hist'])
    elif timeframe == 'monthly':
        df = pd.DataFrame(data['monthly'])
    else:  # yearly
        df = pd.DataFrame(data['yearly'])

    df['Date'] = pd.to_datetime(df['Date'])

    # Plot volume bars
    ax.bar(df['Date'], df['Volume'], width=pd.Timedelta(days=0.8), 
           color='blue', alpha=0.5)

    # Customize the chart
    ax.set_title(f'Trading Volume ({timeframe.capitalize()})')
    ax.set_xlabel('Date')
    ax.set_ylabel('Volume')
    ax.grid(True)
    fig.autofmt_xdate()
    fig.tight_layout()

    return fig

def create_data_table(parent, data, timeframe='daily'):
    """Create a scrollable data table"""
    frame = ttk.Frame(parent)

    # Create Treeview
    tree = ttk.Treeview(frame, show='headings')

    # Get data based on timeframe
    if timeframe == 'daily':
        df = pd.DataFrame(data['daily']['hist'])
    elif timeframe == 'monthly':
        df = pd.DataFrame(data['monthly'])
    else:  # yearly
        df = pd.DataFrame(data['yearly'])

    # Define columns
    columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI']
    tree['columns'] = columns

    # Format columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    # Add data
    for _, row in df.iterrows():
        values = [
            row['Date'].strftime('%Y-%m-%d'),
            f"${row['Open']:.2f}",
            f"${row['High']:.2f}",
            f"${row['Low']:.2f}",
            f"${row['Close']:.2f}",
            f"{row['Volume']:,}",
            f"{row['RSI']:.1f}"
        ]
        tree.insert('', 'end', values=values)

    # Add scrollbars
    v_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Grid layout
    tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    return frame

def create_chart_tab(parent, data, timeframe, chart_type='candlestick'):
    """Create a tab with price and volume charts"""
    # Create main frame for the tab
    main_frame = ScrollableFrame(parent)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Configure weights for the scrollable frame
    main_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
    main_frame.scrollable_frame.grid_rowconfigure(0, weight=3)
    main_frame.scrollable_frame.grid_rowconfigure(1, weight=1)

    # Create view toggle frame
    toggle_frame = ttk.Frame(main_frame.scrollable_frame)
    toggle_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    view_var = tk.StringVar(value="chart")
    ttk.Radiobutton(toggle_frame, text="Chart View", variable=view_var, 
                   value="chart", command=lambda: toggle_view("chart")).pack(side="left", padx=5)
    ttk.Radiobutton(toggle_frame, text="Table View", variable=view_var,
                   value="table", command=lambda: toggle_view("table")).pack(side="left", padx=5)

    # Create frames for different views
    chart_frame = ttk.Frame(main_frame.scrollable_frame)
    table_frame = ttk.Frame(main_frame.scrollable_frame)

    def toggle_view(view_type):
        if view_type == "chart":
            table_frame.grid_remove()
            chart_frame.grid(row=1, column=0, sticky="nsew")
        else:
            chart_frame.grid_remove()
            table_frame.grid(row=1, column=0, sticky="nsew")

    # Set up chart view
    chart_frame.grid(row=1, column=0, sticky="nsew")

    # Create price chart
    price_frame = ttk.Frame(chart_frame)
    price_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    price_fig = create_chart_figure(data, chart_type, timeframe)
    price_canvas = FigureCanvasTkAgg(price_fig, master=price_frame)
    price_canvas.draw()

    # Add navigation toolbar for zoom/pan
    toolbar = NavigationToolbar2Tk(price_canvas, price_frame)
    toolbar.update()

    price_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Create volume chart
    volume_frame = ttk.Frame(chart_frame)
    volume_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    volume_fig = create_volume_figure(data, timeframe)
    volume_canvas = FigureCanvasTkAgg(volume_fig, master=volume_frame)
    volume_canvas.draw()

    # Add navigation toolbar for volume chart
    volume_toolbar = NavigationToolbar2Tk(volume_canvas, volume_frame)
    volume_toolbar.update()

    volume_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Set up table view
    table_frame.grid(row=1, column=0, sticky="nsew")
    table_frame.grid_remove()  # Initially hidden

    data_table = create_data_table(table_frame, data, timeframe)
    data_table.grid(row=0, column=0, sticky="nsew")

    return main_frame

def create_h1b_figures(filtered_df):
    """create h1b figures"""
    state_counts = filtered_df['Petitioner State'].value_counts()
    industry_counts = filtered_df['Industry (NAICS) Code'].value_counts()

    fig = Figure(figsize=(12, 6), dpi=100)
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    ax1.pie(state_counts, 
           labels=state_counts.index, 
           autopct='%1.1f%%',
           startangle=90,
           counterclock=False)
    ax1.set_title("H1B Distribution by State")

    ax2.pie(industry_counts,
           labels=industry_counts.index,
           autopct='%1.1f%%',
           startangle=90,
           counterclock=False)
    ax2.set_title("H1B Distribution by Industry")

    fig.tight_layout()
    return fig

def create_h1b_chart_tab(parent, filtered_df):
    """create h1b chart tab"""
    main_frame = ScrollableFrame(parent)
    main_frame.grid(row=0, column=0, sticky="nsew")

    fig = create_h1b_figures(filtered_df)
    canvas = FigureCanvasTkAgg(fig, master=main_frame.scrollable_frame)
    canvas.draw()
    
    toolbar = NavigationToolbar2Tk(canvas, main_frame.scrollable_frame)
    toolbar.grid(row=0, column=0, sticky="ew")
    
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    main_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
    main_frame.scrollable_frame.grid_rowconfigure(1, weight=1)
    
    return main_frame

def create_layoff_figures(filtered_df):
    """create_layoff_figures"""
    fig = Figure(figsize=(12, 12), dpi=100)
    fig.suptitle("Layoff Analysis Report", fontsize=14, y=0.97)
    
    ax1 = fig.add_subplot(211) 
    ax2 = fig.add_subplot(212) 

    try:       
        
        filtered_df['Number of Workers'] = pd.to_numeric(
            filtered_df['Number of Workers'], errors='coerce'
        ).fillna(0)
        
        state_data = filtered_df.groupby('State')['Number of Workers'].sum()
        print("STATE DATA:", state_data)
        state_data = state_data[state_data > 0].sort_values(ascending=False).head(10)
        
        if not state_data.empty:
            bars = ax1.bar(
                x=state_data.index,
                height=state_data.values,
                color='#1f77b4',
                alpha=0.7,
                edgecolor='navy'
            )
            
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{height:,.0f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=8)
            
            ax1.set_title('Top 10 States by Layoff Impact', pad=15)
            ax1.set_xlabel('State', labelpad=10)
            ax1.set_ylabel('Total Workers Affected', labelpad=10)
            ax1.tick_params(axis='x', rotation=45, labelsize=9)
            ax1.grid(axis='y', linestyle=':', alpha=0.7)
        else:
            ax1.text(0.5, 0.5, 'No Valid State Data', 
                    ha='center', va='center', fontsize=12)
            
    except Exception as e:
        ax1.clear()
        ax1.text(0.5, 0.5, f'State Chart Error: {str(e)}', 
                ha='center', va='center', color='red')

    try:
        # 数据标准化
        
        # 分类映射
        type_mapping = {
            'Closure': 'Permanent',
            'Layoff': 'Temporary',
            'Temporary Layoff': 'Temporary',
            'Plant Closure': 'Permanent'
        }
        
        filtered_df['Type'] = filtered_df['Closure / Layoff'].str.strip().str.title().map(type_mapping)
        filtered_df['Type'] = filtered_df['Type'].fillna('Other')
        
        # 聚合数据
        type_data = filtered_df.groupby('Type')['Number of Workers'].sum()
        type_data = type_data.sort_values(ascending=False)
        
        if not type_data.empty:
            # 绘制柱状图
            colors = ['#ff7f0e' if t == 'Permanent' else '#2ca02c' for t in type_data.index]
            bars = ax2.bar(
                x=type_data.index,
                height=type_data.values,
                color=colors,
                alpha=0.7,
                edgecolor='darkgreen'
            )
            
            # 添加数据标签
            for bar in bars:
                height = bar.get_height()
                ax2.annotate(f'{height:,.0f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=8)
            
            # 图表装饰
            ax2.set_title('Layoff Type Distribution', pad=15)
            ax2.set_xlabel('Layoff Type', labelpad=10)
            ax2.set_ylabel('Total Workers Affected', labelpad=10)
            ax2.tick_params(axis='x', rotation=0)
            ax2.grid(axis='y', linestyle=':', alpha=0.7)
        else:
            ax2.text(0.5, 0.5, 'No Type Data Available', 
                    ha='center', va='center', fontsize=12)
            
    except Exception as e:
        ax2.clear()
        ax2.text(0.5, 0.5, f'Type Chart Error: {str(e)}', 
                ha='center', va='center', color='red')

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def create_layoff_chart_tab(parent, filtered_df):
    """create layoff chart tab"""
    print("create layoff chart tab")
    main_frame = ScrollableFrame(parent)
    main_frame.grid(row=0, column=0, sticky="nsew")

    fig = create_layoff_figures(filtered_df)
    canvas = FigureCanvasTkAgg(fig, master=main_frame.scrollable_frame)
    canvas.draw()
    
    toolbar = NavigationToolbar2Tk(canvas, main_frame.scrollable_frame)
    toolbar.grid(row=0, column=0, sticky="ew")
    
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    main_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
    main_frame.scrollable_frame.grid_rowconfigure(1, weight=1)
    
    return main_frame