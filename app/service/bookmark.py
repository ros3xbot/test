import os
import json
from typing import List, Dict
from app.menus.util_helper import live_loading, print_panel
from app.config.theme_config import get_theme

class Bookmark:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.packages: List[Dict] = []
            self.filepath = "bookmark.json"

            if os.path.exists(self.filepath):
                self.load_bookmark()
            else:
                self._save([])

            self._initialized = True

    def _save(self, data: List[Dict]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _ensure_schema(self):
        updated = False
        for p in self.packages:
            if "family_name" not in p:
                p["family_name"] = ""
                updated = True
            if "order" not in p:
                p["order"] = 0
                updated = True
        if updated:
            self.save_bookmark()

    def load_bookmark(self):
        theme = get_theme()
        with live_loading("Memuat bookmark...", theme):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.packages = json.load(f)
        self._ensure_schema()

    def save_bookmark(self):
        theme = get_theme()
        with live_loading("Menyimpan bookmark...", theme):
            self._save(self.packages)

    def add_bookmark(
        self,
        family_code: str,
        family_name: str,
        is_enterprise: bool,
        variant_name: str,
        option_name: str,
        order: int,
    ) -> bool:
        key = (family_code, variant_name, order)

        if any(
            (p["family_code"], p["variant_name"], p["order"]) == key
            for p in self.packages
        ):
            print_panel("ℹ️ Info", "Bookmark sudah ada.")
            return False

        self.packages.append(
            {
                "family_name": family_name,
                "family_code": family_code,
                "is_enterprise": is_enterprise,
                "variant_name": variant_name,
                "option_name": option_name,
                "order": order,
            }
        )
        self.save_bookmark()
        print_panel("✅ Sukses", "Bookmark berhasil ditambahkan.")
        return True

    def remove_bookmark(
        self,
        family_code: str,
        is_enterprise: bool,
        variant_name: str,
        order: int,
    ) -> bool:
        for i, p in enumerate(self.packages):
            if (
                p["family_code"] == family_code
                and p["is_enterprise"] == is_enterprise
                and p["variant_name"] == variant_name
                and p["order"] == order
            ):
                del self.packages[i]
                self.save_bookmark()
                print_panel("✅ Sukses", "Bookmark berhasil dihapus.")
                return True
        print_panel("⚠️ Error", "Bookmark tidak ditemukan.")
        return False

    def get_bookmarks(self) -> List[Dict]:
        return self.packages.copy()

BookmarkInstance = Bookmark()
