from PIL import Image, ImageDraw

COLORS = {
    "parking_free":  "#22c55e",  # green-500
    "parking_busy":  "#ef4444",  # red-500
    "tl_red":        "#dc2626",
    "tl_yellow":     "#eab308",
    "tl_green":      "#16a34a",
    "tl_unknown":    "#94a3b8",
    "pothole":       "#7c2d12",  # темно-коричневий
    "bump":          "#f97316",  # оранж
    "car":           "#1d4ed8",  # синій
}


def make_circle(color: str, size: int = 14, border: str = "#0f172a", border_width: int = 2) -> Image.Image:
    """Кольоровий кружечок з обводкою."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=color,
        outline=border,
        width=border_width,
    )
    return img


def make_diamond(color: str, size: int = 14, border: str = "#0f172a", border_width: int = 2) -> Image.Image:
    """Ромб — для світлофорів."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    points = [
        (size // 2, 0),
        (size - 1, size // 2),
        (size // 2, size - 1),
        (0, size // 2),
    ]
    draw.polygon(points, fill=color, outline=border)
    return img


def make_triangle(color: str, size: int = 14, border: str = "#0f172a") -> Image.Image:
    """Трикутник — для дорожніх подій (ям/горбків)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    points = [
        (size // 2, 0),
        (size - 1, size - 1),
        (0, size - 1),
    ]
    draw.polygon(points, fill=color, outline=border)
    return img


def make_car(color: str = None, size: int = 22) -> Image.Image:
    """Машина — білий кружечок з кольоровим ядром."""
    color = color or COLORS["car"]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Білий ореол + темна обводка
    draw.ellipse((0, 0, size - 1, size - 1), fill="white", outline="#0f172a", width=2)
    # Внутрішнє кольорове ядро
    pad = 5
    draw.ellipse((pad, pad, size - 1 - pad, size - 1 - pad), fill=color)
    return img