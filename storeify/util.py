import csv

from storeify.db import get_db_session
from storeify.models import Product, Base


def load_test_data(filepath):
    with open(filepath) as csvf:
        # Open file and skip header row
        reader = csv.reader(csvf, delimiter=',', quotechar='"')
        next(reader)

        for row in reader:
            new_product = Product(
                title=row[0],
                price=row[1],
                currency=row[2],
                inventory_count=row[3],
                can_purchase=bool(int(row[4]))
            )

            get_db_session().add(new_product)
        get_db_session().commit()
