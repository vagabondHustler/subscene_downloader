import time

from src import registry
from src.current_user import got_key
from src.edit_config import set_default_values
from src.config import get
from src.file_manager import find_video
from src import log
from src.data import get_parameters
from src.sos import cwd
from src.scraper import subscene
# from src.scraper import opensubtitles
from src import file_manager as fm


def main() -> None:
    # initialising
    start = time.perf_counter()
    if got_key() is False:
        set_default_values()
        registry.add_context_menu()
        return exit(0)

    language, lang_abbr = get("language")
    hearing_impaired = get("hearing_impaired")
    precentage = get("percentage")
    focus = get("terminal_focus")
    video_ext: list = get("video_ext")
    video = find_video(cwd(), video_ext)

    # TODO fix this so no try is needed
    try:
        param = get_parameters(cwd().lower(), lang_abbr, video)
    except IndexError as err:
        log.output(err)
        fm.copy_log_to_cwd()
        if focus == "True":
            return exit(1)
        return

    # log parameters
    log.parameters(param, language, lang_abbr, hearing_impaired, precentage)

    # scrape subscene with parameters
    print("\n")
    log.output("[Searching]")
    download_info = subscene.scrape(param, language, lang_abbr, hearing_impaired, precentage)
    # TODO implement opensubtitles, almost done
    # download_info = opensubtitles.scrape(param, language, lang_abbr, hearing_impaired, precentage)
    if download_info is None:
        elapsed = time.perf_counter() - start
        log.output(f"Finished in {elapsed} seconds.")
        fm.copy_log_to_cwd()
        if focus == "True":
            return exit(1)
        return

    # download files from scrape result
    print("\n")
    log.output("[Downloading]")
    for items in download_info:
        file_path, root_dl_url, current_num, total_num = items
        fm.download_zip(file_path, root_dl_url, current_num, total_num)

    # procsess downloaded files
    print("\n")
    log.output("[Procsessing files]")
    fm.extract_zips(cwd(), ".zip")
    fm.clean_up(cwd(), ".zip")
    fm.rename_srts(f"{param.release}.srt", cwd(), f"{param.group}.srt", ".srt")
    fm.move_files(cwd(), f"{param.group}.srt", ".srt")
    print("\n\n")

    # finnishing up
    elapsed = time.perf_counter() - start
    log.output(f"Finished in {elapsed} seconds")

    if focus == "True":
        exit(1)


if __name__ == "__main__":
    main()
