import datetime
import tkinter as tk
from tkinter import filedialog, ttk
import os
import json
import time
import subprocess
import threading
import psutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))

last_space_time = 0
key_CD_time = 0.3

APP_TITLE = 'CLI控制端'
root = tk.Tk()
root.title(APP_TITLE)
root.geometry('720x560')
root.minsize(720, 560)
root.configure(bg='#f4f5f8')

style = ttk.Style()
try:
    style.theme_use('vista')
except Exception:
    pass
style.configure('TFrame', background='#f4f5f8')
style.configure('TLabel', background='#f4f5f8', font=('Segoe UI', 10), foreground='#333333')
style.configure('Header.TLabel', background='#f4f5f8', font=('Segoe UI', 16, 'bold'), foreground='#1f3f72')
style.configure('SubHeader.TLabel', background='#f4f5f8', font=('Segoe UI', 9), foreground='#5c5c5c')
style.configure('TButton', font=('Segoe UI', 10), padding=6)
style.configure('TEntry', padding=4)
style.configure('Horizontal.TSeparator', background='#c5c8d6')

status_var = tk.StringVar(value='狀態：初始化中...')

start_time = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

try:
    root.iconbitmap('icon.ico')
except Exception:
    pass

paned = tk.PanedWindow(root, orient=tk.VERTICAL)
paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))

listbox = tk.Listbox(
    paned,
    selectmode=tk.SINGLE,
    bg='#ffffff',
    fg='#1f2d3d',
    font=('Segoe UI', 10),
    selectbackground='#4a90e2',
    selectforeground='#ffffff',
    activestyle='none',
    relief=tk.FLAT,
    borderwidth=0,
)
paned.add(listbox)

log_frame = ttk.Frame(paned)
scrollbar = ttk.Scrollbar(log_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text = tk.Text(
    log_frame,
    height=10,
    state='disabled',
    bg='#1a1e2d',
    fg='#d7dbe8',
    insertbackground='#ffffff',
    relief=tk.FLAT,
    borderwidth=0,
)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=log_text.yview)
paned.add(log_frame)

item_colors = {}
running_processes = {}  # 追蹤正在運行的進程

def thread_safe_log(name, msg):
    root.after(0, lambda: start_log(name, msg))

def log(msg):
    print(msg)
    log_text.config(state='normal')
    log_text.insert(tk.END, msg + '\n')
    log_text.see(tk.END)  # 自動捲動
    log_text.config(state='disabled')
    os.makedirs('logs', exist_ok=True)
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/logs/{start_time}.txt", 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
        f.flush()

def start_log(name, msg):
    os.makedirs('logs', exist_ok=True)
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/logs/{start_time}_{name}.txt", 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
        f.flush()
    log(msg)

log('CLI控制端啟動成功')

def start_command_thread(content, cwd):
    selected_indices = listbox.curselection()
    name = content.get('name', 'Unknown')
    command = content.get('start_command', 'None')
    thread_safe_log(name, f"[main_info][{name}] 切換目錄: {cwd}")
    thread_safe_log(name, f"[main_info][{name}] 執行指令: {command}")
    if command == 'None' or not command.strip():
        thread_safe_log(name, f"[main_error][{name}] 找不到啟動指令。")
        return
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore',
        )
        # 保存進程引用
        running_processes[name] = process
        
        for line in process.stdout:
            thread_safe_log(name, f"[{name}] {line.rstrip()}")
        process.wait()
        thread_safe_log(name, f"[main_info][{name}] 執行完成，returncode={process.returncode}")
        listbox.itemconfig(selected_indices[0], {'fg': 'red'})
        # 移除進程引用
        if name in running_processes:
            del running_processes[name]
    except Exception as exc:
        thread_safe_log(name, f"[main_error][{name}] 啟動失敗: {exc}")
        listbox.itemconfig(selected_indices[0], {'fg': 'red'})
        if name in running_processes:
            del running_processes[name]

def log_window():
    log_win = tk.Toplevel(root)
    log_win.title("獨立Log窗口")
    log_win.geometry('600x400')
    def toggle_fullscreen(event=None):
        current = log_win.attributes('-fullscreen')
        log_win.attributes('-fullscreen', not current)
    log_win.bind('<F11>', toggle_fullscreen)
    log_win.bind('<Escape>', lambda e: log_win.attributes('-fullscreen', False))
    scrollbar_win = tk.Scrollbar(log_win)
    scrollbar_win.pack(side=tk.RIGHT, fill=tk.Y)
    log_text_win = tk.Text(log_win, state='disabled', bg='black', fg='lime')
    log_text_win.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_text_win.config(yscrollcommand=scrollbar_win.set)
    scrollbar_win.config(command=log_text_win.yview)

    def update_log_window():
        if not log_win.winfo_exists():
            return
        content = log_text.get(1.0, tk.END).strip()
        log_text_win.config(state='normal')
        log_text_win.delete(1.0, tk.END)
        log_text_win.insert(tk.END, content)
        log_text_win.see(tk.END)
        log_text_win.config(state='disabled')
        log_win.after(1000, update_log_window)

    update_log_window()

