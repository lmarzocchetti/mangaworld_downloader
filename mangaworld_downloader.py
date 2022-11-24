import sys
import requests
import bs4
import os
import subprocess
import shutil
import threading
from PIL import Image
import img2pdf

RESEARCH_STRING = "https://www.mangaworld.so/archive?keyword="

CHAPTERS_STRING = "?style=pages"


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='#', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} [{bar}] {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def research_manga(manga: str) -> dict[str, str]:
    """
    Function that take a manga name and return 
    the dictionary of all results

    Args:
        manga (str): string of the researched manga

    Returns:
        dict[str, str]: dictionary of manga and their link
    """
    page = requests.get(RESEARCH_STRING + manga)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job_all = results.find_all("a", class_="thumb position-relative")

    manga_dict = {job.__str__().split(r'"')[5]: job.__str__().split(r'"')[
        3] for job in job_all}

    return manga_dict


def manga_with_volumes_links(job_all: bs4.element.ResultSet) -> dict[str, list[str]]:
    """Return a dictionary with number of volumes and all the links for their chapters, for mangas that have volumes division

    Args:
        job_all (bs4.element.ResultSet): Each element of the volume to parse

    Returns:
        dict[str, list[str]]: dictionary with keys: volume_number and values:list to their chapter links
    """
    vol_chap_dict = {}

    for num_vol, vol in enumerate(job_all):
        for chap in vol.find_all("a", class_="chap"):
            key = f"Volume{num_vol}"
            if key not in vol_chap_dict.keys():
                vol_chap_dict[key] = []
            vol_chap_dict[key].append(chap.__str__().split(r'"')[3])

    for volume, chap_list in vol_chap_dict.items():
        tmp = chap_list[::-1]
        vol_chap_dict[volume] = tmp

    return vol_chap_dict


def manga_with_chapters_links(job_all: bs4.element.ResultSet) -> dict[str, list[str]]:
    """Return a dictionary with 1 volume and all the links for it chapters, for mangas that doesn't have volumes but only chapters

    Args:
        job_all (bs4.element.ResultSet): Each element of the volume to parse (aka all chapters in this case)

    Returns:
        dict[str, list[str]]: dictionary with keys: dictionary with 1 key (Volume0) and a links to it chapters
    """
    vol_chap_dict = {}
    vol_chap_dict["Volume0"] = []

    for _, vol in enumerate(job_all):
        for chap in vol.find_all("a", class_="chap"):
            vol_chap_dict["Volume0"].append(
                chap.__str__().split(r'"')[3].split("?")[0])

    return vol_chap_dict


def volumes_with_chapter_link(manga_url: str) -> dict[str, list[str]]:
    """
    Function that take a manga url and return a
    dictionary with all volumes and link of their chapters

    Args:
        manga_url (str): String of a manga url

    Returns:
        dict[str, list[str]]: dictionary with in key a string with volume name, and value a list with all the links of every chapters in volumes
    """
    page = requests.get(manga_url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job_all = results.find_all("div", class_="volume-element pl-2")[::-1]

    # se un manga non e' diviso in volumi, ma contiene solo capitoli
    if (len(job_all) == 0):
        job_all = results.find_all("div", class_="chapter pl-2")[::-1]
        return manga_with_chapters_links(job_all)
    else:
        return manga_with_volumes_links(job_all)


def print_manga(manga_dict: dict[str, str]):
    """Clear the screen and print all mangas available

    Args:
        manga_dict (dict[str, str]): Mangas researched
    """
    _ = subprocess.call('clear' if os.name == 'posix' else 'cls')

    for index, manga in enumerate(manga_dict.keys()):
        print(f"{index}-{manga}")
    print("\n")


def choose_manga(manga_dict: dict[str, str]) -> str:
    """Simple TUI for select a manga to download

    Args:
        manga_dict (dict[str, str]): Mangas researched

    Returns:
        str: Manga selected
    """
    while True:
        print_manga(manga_dict)
        selected_manga: str = input(
            "Insert the number of the manga do you want to download: ")

        if selected_manga.isdigit() and int(selected_manga) >= 0 and int(selected_manga) < len(manga_dict.keys()):
            return list(manga_dict.keys())[int(selected_manga)]


def number_of_images_in_chapter(chapter_url: str) -> int:
    """Return the number of images in the chapter linked by the chapter url

    Args:
        chapter_url (str): A chapter url

    Returns:
        int: Number of images in chapters
    """
    page = page = requests.get(chapter_url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    job = results.find(
        "select", class_="page custom-select").find("option").__str__()

    number_of_images = job.split("/")[1].split("<")[0]

    return number_of_images


def download_image(image_url: str, vol_index: str, chap_index: str, image_index: str, selected_manga: str) -> None:
    """Download an image and save it to a folder (Data/{selected_manga}/{vol_index}/{chap_index}_{image_index}.jpg)

    Args:
        image_url (str): url to download the image
        vol_index (str): volume associated with that image
        chap_index (str): chapter index in this volume
        image_index (str): positional number of this image a specific chapter
        selected_manga (str): manga selected
    """
    page = requests.get(image_url)
    soup = bs4.BeautifulSoup(page.content, "html.parser")
    results = soup.find("body")
    image_link = results.find(
        "div", class_="col-12 text-center position-relative").find("img", class_="img-fluid").get("src")

    image = requests.get(image_link, stream=True)
    if image.status_code == 200:
        image.raw.decode_content = True
    with open(os.path.join("Data", selected_manga, str(vol_index), f"{chap_index}_{image_index}.jpg"), "wb") as f:
        shutil.copyfileobj(image.raw, f)


def download_chapter_images(chapter_url: str, vol_index: str, chap_index: str, selected_manga: str, number_of_images: int) -> None:
    """Download all images contained in a chapter and save it (see download_image function)

    Args:
        chapter_url (str): url associated with a chapter
        vol_index (str): volume number associated with this chapter
        chap_index (str): chapter index in this volume
        selected_manga (str): manga selected
        number_of_images (int): number of images contained this chapter
    """
    threads = []

    for i in range(1, int(number_of_images) + 1):
        url: str = chapter_url + "/" + str(i) + CHAPTERS_STRING
        threads.append(threading.Thread(target=download_image, args=(
            url, vol_index, chap_index, str(i), selected_manga)))

    for thread in threads:
        thread.start()

    for i in range(len(threads)):
        threads[i].join()


def download_volumes_images(vol_chap_dict: dict[str, list[str]], selected_manga: str) -> dict[int, dict[int, int]]:
    """Download all images in every volume of a specific manga

    Args:
        vol_chap_dict (dict[str, list[str]]): dictionary in which the keys are the volumes and values are the links to their chapters
        selected_manga (str): manga selected

    Returns:
        dict[int, dict[int, int]]: dictionary of dictionary, with key=volume and the value is dictionary with key=chapter and value=number of images in the chapter
    """
    vol_chap_num_images_dict: dict[int, dict[int, int]] = {}

    total_chapter: int = sum([len(chaps) for chaps in vol_chap_dict.values()])
    current_chapter: int = 0

    for index_vol, vol_name in enumerate(vol_chap_dict.keys()):
        chap_num_pages_dict: dict[int, int] = {}

        for index_chap, chap_link in enumerate(vol_chap_dict[vol_name]):
            url: str = chap_link + "/" + str(1) + CHAPTERS_STRING
            number_of_images = number_of_images_in_chapter(url)
            chap_num_pages_dict[index_chap] = number_of_images
            download_chapter_images(chap_link, str(index_vol), str(
                index_chap), selected_manga, number_of_images)
            current_chapter += 1
            printProgressBar(current_chapter, total_chapter,
                             prefix="Chapter download:", length=50)

        vol_chap_num_images_dict[index_vol] = chap_num_pages_dict

    return vol_chap_num_images_dict


def create_data_volumes_folders(selected_manga: str, vol_chap_dict: dict[str, list[str]]) -> None:
    """Create Data folder, manga folder and inside create the Volumes folders with "volumeNumber_numberofchapters"

    Args:
        selected_manga (str): manga which are selected
        vol_chap_dict (dict[str, list[str]]): dictionary with all volumes and list of links to their chapters
    """
    base_dir = os.path.abspath(os.curdir)

    os.mkdir("Data")
    os.chdir("Data")

    os.mkdir(selected_manga)
    os.chdir(selected_manga)

    for index, _ in enumerate(vol_chap_dict.keys()):
        # name = f"{index}_{len(vol_chap_dict[volume])}"
        os.mkdir(str(index))

    os.chdir(base_dir)


def remove_data_folder() -> None:
    """Remove recursively all data in the Data folder
    """
    shutil.rmtree("Data")


def create_pdf(vol_chap_num_pages: dict[int, dict[int, int]], selected_manga: str) -> None:
    """Create pdfs of every volume contained in the selected manga

    Args:
        vol_chap_num_pages (dict[int, dict[int, int]]): see @download_volumes_images function
        selected_manga (str): manga selected
    """
    for vol_num, chap_num_pag_dict in vol_chap_num_pages.items():
        images = []

        for chap_num, num_pages in chap_num_pag_dict.items():
            for i in range(1, int(num_pages) + 1):
                images.append(Image.open(os.path.join(
                    "Data", selected_manga, str(vol_num), f"{chap_num}_{i}.jpg")))

        images_filename = [image.filename for image in images]

        pdf_bytes = img2pdf.convert(images_filename)

        file = open(f"Volume_{vol_num}.pdf", "wb")

        file.write(pdf_bytes)

        for image in images:
            image.close()

        file.close()


def main():
    if len(sys.argv) != 2:
        print("Insert a manga to research!", file=sys.stderr)
        exit(-1)

    manga_to_research: str = sys.argv[1]

    manga_dict: dict[str, str] = research_manga(manga_to_research)

    if len(manga_dict.keys()) == 0:
        print("No manga found with that name! Closing the program...", file=sys.stderr)
        exit(-2)

    selected_manga: str = choose_manga(manga_dict)

    vol_chap_dict: dict[str, list[str]] = volumes_with_chapter_link(
        manga_dict[selected_manga])

    create_data_volumes_folders(selected_manga, vol_chap_dict)

    volume_chap_num_pages_dict: dict[int, dict[int, int]] = download_volumes_images(
        vol_chap_dict, selected_manga)

    create_pdf(volume_chap_num_pages_dict, selected_manga)

    remove_data_folder()


if __name__ == "__main__":
    main()
