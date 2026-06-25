import flet as ft
import random
import traceback
import data  

def main(page: ft.Page):
    try:
        page.title = "题库刷"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.padding = 0

        # 初始化数据库结构
        db = {'chapters': {}, 'all': {'单选题': [], '多选题': [], '填空题': [], '判断题': []}}
        favorites = {}
        exam_state = {"paper": [], "config": {}, "answers": {}, "marked": {}}

        def load_built_in_banks():
            text_lines = []
            for line in data.RAW_TEXT.splitlines():
                line_str = line.strip()
                if line_str:
                    text_lines.append(line_str)
            
            current_chap = "未分类导言"
            current_q, q_type = None, None
            tags = ["导论", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章", "第十一章", "第十二章"]

            for line in text_lines:
                # 章节判断
                is_chap = False
                if line in tags:
                    is_chap = True
                elif line.startswith("第") and ("章" in line) and len(line) <= 6:
                    is_chap = True
                
                if is_chap:
                    current_chap = line
                    if current_chap not in db['chapters']: 
                        db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                    continue

                # 题型判断
                is_question_line = False
                detected_type = ""
                
                dot_idx = line.find('.')
                if dot_idx == -1:
                    dot_idx = line.find('、')
                
                if dot_idx != -1 and line[:dot_idx].isdigit():
                    if "(单选题)" in line or "（单选题）" in line:
                        is_question_line = True
                        detected_type = "单选题"
                    elif "(多选题)" in line or "（多选题）" in line:
                        is_question_line = True
                        detected_type = "多选题"
                    elif "(填空题)" in line or "（填空题）" in line:
                        is_question_line = True
                        detected_type = "填空题"
                    elif "(判断题)" in line or "（判断题）" in line:
                        is_question_line = True
                        detected_type = "判断题"

                if is_question_line:
                    if current_q and q_type:
                        if current_chap not in db['chapters']: 
                            db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                        db['chapters'][current_chap][q_type].append(current_q)
                        db['all'][q_type].append(current_q)
                    
                    q_type = detected_type
                    current_q = {
                        'id': current_chap + "_" + q_type + "_" + str(len(db['all'][q_type])), 
                        'question': line, 
                        'options': [], 
                        'answer': '', 
                        'chapter': current_chap, 
                        'type': q_type
                    }
                elif current_q:
                    if line.startswith('正确答案') or line.startswith('答案'): 
                        current_q['answer'] = line
                    elif line.startswith('A') or line.startswith('B') or line.startswith('C') or line.startswith('D') or line.startswith('E') or line.startswith('F'):
                        if len(line) > 1 and (line[1] in ['.', '．', '、', ' ']):
                            current_q['options'].append(line)
                        else:
                            current_q['options'].append(line)
                    elif line.startswith('(1)') or line.startswith('（1）'): 
                        current_q['answer'] += "\n" + line
                    else:
                        if not current_q['options'] and not current_q['answer']: 
                            current_q['question'] += "\n" + line
                            
            if current_q and q_type:
                if current_chap not in db['chapters']: 
                    db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                db['chapters'][current_chap][q_type].append(current_q)
                db['all'][q_type].append(current_q)

        load_built_in_banks()

        page.appbar = ft.AppBar(
            title=ft.Text("📚 题库刷", weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor="surfaceVariant", 
        )

        content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

        def create_question_card(q):
            is_fav = q['id'] in favorites
            fav_btn = ft.IconButton(
                icon="star" if is_fav else "star_border",
                icon_color="amber" if is_fav else "grey",
                on_click=lambda e, q=q: toggle_fav(e, q)
            )
            
            def toggle_fav(e, q):
                if q['id'] in favorites: del favorites[q['id']]
                else: favorites[q['id']] = q
                e.control.icon = "star" if q['id'] in favorites else "star_border"
                e.control.icon_color = "amber" if q['id'] in favorites else "grey"
                page.update()

            ans_text = ft.Text(q['answer'], color="green", visible=False, weight=ft.FontWeight.BOLD)
            def toggle_ans(e):
                ans_text.visible = not ans_text.visible
                page.update()

            options_col = ft.Column([ft.Text(opt) for opt in q['options']], spacing=5)
            
            return ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column([
                        ft.Text("[" + q['chapter'] + "]", size=12, color="grey"),
                        ft.Text(q['question'], weight=ft.FontWeight.BOLD, size=16),
                        options_col,
                        ft.Row([fav_btn, ft.TextButton("👁️ 查看答案", on_click=toggle_ans)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ans_text
                    ])
                ),
                # 核心修复：纯数字边距，彻底消灭 AttributeError
                margin=10,
                elevation=2
            )

        def show_empty_warning():
            content_area.controls.clear()
            content_area.controls.append(ft.Container(ft.Text("题库为空，未读取到题目！"), alignment=ft.alignment.center, padding=50))
            page.update()

        def show_global_bank():
            if not (db['all']['单选题'] or db['all']['多选题'] or db['all']['判断题'] or db['all']['填空题']): 
                return show_empty_warning()
            content_area.controls.clear()
            tabs = ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(text="单选", content=ft.ListView([create_question_card(q) for q in db['all']['单选题']], expand=1, padding=10)),
                    ft.Tab(text="多选", content=ft.ListView([create_question_card(q) for q in db['all']['多选题']], expand=1, padding=10)),
                    ft.Tab(text="判断", content=ft.ListView([create_question_card(q) for q in db['all']['判断题']], expand=1, padding=10)),
                    ft.Tab(text="填空", content=ft.ListView([create_question_card(q) for q in db['all']['填空题']], expand=1, padding=10)),
                ],
                expand=1,
            )
            content_area.controls.append(tabs)
            page.update()

        def show_chapter_bank():
            if not (db['all']['单选题'] or db['all']['多选题'] or db['all']['判断题'] or db['all']['填空题']): 
                return show_empty_warning()
            content_area.controls.clear()
            chapter_list = list(db['chapters'].keys())
            if not chapter_list: return
            
            chap_dropdown = ft.Dropdown(label="请选择章节", options=[ft.dropdown.Option(c) for c in chapter_list], value=chapter_list[0], width=300)
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
            
            content_area.controls.append(ft.Column([ft.Container(chap_dropdown, padding=10, alignment=ft.alignment.center), tabs_container], expand=True))
            page.update()

        def show_search():
            if not (db['all']['单选题'] or db['all']['多选题'] or db['all']['判断题'] or db['all']['填空题']): 
                return show_empty_warning()
            content_area.controls.clear()
            search_input = ft.TextField(label="关键字检索", expand=True)
            scope_dropdown = ft.Dropdown(options=[ft.dropdown.Option("全部章节")] + [ft.dropdown.Option(c) for c in db['chapters'].keys()], value="全部章节", width=120)
            results_list = ft.ListView(expand=True, padding=10)
            
            def execute_search(e):
                results_list.controls.clear()
                kw = search_input.value.strip()
                if not kw: return
                scope = scope_dropdown.value
                results = []
                
                def match_kw(q):
                    opt_str = ""
                    for o in q['options']:
                        opt_str += o
                    return (kw in q['question']) or (kw in opt_str)
                    
                if scope == "全部章节":
                    for t in db['all']: 
                        for q in db['all'][t]:
                            if match_kw(q): results.append(q)
                else:
                    for t in db['chapters'][scope]: 
                        for q in db['chapters'][scope][t]:
                            if match_kw(q): results.append(q)
                            
                if not results: 
                    results_list.controls.append(ft.Text("没有找到匹配的题目~", color="grey"))
                else:
                    for q in results: results_list.controls.append(create_question_card(q))
                page.update()
                
            search_btn = ft.ElevatedButton("检索", on_click=execute_search)
            # 核心修复：将 ft.padding 换成纯数字 10
            content_area.controls.append(ft.Column([ft.Container(ft.Row([search_input, scope_dropdown]), padding=10), ft.Container(search_btn, padding=10), ft.Divider(), results_list], expand=True))
            page.update()

        def show_favorites():
            content_area.controls.clear()
            if not favorites: 
                content_area.controls.append(ft.Container(ft.Text("收藏本为空，快去刷题吧！", size=16), alignment=ft.alignment.center, padding=50))
            else:
                list_view = ft.ListView(expand=True, padding=10)
                list_view.controls.append(ft.Text("当前共收藏 " + str(len(favorites)) + " 题", weight=ft.FontWeight.BOLD, color="blue"))
                for q in list(favorites.values()): list_view.controls.append(create_question_card(q))
                content_area.controls.append(list_view)
            page.update()

        def show_exam_setup():
            if not (db['all']['单选题'] or db['all']['多选题'] or db['all']['判断题'] or db['all']['填空题']): 
                return show_empty_warning()
            content_area.controls.clear()
            setup_col = ft.Column(spacing=20, padding=20, scroll=ft.ScrollMode.AUTO, expand=True)
            setup_col.controls.append(ft.Text("⚙️ 考前参数设置", size=20, weight=ft.FontWeight.BOLD))
            time_input = ft.TextField(label="考试时长(分钟)", value="60", keyboard_type=ft.KeyboardType.NUMBER)
            setup_col.controls.append(time_input)
            
            inputs = {}
            for t in ["单选题", "多选题", "填空题", "判断题"]:
                max_q = len(db['all'][t])
                default_cnt = 10 if max_q > 10 else max_q
                row = ft.Row([
                    ft.Text(t + "(余" + str(max_q) + ")", width=90), 
                    ft.TextField(label="数量", value=str(default_cnt), width=60, keyboard_type=ft.KeyboardType.NUMBER), 
                    ft.TextField(label="分值", value="2", width=60, keyboard_type=ft.KeyboardType.NUMBER)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                setup_col.controls.append(row)
                inputs[t] = row

            def start_exam(e):
                paper, configs = [], {}
                for t, row in inputs.items():
                    cnt = int(row.controls[1].value)
                    score = float(row.controls[2].value)
                    configs[t] = {'score': score}
                    
                    actual_max = len(db['all'][t])
                    if cnt > actual_max:
                        cnt = actual_max
                        
                    paper.extend(random.sample(db['all'][t], cnt))
                    
                if not paper: return
                
                init_answers = {}
                for q in paper:
                    if q['type'] == '多选题':
                        init_answers[q['id']] = []
                    else:
                        init_answers[q['id']] = ""
                        
                exam_state['paper'] = paper
                exam_state['config'] = configs
                exam_state['answers'] = init_answers
                show_exam_running()

            setup_col.controls.append(ft.ElevatedButton("🚀 生成试卷作答", on_click=start_exam, height=50))
            content_area.controls.append(setup_col)
            page.update()

        def show_exam_running():
            content_area.controls.clear()
            paper = exam_state['paper']
            exam_list = ft.ListView(expand=True, padding=15, spacing=20)
            exam_list.controls.append(ft.Text("📝 答题区", size=20, weight=ft.FontWeight.BOLD, color="blue"))
            
            for idx, q in enumerate(paper):
                q_id = q['id']
                score = exam_state['config'][q['type']]['score']
                q_col = ft.Column([
                    ft.Text("第 " + str(idx+1) + " 题 (" + q['type'] + " - " + str(score) + "分)", weight=ft.FontWeight.BOLD), 
                    ft.Text(q['question'], size=16)
                ])
                
                def make_record_ans(qid):
                    return lambda e: exam_state['answers'].update({qid: e.control.value})
                    
                def make_record_multi_ans(qid, opt_val):
                    def on_check_change(e):
                        ans_list = exam_state['answers'][qid]
                        if e.control.value:
                            if opt_val not in ans_list: ans_list.append(opt_val)
                        else:
                            if opt_val in ans_list: ans_list.remove(opt_val)
                    return on_check_change

                if q['type'] in ['单选题', '判断题']: 
                    opts = q['options'] if q['options'] else ["对", "错"]
                    q_col.controls.append(ft.RadioGroup(
                        content=ft.Column([ft.Radio(value=opt, label=opt) for opt in opts]), 
                        on_change=make_record_ans(q_id)
                    ))
                elif q['type'] == '多选题': 
                    for opt in q['options']: 
                        q_col.controls.append(ft.Checkbox(label=opt, on_change=make_record_multi_ans(q_id, opt)))
                elif q['type'] == '填空题': 
                    q_col.controls.append(ft.TextField(hint_text="输入答案", on_change=make_record_ans(q_id)))
                    
                exam_list.controls.append(ft.Card(content=ft.Container(padding=15, content=q_col), elevation=1))

            exam_list.controls.append(ft.ElevatedButton("📥 确认交卷", on_click=lambda e: show_exam_result(), height=50, bgcolor="red", color="white"))
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
                    
                    std_ans = ""
                    raw_ans_field = q['answer'].upper()
                    
                    clean_ans = raw_ans_field.replace('正确答案', '').replace('答案', '').replace(':', '').replace('：', '').strip()
                    for char in clean_ans:
                        if char in ['A', 'B', 'C', 'D', 'E', 'F', '对', '错']:
                            std_ans += char
                    std_ans = std_ans.replace('√', '对').replace('×', '错')

                    user_ans = exam_state['answers'].get(q['id'])
                    user_extracted = ""
                    if user_ans:
                        if q['type'] == '单选题': 
                            if len(user_ans) > 0: user_extracted = user_ans[0]
                        elif q['type'] == '多选题': 
                            letters = []
                            for opt in user_ans:
                                if len(opt) > 0 and opt[0] in ['A', 'B', 'C', 'D', 'E', 'F']:
                                    letters.append(opt[0])
                            letters.sort()  
                            user_extracted = "".join(letters)
                        elif q['type'] == '判断题': 
                            user_extracted = user_ans
                            
                    if user_extracted == std_ans and std_ans != "": 
                        obj_score += score_per
                else: 
                    total_sub += score_per

            res_list = ft.ListView(expand=True, padding=15, spacing=15)
            res_list.controls.append(ft.Card(color="blue", content=ft.Container(padding=20, content=ft.Column([
                ft.Text("🏁 考 试 结 束", size=24, weight=ft.FontWeight.BOLD, color="white"), 
                ft.Text("客观题得分: " + str(obj_score) + " / " + str(total_obj), size=18, color="white"), 
                ft.Text("主观题满分: " + str(total_sub), size=18, color="white")
            ]))))
            
            for idx, q in enumerate(paper):
                user_ans = exam_state['answers'].get(q['id'], "")
                if isinstance(user_ans, list):
                    user_ans.sort()
                    user_str = " | ".join(user_ans)
                else:
                    user_str = user_ans
                    
                res_list.controls.append(ft.Card(content=ft.Container(padding=15, content=ft.Column([
                    ft.Text("第 " + str(idx+1) + " 题 (" + q['type'] + ")", weight=ft.FontWeight.BOLD), 
                    ft.Text(q['question']), 
                    ft.Text("📝 你的作答: " + (user_str if user_str else '未作答'), color="blue"), 
                    ft.Text("✅ " + q['answer'], color="green", weight=ft.FontWeight.BOLD)
                ]))))
                
            res_list.controls.append(ft.ElevatedButton("🔙 返回重新生成", on_click=lambda e: show_exam_setup(), height=50))
            content_area.controls.append(res_list)
            page.update()

        def on_nav_change(e):
            idx = e.control.selected_index
            if idx == 0: show_global_bank()
            elif idx == 1: show_chapter_bank()
            elif idx == 2: show_search()
            elif idx == 3: show_favorites()
            elif idx == 4: show_exam_setup()

        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon="menu_book", label="全局"),
                ft.NavigationBarDestination(icon="folder", label="章节"),
                ft.NavigationBarDestination(icon="search", label="检索"),
                ft.NavigationBarDestination(icon="star", label="收藏"),
                ft.NavigationBarDestination(icon="quiz", label="模拟考"),
            ],
            on_change=on_nav_change
        )

        page.add(content_area)
        show_global_bank()

    except Exception as e:
        error_details = traceback.format_exc()
        page.controls.clear()
        page.add(ft.AppBar(title=ft.Text("⚠️ 启动保护模式", color="white"), bgcolor="red"), ft.Container(padding=20, content=ft.Column([ft.Text("糟糕！应用初始化遇到错误：", weight=ft.FontWeight.BOLD, size=18), ft.Container(padding=10, bgcolor="#eeeeee", border_radius=5, content=ft.Text(error_details, size=12, selectable=True, color="black"))], scroll=ft.ScrollMode.AUTO)))
    page.update()

ft.app(target=main)
