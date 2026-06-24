import flet as ft
import os

def main(page: ft.Page):
    page.title = "测试程序"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # 获取 assets 目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    
    # 检查目录下到底有什么
    try:
        files = os.listdir(assets_dir)
        file_list_text = "\n".join(files)
        msg = f"找到 assets 文件夹！\n路径: {assets_dir}\n包含文件:\n{file_list_text}"
    except Exception as e:
        msg = f"错误: {str(e)}"
        
    page.add(
        ft.Container(
            content=ft.Text(msg, size=16),
            padding=20,
            bgcolor=ft.colors.BLUE_100
        )
    )

# 核心：明确 assets_dir
ft.app(target=main, assets_dir="assets")
