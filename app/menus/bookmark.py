from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family
from app.config.theme_config import get_theme
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD
from rich.align import Align

console = Console()

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        #console.print(Panel("🔖 Bookmark Paket", title="📌 Bookmark", border_style=theme["border_info"], expand=True))
        console.print(Panel(
            Align.center("📌Daftar Bookmark Paket", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        bookmarks = BookmarkInstance.get_bookmarks()
        if not bookmarks:
            print_panel("ℹ️ Info", "Tidak ada bookmark tersimpan.")
            pause()
            return None

        bookmark_table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        bookmark_table.add_column("No", style=theme["text_key"], justify="right", width=4)
        bookmark_table.add_column("Nama Paket", style=theme["text_body"])

        for idx, bm in enumerate(bookmarks):
            label = f"{bm['family_name']} - {bm['variant_name']} - {bm['option_name']}"
            bookmark_table.add_row(str(idx + 1), label)

        console.print(Panel(bookmark_table, border_style=theme["border_primary"], expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(justify="left", style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        nav_table.add_row("000", f"[{theme['text_err']}]Hapus Bookmark[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih bookmark (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return None
        elif choice == "000":
            del_choice = console.input("Masukkan nomor bookmark yang ingin dihapus: ").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
                print_panel("✅ Info", "Bookmark berhasil dihapus.")
                pause()
            else:
                print_panel("⚠️ Error", "Input tidak valid. Silakan coba lagi.")
                pause()
            continue
        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]

            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_panel("⚠️ Error", "Gagal mengambil data family.")
                pause()
                continue

            option_code = None
            for variant in family_data["package_variants"]:
                if variant["name"] == selected_bm["variant_name"]:
                    for option in variant["package_options"]:
                        if option["order"] == selected_bm["order"]:
                            option_code = option["package_option_code"]
                            break

            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silakan coba lagi.")
            pause()
