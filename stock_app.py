import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils import get_ticker, validate_symbol, fetch_stock_data, fetch_historical_data, export_stock_data
from styles import COLORS, FONTS, PADDING
from datetime import datetime
from charts import create_chart_tab, create_h1b_chart_tab, create_layoff_chart_tab, ScrollableFrame
from h1b import process_and_match_companies
from layoff import layoffs
from jobsearch import get_filtered_company_jobs
from dispute import get_info
from get_sec import get_summary


TK_SILENCE_DEPRECATION=1

class StockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ComPulse")
        self.root.geometry("1024x768")  # Increased window size for better chart visibility
        self.root.configure(bg=COLORS['bg'])

        self.setup_ui()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def setup_ui(self):
        """Setup the user interface"""
        # Create main frame with notebook
        main_frame = ttk.Frame(self.root, padding=PADDING['large'])
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Header
        header = ttk.Label(
            main_frame,
            text="ComPulse",
            font=FONTS['header']
        )
        header.grid(row=0, column=0, columnspan=2, pady=PADDING['medium'])

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=2, pady=PADDING['medium'])

        # Symbol input
        ttk.Label(
            input_frame,
            text="Enter Company Name:",
            font=FONTS['normal']
        ).grid(row=0, column=0, padx=PADDING['small'])

        self.symbol_entry = ttk.Entry(input_frame, width=20)
        self.symbol_entry.grid(row=0, column=1, padx=PADDING['small'])

        # Search button
        self.search_button = ttk.Button(
            input_frame,
            text="Get Info",
            command=self.fetch_all_data
        )
        self.search_button.grid(row=0, column=2, padx=PADDING['small'])

        # Chart type selection
        ttk.Label(
            input_frame,
            text="Chart Type:",
            font=FONTS['normal']
        ).grid(row=0, column=3, padx=PADDING['small'])

        self.chart_type = tk.StringVar(value='candlestick')
        chart_type_combo = ttk.Combobox(
            input_frame,
            textvariable=self.chart_type,
            values=['candlestick', 'line'],
            state='readonly',
            width=15
        )
        chart_type_combo.grid(row=0, column=4, padx=PADDING['small'])
        chart_type_combo.bind('<<ComboboxSelected>>', lambda e: self.update_charts())

        # Export button
        self.export_button = ttk.Button(
            input_frame,
            text="Export Data",
            command=self.export_data,
            state='disabled'
        )
        self.export_button.grid(row=0, column=5, padx=PADDING['small'])

        # Loading label
        self.loading_label = ttk.Label(
            main_frame,
            text="",
            font=FONTS['small']
        )
        self.loading_label.grid(row=2, column=0, columnspan=2)

        # Notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=PADDING['medium'])

        # Create tabs
        self.overview_frame = ttk.Frame(self.notebook)
        self.daily_charts_frame = ttk.Frame(self.notebook)
        self.monthly_charts_frame = ttk.Frame(self.notebook)
        self.h1b_frame = ttk.Frame(self.notebook)
        self.layoff_frame = ttk.Frame(self.notebook)
        self.jobs_frame = ttk.Frame(self.notebook)
        self.dispute_frame = ttk.Frame(self.notebook)
        self.sec_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.overview_frame, text="Overview")
        self.notebook.add(self.daily_charts_frame, text="Daily Charts")
        self.notebook.add(self.monthly_charts_frame, text="Monthly Charts")
        self.notebook.add(self.h1b_frame, text="H1B Info")
        self.notebook.add(self.layoff_frame, text="Layoff Info")
        self.notebook.add(self.jobs_frame, text="Job Listings")
        self.notebook.add(self.dispute_frame, text="Legal Disputes") 
        self.notebook.add(self.sec_frame, text="10K Summary")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        self.h1b_frame.grid_rowconfigure(0, weight=1)
        self.h1b_frame.grid_columnconfigure(0, weight=1)
        self.layoff_frame.grid_rowconfigure(0, weight=1)
        self.layoff_frame.grid_columnconfigure(0, weight=1)
        self.jobs_frame.grid_rowconfigure(0, weight=1)
        self.jobs_frame.grid_columnconfigure(0, weight=1)
        self.dispute_frame.grid_rowconfigure(0, weight=1)
        self.dispute_frame.grid_columnconfigure(0, weight=1)
        self.sec_frame.grid_rowconfigure(0, weight=1)
        self.sec_frame.grid_columnconfigure(0, weight=1)

        # Configure chart frames
        for frame in [self.daily_charts_frame, self.monthly_charts_frame]:
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

        # Bind Enter key to fetch_data
        self.symbol_entry.bind('<Return>', lambda event: self.fetch_all_data())

        # Store historical data for chart updates
        self.current_hist_data = None
        self.current_symbol = None

    def on_tab_changed(self, event):
        """Handle actions when the notebook tab changes.
        
        This method is bound to the '<<NotebookTabChanged>>' event.
        You can expand its functionality as needed.
        """
        # For example, if the selected tab is one of the chart tabs, update the charts.
        selected_tab = event.widget.tab(event.widget.index("current"), "text")
        if selected_tab in ["Daily Charts", "Monthly Charts"]:
            self.update_charts()

    def show_loading(self, show: bool):
        """Toggle loading state"""
        if show:
            self.loading_label.config(text="Loading...")
            self.search_button.config(state='disabled')
            self.export_button.config(state='disabled')
        else:
            self.loading_label.config(text="")
            self.search_button.config(state='normal')
            if self.current_hist_data:
                self.export_button.config(state='normal')

    def clear_frames(self):
        """Clear all frames"""
        for frame in [self.overview_frame, self.daily_charts_frame, 
                      self.monthly_charts_frame, self.h1b_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

    def display_error(self, message: str):
        """Display error message"""
        self.clear_frames()
        ttk.Label(
            self.overview_frame,
            text=message,
            font=FONTS['normal'],
            foreground=COLORS['error']
        ).pack(pady=PADDING['medium'])

    def display_overview(self, data: dict, h1b_df):
        """Display basic stock information"""
        # ----- Stock Overview Section -----
        ttk.Label(
            self.overview_frame,
            text="Stock Overview",
            font=FONTS['header']
        ).pack(pady=PADDING['medium'])

        for key, value in data.items():
            frame = ttk.Frame(self.overview_frame)
            frame.pack(fill='x', pady=2)

            ttk.Label(
                frame,
                text=f"{key}:",
                font=FONTS['bold'],
                width=20,
                anchor='e'
            ).pack(side='left', padx=PADDING['small'])

            ttk.Label(
                frame,
                text=str(value),
                font=FONTS['normal']
            ).pack(side='left', padx=PADDING['small'])

        # ----- H1B Data Overview Section -----
        if h1b_df is not None and not h1b_df.empty:
            ttk.Label(
                self.overview_frame,
                text="H1B Sponsor Overview",
                font=FONTS['header']
            ).pack(pady=PADDING['medium'])
        else:
            # Optionally, you can show a message indicating that no H1B data is available.
            ttk.Label(
                self.overview_frame,
                text="No H1B Sponsor Data Available",
                font=FONTS['normal'],
                foreground=COLORS['error']
            ).pack(pady=PADDING['medium'])

        # Create the H1B figure using your existing function
        

    def display_charts(self, data: dict):
        """Display stock charts for all timeframes"""
        # Clear previous charts only from chart frames
        for frame in [self.daily_charts_frame, self.monthly_charts_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        # Create charts for each timeframe
        daily_chart = create_chart_tab(self.daily_charts_frame, data, 'daily', self.chart_type.get())
        monthly_chart = create_chart_tab(self.monthly_charts_frame, data, 'monthly', self.chart_type.get())

        # Configure weights and layout
        for chart in [daily_chart, monthly_chart]:
            chart.grid(row=0, column=0, sticky="nsew")

    def display_h1b_charts(self, filtered_df):
        """show H1B charts"""
        h1b_chart = create_h1b_chart_tab(self.h1b_frame, filtered_df)
        h1b_chart.grid(row=0, column=0, sticky="nsew")
        
        # 配置布局权重
        self.h1b_frame.grid_rowconfigure(0, weight=1)
        self.h1b_frame.grid_columnconfigure(0, weight=1)

    def update_charts(self):
        """Update charts when chart type changes"""
        if self.current_hist_data:
            self.display_charts(self.current_hist_data)

    def export_data(self):
        """Export current stock data to CSV files"""
        if not self.current_hist_data or not self.current_symbol:
            messagebox.showerror("Error", "No data available to export")
            return

        success, message = export_stock_data(self.current_symbol, self.current_hist_data)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def display_layoff_charts(self, filtered_df):
        """display layoff charts"""
        print("display_layoff_charts")
        layoff_chart = create_layoff_chart_tab(self.layoff_frame, filtered_df)
        layoff_chart.grid(row=0, column=0, sticky="nsew")
        
        self.layoff_frame.grid_rowconfigure(0, weight=1)
        self.layoff_frame.grid_columnconfigure(0, weight=1)

    def display_jobs(self, jobs_df):
        """display_jobs"""
        # 清空原有内容
        for widget in self.jobs_frame.winfo_children():
            widget.destroy()
        print(jobs_df)
        if jobs_df is None or jobs_df.empty:
            ttk.Label(self.jobs_frame, 
                    text="No job listings found", 
                    font=FONTS['normal']).pack(pady=20)
            return

        # 创建滚动框架
        scroll_frame = ScrollableFrame(self.jobs_frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew")

        # 创建表格
        columns = ["Company", "Title", "Location", "URL"]
        tree = ttk.Treeview(scroll_frame.scrollable_frame, columns=columns, show="headings")
        
        # 配置列
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='w')
        
        # 添加数据
        for _, row in jobs_df.iterrows():
            tree.insert("", "end", values=(
                row['company'],
                row['title'],
                row['location'],
                row['job_url']
            ))

        # 添加滚动条
        vsb = ttk.Scrollbar(scroll_frame.scrollable_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(scroll_frame.scrollable_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # 配置权重
        scroll_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.scrollable_frame.grid_rowconfigure(0, weight=1)

    def display_dispute_report(self, report):
        """显示法律纠纷报告"""
        for widget in self.dispute_frame.winfo_children():
            widget.destroy()
        
        scroll_frame = ScrollableFrame(self.dispute_frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        text_widget = tk.Text(
            scroll_frame.scrollable_frame,
            wrap=tk.WORD,
            font=FONTS['normal'],
            bg=COLORS['bg'],
            padx=10,
            pady=10,
            spacing2=4
        )
        text_widget.insert(tk.END, report)
        text_widget.configure(state='disabled')
        
        vsb = ttk.Scrollbar(scroll_frame.scrollable_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=vsb.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        #make text_widget expand
        scroll_frame.scrollable_frame.grid_rowconfigure(0, weight=1)
        vsb.grid(row=0, column=1, sticky="ns")
        
        scroll_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.scrollable_frame.grid_rowconfigure(0, weight=1)

    def display_sec_summary(self, summary):
        """显示10K摘要"""
        for widget in self.sec_frame.winfo_children():
            widget.destroy()
        
        scroll_frame = ScrollableFrame(self.sec_frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        
        text_widget = tk.Text(
            scroll_frame.scrollable_frame,
            wrap=tk.WORD,
            font=FONTS['normal'],
            bg=COLORS['bg'],
            padx=10,
            pady=10,
            spacing2=4
        )
        text_widget.insert(tk.END, summary)
        text_widget.configure(state='disabled')
        
        vsb = ttk.Scrollbar(scroll_frame.scrollable_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=vsb.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        #make text_widget expand
        scroll_frame.scrollable_frame.grid_rowconfigure(0, weight=1)
        vsb.grid(row=0, column=1, sticky="ns")
        
        scroll_frame.scrollable_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.scrollable_frame.grid_rowconfigure(0, weight=1)
        
    def fetch_all_data(self):
        """Fetch both current and historical data"""
        company_name = self.symbol_entry.get().strip()
        if not company_name:
            messagebox.showerror("Error", "Please enter a company name")
            return

        # Use get_ticker to get the corresponding stock symbol
        ticker = get_ticker(company_name)
        symbol = ticker.upper()
        if not ticker:
            messagebox.showerror("Error", "Ticker not found for the given company name.")
            return

        if not validate_symbol(symbol):
            messagebox.showerror("Error", "Please enter a valid stock symbol")
            return

        def fetch_thread():
            self.show_loading(True)
            self.clear_frames()

            # Fetch current data
            success, current_data = fetch_stock_data(symbol)
            if not success:
                self.root.after(0, lambda: self.show_loading(False))
                self.root.after(0, lambda: self.display_error(current_data.get('error', 'Error fetching current data')))
                return

            # Fetch historical data
            success, hist_data = fetch_historical_data(symbol)
            if not success:
                self.root.after(0, lambda: self.show_loading(False))
                self.root.after(0, lambda: self.display_error(hist_data.get('error', 'Error fetching historical data')))
                return

            h1b_df = process_and_match_companies(company_name)

            try:
                layoff_df = layoffs(company_name)
                print("layoffs:", layoff_df.empty)
                if not layoff_df.empty:
                    self.root.after(0, lambda: self.display_layoff_charts(layoff_df))
                else:
                    self.root.after(0, lambda: self.clear_layoff_tab())
            except Exception as e:
                print(f"Failed to layoff data processing: {str(e)}")
                self.root.after(0, lambda: self.clear_layoff_tab())

            try:
                jobs_df = get_filtered_company_jobs(company_name, "Software Engineer")
                print("job df:", jobs_df)
                self.root.after(0, lambda: self.display_jobs(jobs_df))
            except Exception as e:
                print(f"职位数据获取失败: {str(e)}")
                self.root.after(0, lambda: self.display_jobs(None))
            
            try:
                dispute_report = get_info(company_name)
            except Exception as e:
                dispute_report = f"Error generating legal report: {str(e)}"
                
            try:
                summary = get_summary(company_name)
            except Exception as e:
                summary = f"Error generating 10K summary: {str(e)}"
                
            # Store data for updates and export
            self.current_hist_data = hist_data
            self.current_symbol = symbol

            # Update UI in main thread
            self.root.after(0, lambda: self.show_loading(False))
            self.root.after(0, lambda: self.display_overview(current_data, h1b_df))
            self.root.after(0, lambda: self.display_charts(hist_data))
            self.root.after(0, lambda: self.display_h1b_charts(h1b_df))
            self.root.after(0, lambda: self.display_layoff_charts(layoff_df))
            self.root.after(0, lambda: self.display_jobs(jobs_df))
            self.root.after(0, lambda: self.display_dispute_report(dispute_report))
            self.root.after(0, lambda: self.display_sec_summary(summary))
            

        threading.Thread(target=fetch_thread, daemon=True).start()

    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = StockApp()
    app.run()
