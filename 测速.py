import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import platform
import threading
import socket
import os

class AdvancedNetworkAnalyzer:
    def __init__(self, master):
        self.master = master
        self.master.title("高级网络诊断工具")
        
        # 初始化测试模式变量
        self.current_mode = tk.StringVar(value='专业模式')  # 默认设置为专业模式
        self.continuous_test = tk.BooleanVar(value=False)  # 修复：默认关闭无限持续测试
        
        # 测试配置
        self.test_modes = {
            '专业模式': self.professional_test,
            '自定义模式': self.custom_test,
            '游戏模式': self.game_test
        }
        
        # 测试状态
        self.test_active = False
        self.termination_flag = threading.Event()
        
        # 游戏服务器列表（更新为最新可用的 IP 地址）
        self.game_servers = {
            '英雄联盟-北美': '104.160.131.3',
            'CS2-上海节点': '123.60.157.199',
            'CS2-香港节点': '169.150.222.161',
            '原神-亚服(日本)': '47.91.24.239',
            '原神-亚服(香港)': '8.209.245.30',
            'Steam-香港': '103.28.54.131',
            'Minecraft-国际': '172.65.226.26',
            '王者荣耀': 'game.str.mdt.qq.com'

        }
        
        # 初始化界面
        self.setup_interface()
        self.update_interface()  # 修复：首次打开时更新界面为默认模式

    def setup_interface(self):
        """初始化用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="高级网络诊断工具", 
            # font=("Arial", 16, "bold"), 
            anchor="center"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # 网络代理状态
        self.proxy_status_label = ttk.Label(
            main_frame,
            text="网络代理状态: 检测中...",
            # font=("幼圆", 10),
            anchor="e"
        )
        self.proxy_status_label.grid(row=0, column=1, sticky="e", padx=(0, 10))

        # 模式选择区域
        mode_frame = ttk.LabelFrame(main_frame, text="测试模式", padding=10)
        mode_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        ttk.Label(mode_frame, text="选择模式:").grid(row=0, column=0, sticky="w")
        mode_selector = ttk.Combobox(
            mode_frame,
            textvariable=self.current_mode,
            values=list(self.test_modes.keys()),
            state="readonly",
            width=20
        )
        mode_selector.grid(row=0, column=1, padx=10, sticky="w")
        mode_selector.bind("<<ComboboxSelected>>", self.update_interface)

        # 参数输入区域
        self.control_frame = ttk.LabelFrame(main_frame, text="测试参数", padding=10)
        self.control_frame.grid(row=2, column=0, sticky="ew", pady=10)

        # 动态参数控件
        self.setup_custom_controls()
        self.setup_professional_controls()
        self.setup_game_controls()

        # 通用控制
        ttk.Checkbutton(
            self.control_frame,
            text="无限持续测试",
            variable=self.continuous_test,
            style="TCheckbutton"
        ).grid(row=4, column=0, pady=5, sticky="w")

        self.start_btn = ttk.Button(
            self.control_frame,
            text="开始测试",
            command=self.initiate_testing,
            style="Accent.TButton"
        )
        self.start_btn.grid(row=4, column=1, pady=5, padx=5, sticky="e")
        
        self.stop_btn = ttk.Button(
            self.control_frame,
            text="停止测试",
            state=tk.DISABLED,
            command=self.terminate_testing,
            style="TButton"
        )
        self.stop_btn.grid(row=4, column=2, pady=5, padx=5, sticky="e")

        # 结果展示区域
        result_frame = ttk.LabelFrame(main_frame, text="诊断结果", padding=10)
        result_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        
        self.result_tree = ttk.Treeview(
            result_frame,
            columns=('目标', '状态', '延迟', '丢包'),
            show='headings',
            height=12
        )
        self.result_tree.heading('目标', text='目标名称')
        self.result_tree.heading('状态', text='连接状态')
        self.result_tree.heading('延迟', text='平均延迟(ms)')
        self.result_tree.heading('丢包', text='丢包率(%)')

        # 设置列宽
        self.result_tree.column('目标', width=150, anchor='center')
        self.result_tree.column('状态', width=100, anchor='center')
        self.result_tree.column('延迟', width=100, anchor='center')
        self.result_tree.column('丢包', width=100, anchor='center')

        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 布局配置
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # 样式优化
        self.apply_styles()

        # 检测网络代理状态
        self.check_proxy_status()

    def check_proxy_status(self):
        """检测网络代理是否开启"""
        try:
            proxy_enabled = False
            if platform.system() == "Windows":
                # 检查 Windows 系统代理设置
                output = subprocess.check_output(
                    "reg query \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\" /v ProxyEnable",
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    universal_newlines=True
                )
                if "0x1" in output:  # ProxyEnable 为 0x1 表示代理已启用
                    proxy_enabled = True
            else:
                # 检查类 Unix 系统的环境变量
                proxy_env_vars = ["http_proxy", "https_proxy", "ftp_proxy"]
                proxy_enabled = any(env in os.environ for env in proxy_env_vars)

            # 更新代理状态标签
            status_text = "网络代理状态: 已开启" if proxy_enabled else "网络代理状态: 未开启"
            self.proxy_status_label.config(text=status_text)
        except Exception:
            self.proxy_status_label.config(text="网络代理状态: 检测失败")

    def apply_styles(self):
        """应用样式优化"""
        style = ttk.Style()
        # 去除所有字体设置，使用默认字体
        # style.configure("TLabel", font=("幼圆", 10))
        # style.configure("TButton", font=("幼圆", 10), padding=5, foreground="black")
        # style.configure("Accent.TButton", font=("幼圆", 10, "bold"), foreground="black", background="#0078D7")
        # style.configure("TCheckbutton", font=("幼圆", 10))
        # style.configure("Treeview.Heading", font=("幼圆", 10, "bold"))
        # style.configure("Treeview", font=("幼圆", 10), rowheight=25)
        style.configure("TButton", padding=5, foreground="black")
        style.configure("Accent.TButton", foreground="black", background="#0078D7")
        style.configure("Treeview", rowheight=25)
        # 按钮交互动画
        style.map(
            "TButton",
            background=[("active", "#005A9E"), ("!active", "#0078D7")],
            foreground=[("active", "white"), ("!active", "black")]
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#005A9E"), ("!active", "#0078D7")],
            foreground=[("active", "white"), ("!active", "black")]
        )

    def update_interface(self, event=None):
        """根据选择的模式更新界面"""
        for widget in self.control_frame.winfo_children():
            widget.grid_remove()
            
        if self.current_mode.get() == '自定义模式':
            self.setup_custom_controls()
        elif self.current_mode.get() == '专业模式':
            self.setup_professional_controls()
        elif self.current_mode.get() == '游戏模式':
            self.setup_game_controls()

        # 重新显示通用控件
        ttk.Checkbutton(
            self.control_frame,
            text="无限持续测试",
            variable=self.continuous_test
        ).grid(row=4, column=0, pady=5)
        self.start_btn.grid(row=4, column=1, pady=5)
        self.stop_btn.grid(row=4, column=2, pady=5)

    def setup_custom_controls(self):
        """自定义模式控件"""
        ttk.Label(self.control_frame, text="目标地址:").grid(row=0, column=0)
        self.target_entry = ttk.Entry(self.control_frame, width=25)
        self.target_entry.grid(row=0, column=1, padx=5)
        self.target_entry.insert(0, "8.8.8.8")

        ttk.Label(self.control_frame, text="测试次数:").grid(row=1, column=0)
        self.count_entry = ttk.Entry(self.control_frame, width=8)
        self.count_entry.grid(row=1, column=1, sticky="w", padx=5)
        self.count_entry.insert(0, "20")

        ttk.Label(self.control_frame, text="超时(ms):").grid(row=2, column=0)
        self.timeout_entry = ttk.Entry(self.control_frame, width=8)
        self.timeout_entry.grid(row=2, column=1, sticky="w", padx=5)
        self.timeout_entry.insert(0, "1500")

    def setup_professional_controls(self):
        """专业模式控件"""
        ttk.Label(self.control_frame, text="检测项目:").grid(row=0, column=0)
        info = (
            "包含测试：\n"
            "- 本地回环 (127.0.0.1)\n"
            "- 默认网关\n"
            "- Cloudflare DNS (1.1.1.1)\n"
            "- Google DNS (8.8.8.8)\n"
            "- 百度服务器\n"
            "- 腾讯服务器"
        )
        ttk.Label(self.control_frame, text=info).grid(row=0, column=1, columnspan=2, sticky="w")

    def setup_game_controls(self):
        """游戏模式控件"""
        ttk.Label(self.control_frame, text="选择游戏:").grid(row=0, column=0)
        self.game_selector = ttk.Combobox(
            self.control_frame,
            values=list(self.game_servers.keys()),
            state="readonly",
            width=20
        )
        self.game_selector.grid(row=0, column=1, padx=5)
        self.game_selector.current(0)

    def professional_test(self):
        """专业模式测试逻辑"""
        messagebox.showinfo("提示", "专业模式测试功能尚未实现")

    def custom_test(self):
        """自定义模式测试逻辑"""
        messagebox.showinfo("提示", "自定义模式测试功能尚未实现")

    def game_test(self):
        """游戏模式测试逻辑"""
        messagebox.showinfo("提示", "游戏模式测试功能尚未实现")

    def get_default_gateway(self):
        """获取默认网关（兼容Windows/Linux）"""
        try:
            if platform.system() == "Windows":
                # 使用route命令获取网关
                output = subprocess.check_output(
                    "route print 0.0.0.0",
                    shell=True,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                for line in output.split('\n'):
                    if "0.0.0.0" in line and "在链路上" not in line:
                        parts = line.split()
                        return parts[2]
            else:
                # 使用ip route获取网关
                output = subprocess.check_output(
                    "ip route | grep default",
                    shell=True,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                return output.split()[2]
        except Exception as e:
            self.update_result_table("默认网关", "获取失败", "N/A", "N/A")
            return None

    def initiate_testing(self):
        """启动测试流程"""
        if self.test_active:
            return

        self.prepare_test_environment()
        test_thread = threading.Thread(
            target=self.execute_test_sequence,
            daemon=True
        )
        test_thread.start()

    def execute_test_sequence(self):
        """执行测试序列"""
        mode = self.current_mode.get()
        test_targets = []
        total_packets = 0  # 总发包数
        total_success = 0  # 总成功接收数
        total_failed = 0  # 总丢包数
        
        if mode == '自定义模式':
            target = self.target_entry.get().strip()
            count = int(self.count_entry.get())
            timeout = int(self.timeout_entry.get())
            test_targets = [("自定义目标", target, count, timeout)]
            
        elif mode == '专业模式':
            test_targets = self.get_professional_targets()
            
        elif mode == '游戏模式':
            selected_game = self.game_selector.get()
            target = self.game_servers[selected_game]
            test_targets = [(selected_game, target, 30, 2000)]  # 游戏模式默认30次测试

        while not self.termination_flag.is_set():
            for target_name, target_addr, count, timeout in test_targets:
                result = self.run_diagnostic(target_name, target_addr, count, timeout)
                if result:
                    total_packets += result["总发包数"]
                    total_success += result["成功接收"]
                    total_failed += result["丢包数"]
                
            # 修复：游戏模式不再默认无限测试，受“无限持续测试”选项控制
            if not self.continuous_test.get():
                break

        self.cleanup_test_environment()
        self.send_final_results(total_packets, total_success, total_failed)  # 在测试结束后发送汇总结果

    def get_professional_targets(self):
        """获取专业模式测试目标"""
        targets = []
        
        # 获取默认网关
        gateway = self.get_default_gateway()
        if gateway:
            targets.append(("默认网关", gateway, 10, 1000))

        # 预设重要节点
        preset_nodes = [
            ("本地回环", "127.0.0.1", 5, 500),
            ("Cloudflare DNS", "1.1.1.1", 10, 1500),
            ("Google DNS", "8.8.8.8", 10, 1500),
            ("百度服务器", "www.baidu.com", 10, 2000),
            ("腾讯服务器", "www.qq.com", 10, 2000)
        ]
        
        return preset_nodes + targets

    def run_diagnostic(self, target_name, target_addr, count, timeout):
        """执行单个目标诊断"""
        success = 0
        total_latency = 0
        
        for _ in range(count):
            if self.termination_flag.is_set():  # 检查是否需要停止
                # 修复：停止后直接退出，不记录错误结果
                return None
            
            try:
                latency = self.perform_ping(target_addr, timeout)
                if latency is not None:
                    success += 1
                    total_latency += latency
            except Exception:
                # 修复：停止后不更新表格
                if not self.termination_flag.is_set():
                    self.update_result_table(target_name, "错误", "N/A", "N/A")
                continue

        failed = count - success
        loss_rate = (failed / count) * 100
        avg_latency = total_latency / success if success > 0 else 0
        status = "正常" if loss_rate < 5 else "不稳定" if loss_rate < 20 else "断开"
        
        # 更新结果表格
        self.update_result_table(
            target_name,
            status,
            f"{avg_latency:.1f}" if success > 0 else "N/A",
            f"{loss_rate:.2f}"
        )

        # 返回统计结果
        return {
            "目标": target_name,
            "总发包数": count,
            "成功接收": success,
            "丢包数": failed,
            "丢包率": f"{loss_rate:.2f}%",
            "平均延迟": f"{avg_latency:.1f}" if success > 0 else "N/A"
        }

    def send_final_results(self, total_packets, total_success, total_failed):
        """发送最终汇总测试结果"""
        if total_packets == 0:
            messagebox.showinfo("测试结果", "没有可用的测试结果")
            return

        loss_rate = (total_failed / total_packets) * 100
        result_summary = (
            f"测试结果汇总:\n\n"
            f"总发包数: {total_packets}\n"
            f"成功接收: {total_success}\n"
            f"丢包数: {total_failed}\n"
            f"总体丢包率: {loss_rate:.2f}%\n"
        )

        messagebox.showinfo("测试结果", result_summary)

    def perform_ping(self, target, timeout):
        """执行单个ping测试"""
        cmd = self.build_ping_command(target, timeout)
        try:
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=(timeout / 1000 + 2)
            )
            return self.parse_ping_result(output)
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            raise RuntimeError(f"Ping失败: {str(e)}")

    def build_ping_command(self, target, timeout):
        """构建跨平台ping命令"""
        if platform.system() == "Windows":
            return ["ping", "-n", "1", "-w", str(timeout), target]
        else:
            timeout_sec = max(1, timeout // 1000)
            return ["ping", "-c", "1", "-W", str(timeout_sec), target]

    def parse_ping_result(self, output):
        """解析ping结果"""
        pattern = r"(?:时间|time)[=<>](\d+\.?\d*)\s*ms"
        match = re.search(pattern, output, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def update_result_table(self, target, status, latency, loss):
        """更新结果表格"""
        # 修复：确保在主线程中更新表格
        self.master.after(0, lambda: self.result_tree.insert(
            '', 'end',
            values=(target, status, latency, loss)
        ))
        self.master.after(0, lambda: self.result_tree.yview_moveto(1))

    def prepare_test_environment(self):
        """准备测试环境"""
        self.test_active = True
        self.termination_flag.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.result_tree.delete(*self.result_tree.get_children())

    def cleanup_test_environment(self):
        """清理测试环境"""
        self.master.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.master.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.test_active = False

    def terminate_testing(self):
        """终止测试"""
        self.termination_flag.set()  # 设置停止标志
        self.test_active = False
        self.cleanup_test_environment()  # 清理测试环境

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedNetworkAnalyzer(root)
    root.mainloop()