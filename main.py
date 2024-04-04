# -*- coding: utf-8 -*-
import os, re, requests
from time import time, mktime
from datetime import datetime


RESET, RED, GREEN, YELLOW, BLUE = (
    "\033[0m",
    "\033[31m",
    "\033[32m",
    "\033[33m",
    "\033[34m",
)
BREAKLINE = "\n" + BLUE + "-" * 75 + RESET


def get_coordinate(prompt: str, example: str) -> str:
    print(f"{BREAKLINE}\n{prompt} Пример: {YELLOW}{example}{RESET}")
    while True:
        coordinate = input(f"{GREEN}Введите координату: {RESET}")
        if re.match(r"\d{1,2}\.\d{1,16}", coordinate):
            return coordinate.strip()
        print(f"{RED}Неверный формат координаты!")


def get_date(date_type: str) -> int:
    print(
        f"{BREAKLINE}\nФормат ДД/ММ/ГГГГ ЧЧ:ММ Пример: {YELLOW} 1/3/2020 08:05 \n(время можно не указывать. По умолчанию 00:00) {BREAKLINE}"
    )
    while True:
        if date_type == "start":
            input_date = input(f"{GREEN}Начальная дата: {RESET}")
        elif date_type == "end":
            input_date = input(
                f"{GREEN}Конечная дата или [{RESET}Enter{GREEN}] - текущая: {RESET}"
            )
            if not input_date:
                return int(time())
        else:
            raise ValueError(f"Недопустимый тип даты: {date_type}")
        for format in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                return int(mktime(datetime.strptime(input_date, format).timetuple()))
            except ValueError:
                pass
        print(f"{RED}Неверный формат даты-времени!")


def get_radius() -> int:
    while True:
        radius = input(
            f"{GREEN}Радиус поиска в метрах [{RESET}10, 100, 800, 6000, 50000{GREEN}]: {RESET}"
        )
        if len(radius) > 0 and int(radius) in [10, 100, 800, 6000, 50000]:
            return int(radius)
        print(f"{RED}Неверный формат радиуса!")


def get_size() -> str:
    return input(
        f"{GREEN}Разрешение фото [{RESET}y{GREEN}]-большое или [{RESET}Enter{GREEN}]-маленькое: {RESET}"
    )


class VKPhotoSearcher:
    BASE_URL = "https://api.vk.com/method/photos.search"
    ACCESS_TOKEN = "YOUR_VK_API_TOKEN"  # replace with your VK API token
    API_VERSION = "5.103"  # replace with your VK API version

    def __init__(
        self, lat: str, lon: str, start_time: int, end_time: int, radius: int, size: str
    ) -> None:
        self.lat = lat
        self.lon = lon
        self.start_time = start_time
        self.end_time = end_time
        self.radius = radius
        self.size = size

    def get_search_params(self):
        return {
            "lat": self.lat,
            "long": self.lon,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "radius": self.radius,
            "sort": 0,
            "count": 1000,
            "access_token": self.ACCESS_TOKEN,
            "v": self.API_VERSION,
        }

    def get_photo_url(self, sizes):
        photo = ""
        size_type = "w" if self.size.lower() == "y" else "m"
        for s in sizes:
            if s["type"] == size_type:
                photo = sizes[-4]["url"] if size_type == "w" else sizes[0]["url"]
        if not photo:
            photo = sizes[-1]["url"]
        return photo

    def process_response(self, response):
        result = []
        for item in response["items"]:
            photo_url = self.get_photo_url(item["sizes"])
            date = item["date"]
            if item["owner_id"] > 0:
                result.append([photo_url, date, item["owner_id"]])
        return result

    def search_photos(self):
        params = self.get_search_params()
        response = requests.get(self.BASE_URL, params=params).json()["response"]
        amount = response["count"]
        print(f"Total: {amount}")
        return self.process_response(response)


def generate_html_file(photos, longitude, latitude, size):
    filename = f"{int(time())}.html"
    print(f"Файл: {os.getcwd()}/{filename}")

    with open(filename, "w+", encoding="utf-8") as file:
        place_info = (
            f"Координаты: {longitude} {latitude} <br>Результатов: {len(photos)}"
        )
        columns = (
            " 400px 400px 400px;"
            if size == "y"
            else " 200px 200px 200px 200px 200px 200px;"
        )

        header = """
        <html><head>
        <style>
            .container {{
                display: grid;
                grid-gap: 20px;
                grid-template-columns: {columns};
                text-align: center;
            }}
            a {{
                text-decoration: none;
                color: black;
            }}
            img {{
                max-width: 400px;
                max-height: 300px;
                object-fit: cover;
            }}
        </style></head>
        <body>
        <h2 style="text-align: center">{place_info}</h2>
        <div class="container">
        """.format(
            columns=columns, place_info=place_info
        )
        file.write(header)

        for photo in photos:
            photo_info = f'\n<a target="_blank" rel="noopener" href="https://vk.com/id{photo[2]}"><img src="{photo[0]}" alt=""><br>{datetime.fromtimestamp(photo[1])}</a>'
            file.write(photo_info)

        file.write("\n</div>\n</body>\n</html>")


if __name__ == "__main__":
    try:
        while True:
            longitude = get_coordinate("Координаты в формате ДОЛГОТА", "55.753215")
            latitude = get_coordinate("Координаты в формате ШИРОТА", "37.622504")
            end_date = get_date("end")
            start_date = get_date("start")
            radius = get_radius()
            size = get_size()
            searcher = VKPhotoSearcher(
                latitude, longitude, start_date, end_date, radius, size
            )
            photos = searcher.search_photos()

            print(f"{BLUE}Отфильтрованых результатов: {RESET} {len(photos)}")
            if len(photos) == 0:
                exit(0)

            # with open("photos.json", "w+", encoding="utf-8") as f:
            #     json.dump(photos, f, ensure_ascii=False)

            generate_html_file(photos, longitude, latitude, size)

            input(
                f"{GREEN}Для продолжения нажмите [{RESET}любую клавишу{GREEN}] или [{RESET}Ctrl+C{GREEN}] для выхода{RESET})"
            )
    except KeyboardInterrupt:
        print("\n Выход...")
        exit(0)

    except Exception as err:
        print(err)
        exit(1)
