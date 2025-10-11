from app.menus.package import get_packages_by_family
from app.menus.util import clear_screen, pause
from app.service.family_bookmark import FamilyBookmarkInstance
from app.config.theme_config import get_theme

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD

console = Console()

def show_family_bookmark_menu():
    theme = get_theme()
    in_menu = True

    while in_menu:
        clear_screen()
        console.print(Panel("📚 Bookmark Family Code", style=theme["border_info"], expand=True))

        bookmarks = FamilyBookmarkInstance.get_bookmarks()
        if not bookmarks:
            console.print(Panel("ℹ️ Tidak ada bookmark family code tersimpan.", style=theme["border_warning"], expand=True))
            pause()
            return

        # Tabel daftar bookmark
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Kode", style=theme["border_warning"])

        for idx, bm in enumerate(bookmarks, start=1):
            table.add_row(str(idx), bm["family_name"], bm["family_code"])

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

        # Navigasi
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("🔢", "Pilih nomor untuk melihat daftar paket")
        nav.add_row("99", "❌ Hapus Bookmark")
        nav.add_row("00", "↩️ Kembali ke Menu Utama")

        console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()

        if choice == "00":
            break

        elif choice == "99":
            del_choice = console.input(f"[{theme['text_sub']}]Masukkan nomor bookmark yang ingin dihapus:[/{theme['text_sub']}] ").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                bm = bookmarks[int(del_choice) - 1]
                success = FamilyBookmarkInstance.remove_bookmark(bm["family_code"])
                msg = f"Bookmark '{bm['family_name']}' berhasil dihapus." if success else "Gagal menghapus bookmark."
                style = theme["border_success"] if success else theme["border_err"]
                console.print(Panel(msg, style=style, expand=True))
                pause()
            else:
                console.print(Panel("⚠️ Nomor tidak valid.", style=theme["border_err"], expand=True))
                pause()

        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected = bookmarks[int(choice) - 1]
            get_packages_by_family(selected["family_code"])
            # Setelah kembali dari daftar paket, menu bookmark akan ditampilkan ulang

        else:
            console.print(Panel("⚠️ Pilihan tidak valid.", style=theme["border_err"], expand=True))
            pause()
