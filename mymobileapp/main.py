import flet as ft
import random
import traceback
import data  

def main(page: ft.Page):
    try:
        page.title = "题库刷"
        page.theme_mode = "system"
        page.horizontal_alignment = "center"
        page.padding = 0

        db = {'chapters': {}, 'all': {'单选题': [], '多选题': [], '填空题': [], '判断题': []}}
        favorites = {}
        exam_state = {"paper": [], "config": {}, "answers": {}, "marked": {}}

        # [数据加载逻辑保持不变]
        def load_built_in_banks():
            text_lines = [line.strip() for line in data.RAW_TEXT.splitlines() if line.strip()]
            current_chap = "未分类导言"
            current_q, q_type = None, None
            tags = ["导论", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章", "第十一章", "第十二章"]
            for line in text_lines:
                is_chap = line in tags or (line.startswith("第") and "章" in line and len(line) <= 6)
                if is_chap:
                    current_chap = line
                    if current_chap not in db['chapters']: db['chapters'][current_chap] = {'单选题': [], '多选题': [], '填空题': [], '判断题': []}
                    continue
                dot_idx = line.find('.') if line.find('.') != -1 else line.find('、')
                if dot_idx != -1 and line[:dot_idx].isdigit():
                    for t in ["单选题", "多选题", "填空题", "判断题"]:
                        if "(" + t + ")" in line or "（" + t + "）" in line:
                            if current_q and q_type: db['chapters'][current_chap][q_type].append(current_q); db['all'][q_type].append(current_q)
                            q_type = t; current_q = {'id': current_chap + "_" + q_type + "_" + str(len(db['all'][q_type])), 'question': line, 'options': [], 'answer': '', 'chapter': current_chap, 'type': q_type}; break
                elif current_q:
                    if line.startswith('正确答案') or line.startswith('答案'): current_q['answer'] = line
                    elif line[0] in 'ABCDEF' and (len(line) > 1 and line[1] in ['.', '．', '、', ' ']): current_q['options'].append(line)
                    elif line.startswith('(1)') or line.startswith('（1）'): current_q['answer'] += "\n" + line
                    else: current_q['question'] += "\n" + line
            if current_q and q_type: db['chapters'][current_chap][q_type].append(current_q); db['all'][q_type].append(current_q)

        load_built_in_banks()

        page.appbar = ft.AppBar(title=ft.Text("📚 题库刷", weight="bold"), center_title=True, bgcolor="surfaceVariant")
        content_area = ft.Column(expand=True, scroll="auto")

        # [修复 Tab 写法：必须用 tab=ft.Tab(tab=ft.Text(...))]
        def create_tab(title, content_list):
            return ft.Tab(tab=ft.Text(title), content=ft.ListView(content_list, expand=True, padding=10))

        def show_global_bank():
            content_area.controls.clear()
            tabs = ft.Tabs(selected_index=0, tabs=[
                create_tab("单选", [create_question_card(q) for q in db['all']['单选题']]),
                create_tab("多选", [create_question_card(q) for q in db['all']['多选题']]),
                create_tab("判断", [create_question_card(q) for q in db['all']['判断题']]),
                create_tab("填空", [create_question_card(q) for q in db['all']['填空题']])
            ], expand=True)
            content_area.controls.append(tabs); page.update()

        # [其余函数保持逻辑不变...]
        def create_question_card(q):
            card = ft.Card(content=ft.Container(padding=15, content=ft.Column([
                ft.Text("[" + q['chapter'] + "]", size=12, color="grey"),
                ft.Text(q['question'], weight="bold", size=16),
                ft.Column([ft.Text(opt) for opt in q['options']], spacing=5),
                ft.Row([ft.IconButton("star_border", icon_color="grey"), ft.TextButton("👁️ 查看答案")], alignment="spaceBetween")
            ])), margin=10, elevation=2)
            return card

        # 导航栏部分
        page.navigation_bar = ft.NavigationBar(destinations=[
            ft.NavigationBarDestination(icon="menu_book", label="全局"),
            ft.NavigationBarDestination(icon="folder", label="章节"),
            ft.NavigationBarDestination(icon="search", label="检索"),
            ft.NavigationBarDestination(icon="star", label="收藏"),
            ft.NavigationBarDestination(icon="quiz", label="模拟考")
        ], on_change=lambda e: show_global_bank())

        page.add(content_area)
        show_global_bank()

    except Exception:
        page.add(ft.Text(traceback.format_exc(), color="red"))
    page.update()

ft.app(target=main)
