from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel
from app.config.theme_config import get_theme

from app.client.circle_api import (
    validate_member,
    check_group_status,
    get_group_info,
    get_spending_tracker,
    get_bonus_list,
)

console = Console()

def show_circle_menu():
    clear_screen()
    theme = get_theme()
    tokens = AuthInstance.get_active_tokens()

    if not tokens:
        print_panel("⚠️ Error", "Token tidak ditemukan. Silakan login terlebih dahulu.")
        pause()
        return

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("🐒 Menu XL Circle", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("Kode", justify="right", style=theme["text_key"], width=6)
        table.add_column("Aksi", style=theme["text_body"])
        table.add_row("1", "Validasi Nomor")
        table.add_row("2", "Cek Status Grup")
        table.add_row("3", "Info Grup")
        table.add_row("4", "Spending Tracker")
        table.add_row("5", "Daftar Bonus")
        table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(table, border_style=theme["border_primary"], expand=True))
        choice = console.input(f"[{theme['text_sub']}]Pilih menu:[/{theme['text_sub']}] ").strip()

        match choice:
            case "1":
                msisdn = console.input("Masukkan nomor XL: ").strip()
                validate_member(tokens, msisdn)
                pause()
            case "2":
                msisdn = console.input("Masukkan nomor XL: ").strip()
                check_group_status(tokens, msisdn)
                pause()
            case "3":
                group_id = console.input("Masukkan Group ID: ").strip()
                get_group_info(tokens, group_id)
                pause()
            case "4":
                fid = console.input("Family ID: ").strip()
                sid = console.input("Parent Subs ID: ").strip()
                get_spending_tracker(tokens, fid, sid)
                pause()
            case "5":
                fid = console.input("Family ID: ").strip()
                sid = console.input("Parent Subs ID: ").strip()
                get_bonus_list(tokens, fid, sid)
                pause()
            case "00":
                return
            case _:
                print_panel("⚠️ Error", "Pilihan tidak valid.")
                pause()