def switch_CLI():
    selected_indices = listbox.curselection()  # 獲取選中的項目索引
    if not selected_indices:
        tk.messagebox.showinfo('提示', '請選擇要啟動的項目')
        log("[main_warn]未選擇項目，無法啟動")
        return
    index = selected_indices[0]  # 取第一個選中的索引
    file_path = data[index]  # 根據索引獲取對應的文件路徑
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)[0]

    cwd = content['work_folder'] 
    if content['work_folder'] != 'None':
        content['work_folder'] = cwd
    if content['work_folder'] == 'None':
        cwd = os.path.dirname(file_path)
    os.chdir(cwd)

    color = listbox.itemcget(index, 'fg')
    if color in ('red', 'yellow'):
        listbox.itemconfig(index, {'fg': 'green'})
        log(f"[main_info][{content['name']}] 啟動項目")
        thread = threading.Thread(target=start_command_thread, args=(content, cwd), daemon=True)
        thread.start()
    else:
        result = tk.messagebox.askyesno('確認', f'確定要停止 {content["name"]} 嗎？')
        if not result:
            log("[main_info]取消停止項目")
            return
        stop_command = content.get('stop_command', 'None')
        if stop_command == 'None':
            # 直接強制結束進程及其子進程
            name = content['name']
            if name in running_processes:
                process = running_processes[name]
                try:
                    log(f"[main_info][{name}] 嘗試強制結束進程 (PID: {process.pid})")
                    
                    # 使用 psutil 獲取進程樹並終止所有子進程
                    try:
                        parent = psutil.Process(process.pid)
                        # 獲取所有子進程
                        children = parent.children(recursive=True)
                        
                        # 先終止子進程
                        for child in children:
                            try:
                                log(f"[main_info][{name}] 終止子進程 (PID: {child.pid})")
                                child.terminate()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        
                        # 再終止父進程
                        process.terminate()
                        
                        # 等待進程終止
                        try:
                            process.wait(timeout=3)
                            log(f"[main_info][{name}] 進程已終止")
                        except subprocess.TimeoutExpired:
                            # 如果超時，強制殺死進程及子進程
                            log(f"[main_info][{name}] 進程未及時終止，強制殺死進程樹")
                            for child in children:
                                try:
                                    child.kill()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                            process.kill()
                            process.wait()
                            log(f"[main_info][{name}] 進程已強制結束")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 如果 psutil 失敗，使用系統命令（Windows 特定）
                        log(f"[main_info][{name}] 使用系統命令終止進程樹")
                        try:
                            subprocess.run(f"taskkill /PID {process.pid} /T /F", shell=True, check=False)
                            log(f"[main_info][{name}] 進程已通過 taskkill 強制結束")
                        except Exception:
                            pass
                    
                    if name in running_processes:
                        del running_processes[name]
                    listbox.itemconfig(selected_indices[0], {'fg': 'red'})
                except Exception as exc:
                    log(f"[main_error][{name}] 終止進程失敗: {exc}")
            else:
                log(f"[main_warn][{content['name']}] 找不到運行中的進程")
        else:
            try:
                log(f"[main_info][{content['name']}] 執行停止指令: {stop_command}")
                subprocess.run(stop_command, shell=True, cwd=cwd, check=True)
            except Exception as exc:
                log(f"[main_error][{content['name']}] 停止失敗: {exc}")
 
            



