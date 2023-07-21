import re
import tkinter as tk
from tkinter import ttk

from subsearch.data.constants import APP_PATHS, VIDEO_FILE
from subsearch.data.data_classes import SkippedSubtitle, Subtitle
from subsearch.gui.resources import config as cfg
from subsearch.providers import subscene
from subsearch.utils import io_file_system


class DownloadList(tk.Frame):
    def __init__(self, parent, formatted_data: list[SkippedSubtitle]) -> None:
        tk.Frame.__init__(self, parent)
        root_posx, root_posy = parent.winfo_reqwidth(), parent.winfo_reqheight()
        self.configure(bg=cfg.color.dark_grey, width=root_posx, height=root_posy - 82)
        if formatted_data is not None:
            formatted_data.sort(key=lambda x: x.pct_result, reverse=True)
        self.formatted_data = formatted_data
        self.subscene_scrape = subscene.SubsceneScraper()
        self.extent = 0
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", style="Vertical.TScrollbar")
        self.sub_listbox = tk.Listbox(
            self,
            height=root_posy,
            bg=cfg.color.dark_grey,
            fg=cfg.color.light_grey,
            font=cfg.font.cas8b,
            bd=0,
            border=0,
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            yscrollcommand=self.scrollbar.set,
        )
        hsx, _hsy = self.scrollbar.winfo_reqwidth(), self.scrollbar.winfo_reqheight()
        self.sub_listbox.place(
            height=root_posy - 82,
            width=root_posx - hsx - 20,
            x=18,
            rely=0.5,
            bordermode="inside",
            anchor="w",
        )
        if self.formatted_data is not None:
            self.fill_listbox()
        self.scrollbar.place(x=root_posx - 17, y=0, bordermode="inside", height=root_posy - 82)
        self.scrollbar.config(command=self.sub_listbox.yview)
        self.scrollbar.lift()

    def fill_listbox(self) -> None:
        self._providers = {}
        self._releases = {}
        self._urls = {}
        # fil list box with all available subtitles that were found and not downloaded
        for enu, data in enumerate(self.formatted_data):
            self.sub_listbox.insert(tk.END, f"{data.prettified_release}\n")
            self.sub_listbox.bind("<ButtonPress-1>", self.mouse_b1_press)
            self._providers[enu] = data.provider
            self._releases[enu] = data.name
            self._urls[enu] = data.url

    def mouse_b1_press(self, event) -> None:
        self.sub_listbox.bind("<<ListboxSelect>>", self.download_button)

    def mouse_b1_release(self, event) -> None:
        self.sub_listbox.bind("<ButtonPress-1>", self.mouse_b1_press)

    def download_button(self, event) -> None:
        self.sub_listbox.unbind("<<ListboxSelect>>")
        self.sub_listbox.bind("<ButtonRelease-1>", self.mouse_b1_release)
        selection = str(self.sub_listbox.curselection())
        item_num = re.findall("(\d+)", selection)[0]
        self.sub_listbox.delete(int(item_num))
        self.sub_listbox.insert(int(item_num), f"» DOWNLOADING «")
        for enum, _provider, _release, _url in zip(
            self._providers.keys(), self._providers.values(), self._releases.values(), self._urls.values()
        ):
            if enum != int(item_num):
                continue
            self.sub_listbox.itemconfig(int(enum), {"fg": cfg.color.blue})
            if _provider == "subscene":
                download_url = self.subscene_scrape.get_download_url(_url)
            else:
                download_url = _url
            path = f"{ APP_PATHS.tmp_dir}\\__{_provider}__{item_num}.zip"
            enum = Subtitle(
                provider=f"Downloading from {_provider}",
                release_name=_release,
                file_path=path,
                download_url=download_url,
                idx_pos=1,
                idx_lenght=1,
            )  # type: ignore
            io_file_system.download_subtitle(enum)  # type: ignore
            io_file_system.extract_files_in_dir(APP_PATHS.tmp_dir, VIDEO_FILE.subs_dir, ".zip")
            io_file_system.del_directory_content(APP_PATHS.tmp_dir)
            break
        self.sub_listbox.delete(int(item_num))
        self.sub_listbox.insert(int(item_num), f"✔ {_release}")
        self.sub_listbox.itemconfig(int(item_num), {"fg": cfg.color.green})
