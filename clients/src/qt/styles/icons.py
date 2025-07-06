import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
media_dir = os.path.join(base_dir, "media")
svgs_dir = os.path.join(media_dir, "svgs")

class SVGManager:
    def __init__(self):
        self.icons = {}

    def add_icon(self, path):
        sys_path = os.path.join(svgs_dir, path).replace("\\", "/")

        if not os.path.exists(sys_path):
            print(f"SVG-файл не найден: {self.icons[path]}")
            return

        self.icons[path] = sys_path

    def get_icon(self, path):
        return self.icons.get(path)


icons_paths = [
    "done.svg",
    "maximize.svg",
    "minimize.svg",
    "collapse.svg",
    "close.svg",
    "back.svg",
]

svg_manager = SVGManager()

for path in icons_paths:
    svg_manager.add_icon(path)