def delete_file():
    selected_indices = listbox.curselection()  # 獲取選中的項目索引
    if not selected_indices:
        tk.messagebox.showinfo('提示', '請選擇要刪除的項目')
        log("[main_warn]未選擇項目，無法刪除")
        return
    index = selected_indices[0]  # 取第一個選中的索引
    file_path = data[index]  # 根據索引獲取對應的文件路徑
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    result = tk.messagebox.askyesno('確認', f'確定要刪除 {content[0]["name"]} 嗎？')
    if not result:
        log("[main_info]取消刪除項目")
        return
    data.pop(index)  # 從列表中移除該路徑
    with open('GUI.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)  # 更新GUI.json文件
        log(f"[main_info]刪除項目: {content[0]['name']} 成功")
    reset_list()  # 刷新列表顯示



def reset_list():
    log("[main_info]刷新列表")
    global data, item_colors, status_var
    old_colors = {}
    if 'data' in globals():
        for idx in range(listbox.size()):
            if idx < len(data):
                old_colors[data[idx]] = listbox.itemcget(idx, 'fg')

    listbox.delete(0, tk.END)
    if os.path.exists('GUI.json'):
        with open('GUI.json', 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                tk.messagebox.showinfo('警告', 'GUI.json文件格式錯誤，已重置文件')
                with open('GUI.json', 'w', encoding='utf-8') as f:
                    json.dump([], f)
                    log("[main_warn]GUI.json文件格式錯誤，已重置文件")
                data = []
            try:
                for line in data:
                    try:
                        with open(line, 'r', encoding='utf-8') as f:
                            content = json.load(f)[0]
                            content['work_folder']
                            content['start_command']
                            content['stop_command']
                            content['remark']
                            content['name']
                            listbox.insert(tk.END, f"{content['name']} - {content['remark']}")
                            color = old_colors.get(line, 'red')
                            listbox.itemconfig(listbox.size() - 1, {'fg': color})
                            item_colors[line] = color
                    except FileNotFoundError:
                        tk.messagebox.showinfo('警告', f'文件 {line} 不存在，已從列表中刪除')
                        data.remove(line)
                        with open('GUI.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f)
                            log(f"[main_warn]文件 {line} 不存在，已從列表中刪除")
            except:
                tk.messagebox.showinfo('警告', f'文件 {line}結構讀取時發生錯誤，已從列表中刪除')
                with open('GUI.json', 'w', encoding='utf-8') as f:
                    data.remove(line)
                    json.dump(data, f)
                    log(f"[main_warn]文件 {line} 結構讀取時發生錯誤，已從列表中刪除")
    else:
        with open('GUI.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
            log("[main_info]GUI.json文件不存在，已創建新文件")
            data = []

    if data:
        status_var.set(f'狀態：已載入 {len(data)} 個項目。按 Space 或按鈕啟動/停止。')
    else:
        status_var.set('狀態：目前無項目，請按 開啟 新增 GUI_info 文件。')
    return data
reset_list()

def open_file():
    file_path = tk.filedialog.askopenfilename(title='選擇文件', filetypes=[('GUI_info文件', 'GUI_info.json')])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            if file_path in data:
                tk.messagebox.showinfo('提示', '文件已存在')
                log(f"[main_warn]文件: {file_path} 已存在，無法添加")
            else:
                data.append(file_path)
                with open('GUI.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    log(f"[main_info]添加文件: {file_path} 成功")
                reset_list()




menubar = tk.Menu(root)               # 建立主選單

filemenu = tk.Menu(menubar)           # 建立子選單，選單綁定 menubar 主選單
filemenu.add_command(label="開啟", command=open_file)    # 子選單項目
filemenu.add_command(label="刪除", command=delete_file)    # 子選單項目
filemenu.add_command(label="刷新", command=reset_list)    # 子選單項目
menubar.add_cascade(label='檔案', menu=filemenu)   # 建立主選單，內容為子選單
view = tk.Menu(menubar)           # 建立子選單，選單綁定 menubar 主選單
view.add_command(label="獨立Log窗口", command=log_window)    # 子選單項目
menubar.add_cascade(label='視圖', menu=view)   # 建立主選單，內容為子選單

root.config(menu=menubar)             # 主視窗加入主選單

button_frame = ttk.Frame(root)
button_frame.pack(fill='x', padx=12, pady=(0, 8))

ttk.Button(button_frame, text='開啟', command=open_file).pack(side='left', padx=4)
ttk.Button(button_frame, text='刪除', command=delete_file).pack(side='left', padx=4)
ttk.Button(button_frame, text='刷新', command=reset_list).pack(side='left', padx=4)
ttk.Button(button_frame, text='啟動/停止', command=switch_CLI).pack(side='left', padx=4)
ttk.Button(button_frame, text='查看Log', command=log_window).pack(side='left', padx=4)

status_bar = ttk.Label(root, textvariable=status_var, style='SubHeader.TLabel', anchor='w')
status_bar.pack(fill='x', padx=12, pady=(0, 10))

def on_F5(event):
    global last_space_time
    now = time.time()
    if not now - last_space_time < key_CD_time: 
        log("[main_info]按下F5鍵 (刷新)")
        reset_list()   # 你想做的動作
        last_space_time = now  # 更新上次按下快捷鍵的時間

def on_start_stop(event):
    global last_space_time
    now = time.time()
    if not now - last_space_time < key_CD_time:  
        log("[main_info]按下Space")    
        switch_CLI()   # 你想做的動作
        last_space_time = now  # 更新上次按下快捷鍵的時間

def on_open(event):
    global last_space_time
    now = time.time()
    if not now - last_space_time < key_CD_time:  
        log("[main_info]按下Ctrl+O")
        open_file()   # 你想做的動作
        last_space_time = now  # 更新上次按下快捷鍵的時間

def on_delete(event):
    global last_space_time
    now = time.time()
    if not now - last_space_time < key_CD_time:
        log("[main_info]按下Ctrl+D")
        delete_file()   # 你想做的動作
        last_space_time = now  # 更新上次按下快捷鍵的時間

def on_log_window(event):
    global last_space_time
    now = time.time()
    if not now - last_space_time < 2:
        log("[main_info]按下Ctrl+L")
        log_window()   # 你想做的動作
        last_space_time = now  # 更新上次按下快捷鍵的時間


root.bind("<F5>", on_F5)
root.bind("<space>", on_start_stop)
root.bind("<Control-o>", on_open)
root.bind("<Control-d>", on_delete)
root.bind("<Control-l>", on_log_window)

root.mainloop()