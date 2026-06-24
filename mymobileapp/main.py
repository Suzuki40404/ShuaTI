import flet as ft
import docx
import re
import random
import os

def main(page: ft.Page):
    # --- App 全局设置 ---
    page.title = "题库刷"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0

    # --- 核心数据结构 ---
    db = {'chapters': {}, 'all': {'单选题': [], '多选题': [], '填空题': [], '判断题': []}}
    favorites = {}
    
    # 考试状态数据
    exam_state = {"paper": [], "config": {}, "answers": {}, "marked": {}}

    # --- 1. 自动读取 assets 文件夹中的题库 ---
    def load_built_in_banks():
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            return
        
        for file in os.listdir(assets_dir):
            if file.endswith(".docx"):
                path = os.path.join(assets_dir, file)
                doc = docx.Document(path)
                text_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                
                current_chap = "未分类导言"
                current_q, q_type = None, None
                tags = ["导论", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章", "第十一章", "第十二章"]

                for line in text_lines:
                    if line in tags or re.match(r'^第[一二三四五六七八九十]+章$', line):
                        current_chap = line
                        if current_chap not in db['chapters']: db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                        continue

                    m = re.match(r'^\d+\.\s*[（\(](单选题|多选题|填空题|判断题)[）\)]\s*(.*)', line)
                    if m:
                        if current_q and q_type:
                            if current_chap not in db['chapters']: db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                            db['chapters'][current_chap][q_type].append(current_q)
                            db['all'][q_type].append(current_q)
                        q_type = m.group(1)
                        current_q = {'id': f"{current_chap}_{q_type}_{len(db['all'][q_type])}", 'question': line, 'options': [], 'answer': '', 'chapter': current_chap, 'type': q_type}
                    elif current_q:
                        if line.startswith('正确答案') or line.startswith('答案'): current_q['answer'] = line
                        elif re.match(r'^[A-Z][\.．、]', line): current_q['options'].append(line)
                        elif line.startswith('(1)') or line.startswith('（1）'): current_q['answer'] += f"\n{line}"
                        else:
                            if not current_q['options'] and not current_q['answer']: current_q['question'] += f"\n{line}"
                if current_q and q_type:
                    if current_chap not in db['chapters']: db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                    db['chapters'][current_chap][q_type].append(current_q)
                    db['all'][q_type].append(current_q)

    # 启动时自动加载内置题库
    load_built_in_banks()

    # --- 2. 手机端 UI 核心组件区 ---
    # 顶部标题栏
    page.appbar = ft.AppBar(
        title=ft.Text("📚 题库刷", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.colors.SURFACE_VARIANT,
    )

    # 主内容滚动区
    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # 渲染单道题目的精美卡片 (浏览模式)
    def create_question_card(q):
        is_fav = q['id'] in favorites
        fav_btn = ft.IconButton(
            icon=ft.icons.STAR if is_fav else ft.icons.STAR_BORDER,
            icon_color=ft.colors.AMBER if is_fav else ft.colors.GREY,
            on_click=lambda e, q=q: toggle_fav(e, q)
        )
        
        def toggle_fav(e, q):
            if q['id'] in favorites: del favorites[q['id']]
            else: favorites[q['id']] = q
            e.control.icon = ft.icons.STAR if q['id'] in favorites else ft.icons.STAR_BORDER
            e.control.icon_color = ft.colors.AMBER if q['id'] in favorites else ft.colors.GREY
            page.update()

        ans_text = ft.Text(q['answer'], color=ft.colors.GREEN, visible=False, weight=ft.FontWeight.BOLD)
        def toggle_ans(e):
            ans_text.visible = not ans_text.visible
            page.update()

        options_col = ft.Column([ft.Text(opt) for opt in q['options']], spacing=5)
        
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text(f"[{q['chapter']}]", size=12, color=ft.colors.GREY),
                    ft.Text(q['question'], weight=ft.FontWeight.BOLD, size=16),
                    options_col,
                    ft.Row([fav_btn, ft.TextButton("👁️ 查看答案", on_click=toggle_ans)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ans_text
                ])
            ),
            margin=ft.margin.symmetric(vertical=5, horizontal=10),
            elevation=2
        )

    def show_empty_warning():
        content_area.controls.clear()
        content_area.controls.append(ft.Container(ft.Text("题库为空，请检查 assets 文件夹中的 Word 文件"), alignment=ft.alignment.center, padding=50))
        page.update()

    # --- 3. 视图切换逻辑 ---
    
    # 【模块 1：全局分类题库】
    def show_global_bank():
        if not any(db['all'].values()): return show_empty_warning()
        content_area.controls.clear()
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="单选题", content=ft.ListView([create_question_card(q) for q in db['all']['单选题']], expand=1, padding=10)),
                ft.Tab(text="多选题", content=ft.ListView([create_question_card(q) for q in db['all']['多选题']], expand=1, padding=10)),
                ft.Tab(text="判断题", content=ft.ListView([create_question_card(q) for q in db['all']['判断题']], expand=1, padding=10)),
                ft.Tab(text="填空题", content=ft.ListView([create_question_card(q) for q in db['all']['填空题']], expand=1, padding=10)),
            ],
            expand=1,
        )
        content_area.controls.append(tabs)
        page.update()

    # 【模块 2：分章节题库】
    def show_chapter_bank():
        if not any(db['all'].values()): return show_empty_warning()
        content_area.controls.clear()
        
        chapter_list = list(db['chapters'].keys())
        if not chapter_list: return
        
        chap_dropdown = ft.Dropdown(
            label="请选择章节",
            options=[ft.dropdown.Option(c) for c in chapter_list],
            value=chapter_list[0],
            width=300
        )
        
        tabs_container = ft.Container(expand=True)
        
        def update_chapter_tabs(e=None):
            chap = chap_dropdown.value
            tabs_container.content = ft.Tabs(
                selected_index=0,
                tabs=[
                    ft.Tab(text="单选", content=ft.ListView([create_question_card(q) for q in db['chapters'][chap].get('单选题', [])], expand=1, padding=10)),
                    ft.Tab(text="多选", content=ft.ListView([create_question_card(q) for q in db['chapters'][chap].get('多选题', [])], expand=1, padding=10)),
                    ft.Tab(text="判断", content=ft.ListView([create_question_card(q) for q in db['chapters'][chap].get('判断题', [])], expand=1, padding=10)),
                    ft.Tab(text="填空", content=ft.ListView([create_question_card(q) for q in db['chapters'][chap].get('填空题', [])], expand=1, padding=10)),
                ],
                expand=1,
            )
            page.update()
            
        chap_dropdown.on_change = update_chapter_tabs
        update_chapter_tabs()
        
        content_area.controls.append(ft.Column([
            ft.Container(chap_dropdown, padding=10, alignment=ft.alignment.center),
            tabs_container
        ], expand=True))
        page.update()

    # 【模块 3：题目检索】
    def show_search():
        if not any(db['all'].values()): return show_empty_warning()
        content_area.controls.clear()
        
        search_input = ft.TextField(label="关键字检索 (输入题干或选项)", expand=True)
        scope_dropdown = ft.Dropdown(label="范围", options=[ft.dropdown.Option("全部章节")] + [ft.dropdown.Option(c) for c in db['chapters'].keys()], value="全部章节", width=120)
        results_list = ft.ListView(expand=True, padding=10)
        
        def execute_search(e):
            results_list.controls.clear()
            kw = search_input.value.strip()
            if not kw: return
            
            scope = scope_dropdown.value
            results = []
            def match_kw(q): return kw in (q['question'] + "".join(q['options']))
            
            if scope == "全部章节":
                for t in db['all']: results.extend([q for q in db['all'][t] if match_kw(q)])
            else:
                for t in db['chapters'][scope]: results.extend([q for q in db['chapters'][scope][t] if match_kw(q)])
            
            if not results:
                results_list.controls.append(ft.Text("没有找到匹配的题目~", color=ft.colors.GREY))
            else:
                for q in results: results_list.controls.append(create_question_card(q))
            page.update()
            
        search_btn = ft.ElevatedButton("检索", on_click=execute_search)
        
        content_area.controls.append(ft.Column([
            ft.Container(ft.Row([search_input, scope_dropdown]), padding=10),
            ft.Container(search_btn, padding=ft.padding.symmetric(horizontal=10)),
            ft.Divider(),
            results_list
        ], expand=True))
        page.update()

    # 【模块 4：我的收藏】
    def show_favorites():
        content_area.controls.clear()
        if not favorites:
            content_area.controls.append(ft.Container(ft.Text("收藏本为空，快去刷题吧！", size=16), alignment=ft.alignment.center, padding=50))
        else:
            list_view = ft.ListView(expand=True, padding=10)
            list_view.controls.append(ft.Text(f"当前共收藏 {len(favorites)} 题", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE))
            for q in list(favorites.values()):
                list_view.controls.append(create_question_card(q))
            content_area.controls.append(list_view)
        page.update()

    # 【模块 5：全真模拟考场】
    def show_exam_setup():
        if not any(db['all'].values()): return show_empty_warning()
        content_area.controls.clear()
        
        setup_col = ft.Column(spacing=20, padding=20, scroll=ft.ScrollMode.AUTO, expand=True)
        setup_col.controls.append(ft.Text("⚙️ 考前参数设置", size=20, weight=ft.FontWeight.BOLD))
        
        time_input = ft.TextField(label="考试总时长 (分钟)", value="60", keyboard_type=ft.KeyboardType.NUMBER)
        setup_col.controls.append(time_input)
        
        inputs = {}
        for t in ["单选题", "多选题", "填空题", "判断题"]:
            max_q = len(db['all'][t])
            row = ft.Row([
                ft.Text(f"{t} (库余 {max_q})", width=120),
                ft.TextField(label="抽取数量", value=str(min(10, max_q)), width=80, keyboard_type=ft.KeyboardType.NUMBER),
                ft.TextField(label="每题分值", value="2", width=80, keyboard_type=ft.KeyboardType.NUMBER)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            setup_col.controls.append(row)
            inputs[t] = row

        def start_exam(e):
            paper = []
            configs = {}
            for t, row in inputs.items():
                cnt = int(row.controls[1].value)
                score = float(row.controls[2].value)
                configs[t] = {'score': score}
                paper.extend(random.sample(db['all'][t], cnt))
            
            if not paper: return
            
            exam_state['paper'] = paper
            exam_state['config'] = configs
            exam_state['answers'] = {q['id']: [] if q['type'] == '多选题' else "" for q in paper}
            show_exam_running()

        setup_col.controls.append(ft.ElevatedButton("🚀 生成试卷并开始作答", on_click=start_exam, width=300, height=50))
        content_area.controls.append(setup_col)
        page.update()

    def show_exam_running():
        content_area.controls.clear()
        paper = exam_state['paper']
        
        exam_list = ft.ListView(expand=True, padding=15, spacing=20)
        exam_list.controls.append(ft.Text("📝 答题区 (请仔细作答)", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE))
        
        for idx, q in enumerate(paper):
            q_id = q['id']
            score = exam_state['config'][q['type']]['score']
            
            q_col = ft.Column([
                ft.Text(f"第 {idx+1} 题 ({q['type']} - {score}分)", weight=ft.FontWeight.BOLD),
                ft.Text(q['question'], size=16),
            ])
            
            def record_ans(e, q_id=q_id): exam_state['answers'][q_id] = e.control.value
            
            def record_multi_ans(e, q_id=q_id, opt=None):
                ans_list = exam_state['answers'][q_id]
                if e.control.value: ans_list.append(opt)
                else: ans_list.remove(opt)

            if q['type'] in ['单选题', '判断题']:
                rg = ft.RadioGroup(content=ft.Column([ft.Radio(value=opt, label=opt) for opt in (q['options'] if q['options'] else ["对", "错"])]), on_change=record_ans)
                q_col.controls.append(rg)
            elif q['type'] == '多选题':
                for opt in q['options']:
                    q_col.controls.append(ft.Checkbox(label=opt, on_change=lambda e, o=opt: record_multi_ans(e, opt=o)))
            elif q['type'] == '填空题':
                q_col.controls.append(ft.TextField(hint_text="在此输入答案", on_change=record_ans))
                
            exam_list.controls.append(ft.Card(content=ft.Container(padding=15, content=q_col), elevation=1))

        exam_list.controls.append(ft.ElevatedButton("📥 确认交卷", on_click=lambda e: show_exam_result(), width=300, height=50, bgcolor=ft.colors.ERROR, color=ft.colors.WHITE))
        content_area.controls.append(exam_list)
        page.update()

    def show_exam_result():
        content_area.controls.clear()
        paper = exam_state['paper']
        
        obj_score, total_obj, total_sub = 0, 0, 0
        for q in paper:
            score_per = exam_state['config'][q['type']]['score']
            if q['type'] in ['单选题', '多选题', '判断题']:
                total_obj += score_per
                std_match = re.search(r'[正]?[确]?[答]?[案]?[：:\s]*([A-Za-z]+|[对错√×])', q['answer'])
                if std_match:
                    std_ans = std_match.group(1).upper().replace('√', '对').replace('×', '错')
                    user_ans = exam_state['answers'].get(q['id'])
                    user_extracted = ""
                    if user_ans:
                        if q['type'] == '单选题': 
                            m = re.match(r'^([A-Z])[\.．、]', user_ans)
                            user_extracted = m.group(1) if m else ""
                        elif q['type'] == '多选题':
                            letters = [re.match(r'^([A-Z])[\.．、]', opt).group(1) for opt in user_ans if re.match(r'^([A-Z])[\.．、]', opt)]
                            user_extracted = "".join(sorted(letters))
                        elif q['type'] == '判断题': user_extracted = user_ans
                    if user_extracted == std_ans: obj_score += score_per
            else:
                total_sub += score_per

        res_list = ft.ListView(expand=True, padding=15, spacing=15)
        
        # 成绩看板
        res_list.controls.append(
            ft.Card(
                color=ft.colors.BLUE_700,
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("🏁 考 试 结 束", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Text(f"客观题得分 (自动): {obj_score:g} / {total_obj:g}", size=18, color=ft.colors.WHITE),
                        ft.Text(f"主观题满分 (自评): {total_sub:g}", size=18, color=ft.colors.WHITE70),
                    ])
                )
            )
        )
        
        for idx, q in enumerate(paper):
            user_ans = exam_state['answers'].get(q['id'], "")
            user_str = " | ".join(sorted(user_ans)) if isinstance(user_ans, list) else user_ans
            
            res_list.controls.append(ft.Card(content=ft.Container(padding=15, content=ft.Column([
                ft.Text(f"第 {idx+1} 题 ({q['type']})", weight=ft.FontWeight.BOLD),
                ft.Text(q['question']),
                ft.Text(f"📝 你的作答: {user_str if user_str else '未作答'}", color=ft.colors.BLUE),
                ft.Text(f"✅ {q['answer']}", color=ft.colors.GREEN, weight=ft.FontWeight.BOLD),
            ]))))
            
        res_list.controls.append(ft.ElevatedButton("🔙 返回重新生成试卷", on_click=lambda e: show_exam_setup(), height=50))
        content_area.controls.append(res_list)
        page.update()

    # --- 4. 底部导航栏联动逻辑 ---
    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0: show_global_bank()
        elif idx == 1: show_chapter_bank()
        elif idx == 2: show_search()
        elif idx == 3: show_favorites()
        elif idx == 4: show_exam_setup()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.MENU_BOOK, label="全局"),
            ft.NavigationDestination(icon=ft.icons.FOLDER, label="章节"),
            ft.NavigationDestination(icon=ft.icons.SEARCH, label="检索"),
            ft.NavigationDestination(icon=ft.icons.STAR, label="收藏"),
            ft.NavigationDestination(icon=ft.icons.QUIZ, label="模拟考"),
        ],
        on_change=on_nav_change
    )

    page.add(content_area)
    show_global_bank()

ft.app(target=main)
