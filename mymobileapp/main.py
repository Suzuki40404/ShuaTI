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
    page.scroll = ft.ScrollMode.AUTO

    # --- 核心数据 ---
    db = {'chapters': {}, 'all': {'单选题': [], '多选题': [], '填空题': [], '判断题': []}}
    favorites = {}

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
                
                current_chap = "未分类"
                current_q, q_type = None, None
                tags = ["导论", "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章", "第九章", "第十章"]

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

    # 启动时自动加载
    load_built_in_banks()

    # --- 2. 手机端 UI 组件 ---
    # 顶部标题栏
    page.appbar = ft.AppBar(
        title=ft.Text("📚 题库刷 - 终极版", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.colors.SURFACE_VARIANT,
    )

    # 主内容区
    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.HIDDEN)

    # 渲染单道题目的精美卡片
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

        ans_text = ft.Text(q['answer'], color=ft.colors.GREEN, visible=False)
        def toggle_ans(e):
            ans_text.visible = not ans_text.visible
            page.update()

        options_col = ft.Column([ft.Text(opt) for opt in q['options']])
        
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text(f"[{q['chapter']}]", size=12, color=ft.colors.GREY),
                    ft.Text(q['question'], weight=ft.FontWeight.BOLD),
                    options_col,
                    ft.Row([fav_btn, ft.TextButton("👁️ 查看答案", on_click=toggle_ans)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ans_text
                ])
            ),
            margin=ft.margin.symmetric(vertical=5, horizontal=10)
        )

    # --- 3. 视图切换逻辑 ---
    def show_global_bank():
        content_area.controls.clear()
        if not any(db['all'].values()):
            content_area.controls.append(ft.Container(ft.Text("题库为空，请检查 assets 文件夹"), alignment=ft.alignment.center, padding=50))
            return
            
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

    def show_favorites():
        content_area.controls.clear()
        if not favorites:
            content_area.controls.append(ft.Container(ft.Text("收藏本为空，快去刷题吧！"), alignment=ft.alignment.center, padding=50))
        else:
            list_view = ft.ListView(expand=1, padding=10)
            for q in list(favorites.values()):
                list_view.controls.append(create_question_card(q))
            content_area.controls.append(list_view)

    # --- 4. 底部导航栏 ---
    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0: show_global_bank()
        elif idx == 1: show_favorites()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.MENU_BOOK, label="全部题库"),
            ft.NavigationDestination(icon=ft.icons.STAR, label="收藏本"),
        ],
        on_change=on_nav_change
    )

    # 初始化显示
    page.add(content_area)
    show_global_bank()

ft.app(target=main)