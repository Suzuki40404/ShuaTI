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

                # 题型判断（安全平替正则表达式）
                is_question_line = False
                detected_type = ""
                
                # 检查是否以数字加点开头
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
                    # 保存上一题
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
                            
            # 保存最后一题
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
                margin=ft.margin.symmetric(vertical=5, horizontal=10),
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
                    
                if scope == "
