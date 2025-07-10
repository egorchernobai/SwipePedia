import threading
import requests
import concurrent.futures
import webbrowser
from time import time
from kivy.app import App
from kivy.uix.carousel import Carousel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

Window.size = (360, 640)


# 💡 Быстрая реализация WikipediaLib
class WikipediaLib:
    def __init__(self, language='ru'):
        self.language = language
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "WikiCarouselApp/1.0 (https://example.com)"
        }

    def randomPage(self):
        try:
            # 1. Случайная страница
            r = self.session.get(self.api_url, params={
                "action": "query", "format": "json",
                "list": "random", "rnnamespace": 0, "rnlimit": 1
            }, headers=self.headers)
            page = r.json()['query']['random'][0]
            pageid = page['id']
            title = page['title']

            # 2. Описание
            r = self.session.get(self.api_url, params={
                "action": "query", "format": "json",
                "prop": "extracts", "exintro": True,
                "explaintext": True, "pageids": pageid
            }, headers=self.headers)
            desc = r.json()['query']['pages'][str(pageid)].get('extract', '')

            # 3. Изображения
            r = self.session.get(self.api_url, params={
                "action": "query", "format": "json",
                "prop": "images", "pageids": pageid,
                "imlimit": "max"
            }, headers=self.headers)
            image_titles = []
            for page in r.json().get('query', {}).get('pages', {}).values():
                for img in page.get('images', []):
                    image_titles.append(img['title'])

            # 4. Прямые ссылки
            image_urls = []
            for batch in self._batch(image_titles, 20):
                titles = '|'.join(batch)
                r = self.session.get(self.api_url, params={
                    "action": "query", "format": "json",
                    "prop": "imageinfo", "iiprop": "url",
                    "titles": titles
                }, headers=self.headers)
                for page in r.json().get('query', {}).get('pages', {}).values():
                    if 'imageinfo' in page:
                        url = page['imageinfo'][0]['url']
                        if url.lower().endswith(('.jpg', '.jpeg', '.png')):
                            image_urls.append(url)
            return title, desc.strip(), pageid, image_urls
        except Exception as e:
            print(f"[WikipediaLib] Ошибка: {e}")
            return "Ошибка", "Не удалось загрузить статью", -1, []

    def _batch(self, iterable, size):
        for i in range(0, len(iterable), size):
            yield iterable[i:i + size]


# 🔲 Фоновая подложка
class OverlayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0, 0, 0.5)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# 📱 Слайд с двойным тапом
class DoubleTapSlide(FloatLayout):
    def __init__(self, title, desc, img_url, pageid, language='ru', **kwargs):
        super().__init__(**kwargs)
        self.pageid = pageid
        self.language = language
        self.last_touch_time = 0

        img = AsyncImage(source=img_url, allow_stretch=True, keep_ratio=True,
                         size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.add_widget(img)

        overlay = OverlayWidget(size_hint=(1, None), height=100,
                                pos_hint={'x': 0, 'y': 0})
        self.add_widget(overlay)

        text_box = BoxLayout(orientation='vertical',
                             size_hint=(None, None),
                             size=(Window.width * 0.9, 100),
                             pos_hint={'x': 0.05, 'y': 0.02})

        title_label = Label(text=title, height=30, size_hint=(1, None),
                            color=get_color_from_hex('#FFFFFF'),
                            halign='left', valign='middle')
        title_label.bind(size=title_label.setter('text_size'))

        desc_label = Label(text=desc, height=70, size_hint=(1, None),
                           color=get_color_from_hex('#DDDDDD'),
                           halign='left', valign='top')
        desc_label.bind(size=desc_label.setter('text_size'))

        text_box.add_widget(title_label)
        text_box.add_widget(desc_label)
        self.add_widget(text_box)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            now = time()
            if now - self.last_touch_time < 0.3:
                url = f"https://{self.language}.wikipedia.org/?curid={self.pageid}"
                webbrowser.open(url)
            self.last_touch_time = now
        return super().on_touch_down(touch)


# 🔁 Основное приложение
class WikiCarouselApp(App):
    def build(self):
        self.carousel = Carousel(direction='bottom')
        self.wiki = WikipediaLib()
        self.loading = False
        self.max_slides = 10
        self.load_slides_threaded(5)
        self.carousel.bind(on_touch_up=self.on_swipe_end)
        return self.carousel

    def on_swipe_end(self, instance, touch):
        if instance.collide_point(*touch.pos):
            index = self.carousel.index
            total = len(self.carousel.slides)
            if index is not None and index >= total - 3:
                self.load_slides_threaded(4)

    def load_slides_threaded(self, count=3):
        if self.loading:
            return
        self.loading = True

        def get_slide():
            title, desc, pageid, images = self.wiki.randomPage()
            img_url = next(
                (url for url in images if url.lower().endswith(('.jpg', '.png'))), "")
            return title, desc, img_url, pageid

        def load():
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(
                    lambda _: get_slide(), range(count)))
            slides = [r for r in results if r and r[2]]
            Clock.schedule_once(lambda dt: self.add_slides(slides))

        threading.Thread(target=load, daemon=True).start()

    def add_slides(self, slide_data):
        for title, desc, img_url, pageid in slide_data:
            slide = DoubleTapSlide(title, desc, img_url,
                                   pageid, language=self.wiki.language)
            self.carousel.add_widget(slide)
        self.loading = False
        self.cleanup_old_slides()

    def cleanup_old_slides(self):
        while len(self.carousel.slides) > self.max_slides:
            self.carousel.remove_widget(self.carousel.slides[0])


if __name__ == '__main__':
    WikiCarouselApp().run()
