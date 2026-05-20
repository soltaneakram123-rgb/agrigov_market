from django.db import migrations


PRODUCT_TYPES = [
    # (name, name_ar, category, image_url)
    ("Tomato",      "طماطم",     "vegetables", "https://images.unsplash.com/photo-1607305387299-a3d9611cd469?w=400&auto=format"),
    ("Potato",      "بطاطا",     "vegetables", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400&auto=format"),
    ("Onion",       "بصل",       "vegetables", "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400&auto=format"),
    ("Carrot",      "جزرة",      "vegetables", "https://images.unsplash.com/photo-1447175008436-054170c2e979?w=400&auto=format"),
    ("Pepper",      "فلفل",      "vegetables", "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&auto=format"),
    ("Zucchini",    "كوسة",      "vegetables", "https://images.unsplash.com/photo-1554568218-0f1715e72254?w=400&auto=format"),
    ("Eggplant",    "باذنجان",   "vegetables", "https://images.unsplash.com/photo-1603048297172-c92544798d5a?w=400&auto=format"),
    ("Cucumber",    "خيار",      "vegetables", "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=400&auto=format"),
    ("Cabbage",     "ملفوف",     "vegetables", "https://images.unsplash.com/photo-1594282486552-05b4d80fbb9f?w=400&auto=format"),
    ("Lettuce",     "خس",        "vegetables", "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&auto=format"),
    ("Garlic",      "ثوم",       "vegetables", "https://images.unsplash.com/photo-1501420193893-eba33e2e0c0d?w=400&auto=format"),
    ("Orange",      "برتقال",    "fruits",     "https://images.unsplash.com/photo-1547514701-42782101795e?w=400&auto=format"),
    ("Apple",       "تفاح",      "fruits",     "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&auto=format"),
    ("Watermelon",  "بطيخ",      "fruits",     "https://images.unsplash.com/photo-1571575173700-afb9492e6a50?w=400&auto=format"),
    ("Grapes",      "عنب",       "fruits",     "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=400&auto=format"),
    ("Dates",       "تمر",       "fruits",     "https://images.unsplash.com/photo-1561190928-8f674e1ba444?w=400&auto=format"),
    ("Fig",         "تين",       "fruits",     "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=400&auto=format"),
    ("Peach",       "خوخ",       "fruits",     "https://images.unsplash.com/photo-1595743825637-cdafc8ad4173?w=400&auto=format"),
    ("Wheat",       "قمح",       "grains",     "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&auto=format"),
    ("Barley",      "شعير",      "grains",     "https://images.unsplash.com/photo-1600688640154-9619e002df30?w=400&auto=format"),
    ("Corn",        "ذرة",       "grains",     "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&auto=format"),
    ("Lentils",     "عدس",       "legumes",    "https://images.unsplash.com/photo-1585564816619-f7e2228f1cdf?w=400&auto=format"),
    ("Chickpeas",   "حمص",       "legumes",    "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?w=400&auto=format"),
    ("Mint",        "نعناع",     "herbs",      "https://images.unsplash.com/photo-1628556270448-4d4e4148e1b1?w=400&auto=format"),
    ("Parsley",     "بقدونس",    "herbs",      "https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=400&auto=format"),
]


def seed_product_types(apps, schema_editor):
    ProductType = apps.get_model('products', 'ProductType')
    for name, name_ar, category, image_url in PRODUCT_TYPES:
        ProductType.objects.get_or_create(
            name=name,
            defaults={
                'name_ar':   name_ar,
                'category':  category,
                'image_url': image_url,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_producttype'),
    ]

    operations = [
        migrations.RunPython(seed_product_types, migrations.RunPython.noop),
    ]
