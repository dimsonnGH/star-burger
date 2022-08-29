from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from geopy import distance
from coordinates.geocoder_functions import get_address_coordinates, Location


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                .filter(availability=True)
                .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def calculate_order_sum(self):
        orders = self.prefetch_related('items').annotate(order_sum=Sum(F('items__quantity') * F('items__price')))
        return orders

    def include_available_restaurants(self):
        menu_items = RestaurantMenuItem.objects.select_related('restaurant').filter(availability=True)
        orders = self.prefetch_related('items')

        addresses = [order.address for order in orders]
        addresses = addresses + [restaurant.address for restaurant in Restaurant.objects.all()]

        locations = Location.objects.filter(address__in=set(addresses))
        cache_of_coordinates = {location.address: (location.longitude, location.latitude) for location in locations}

        for order in orders:
            order_restaurants = set()
            restaurants_with_distance = []
            restaurants_with_unknown_distance = []
            order_address_coordinates, cache_of_coordinates = get_address_coordinates(order.address,
                                                                                      cache_of_coordinates)

            order_items = order.items.all()
            for order_item in order_items:
                item_restaurants = [menu_item.restaurant for menu_item in menu_items if
                                    menu_item.product_id == order_item.product_id]
                if order_restaurants:
                    order_restaurants = order_restaurants & set(item_restaurants)
                else:
                    order_restaurants = set(item_restaurants)

            for restaurant in order_restaurants:
                restorant_coordinates, cache_of_coordinates = get_address_coordinates(restaurant.address,
                                                                                      cache_of_coordinates)
                if order_address_coordinates and restorant_coordinates:
                    distance_to = round(distance.distance(restorant_coordinates, order_address_coordinates).km, 2)
                    restaurants_with_distance.append((restaurant, distance_to))
                else:
                    restaurants_with_unknown_distance.append((restaurant, None))

            order.restaurants = sorted(restaurants_with_distance, key=lambda item: item[1]) \
                                + restaurants_with_unknown_distance
            order.restaurants_count = len(order.restaurants)

        return orders


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('CLOSED', 'Закрыт')
    ]
    ORDER_PAYMENT_METHOD_CHOICES = [
        ('UNDEFINED', 'Не известен'),
        ('CARD', 'Картой'),
        ('CASH', 'Наличными')
    ]

    # переопределяем поле id, чтобы установить свой заголовок в админке
    id = models.AutoField(verbose_name='№', primary_key=True)
    firstname = models.CharField('имя', max_length=50)
    lastname = models.CharField('фамилия', max_length=100)
    phonenumber = PhoneNumberField('номер телефона', db_index=True)
    address = models.CharField('адрес', max_length=500)
    created_at = models.DateTimeField('дата создания', default=timezone.now, db_index=True)
    called_at = models.DateTimeField('дата звонка', blank=True, null=True)
    delivered_at = models.DateTimeField('дата доставки', blank=True, null=True)
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='NEW',
                              db_index=True, verbose_name='Статус заказа')
    payment_method = models.CharField(max_length=15, choices=ORDER_PAYMENT_METHOD_CHOICES, blank=False,
                                      default='UNDEFINED', verbose_name='Способ оплаты')
    comment = models.TextField('комментарий', blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, verbose_name='ресторан',
                                   related_name='orders', blank=True, null=True)
    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'№{self.id} - {self.lastname} {self.phonenumber}'

    class Meta():
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class OrderItem(models.Model):
    """Позиция заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name='товар')
    quantity = models.SmallIntegerField('количество', validators=[MinValueValidator(1)])
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f'заказ {self.order.id} - {self.product}: {self.quantity}'

    class Meta():
        verbose_name = 'пункт заказа'
        verbose_name_plural = 'пункты заказа'
