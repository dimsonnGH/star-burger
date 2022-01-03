from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


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
    def orders_with_restaurants(self):
        menu_items = RestaurantMenuItem.objects.select_related('restaurant').all()
        orders = self.prefetch_related('order_items')
        for order in orders:
            order_sum = 0
            order_restaurants = set()
            for order_item in order.order_items.all():
                order_sum += order_item.price * order_item.quantity
                item_restaurants = []
                for menu_item in menu_items:
                    if menu_item.product_id == order_item.product_id and menu_item.availability:
                        item_restaurants.append(menu_item.restaurant)
                if order_restaurants:
                    order_restaurants = order_restaurants & set(item_restaurants)
                else:
                    order_restaurants = set(item_restaurants)
            order.order_sum = order_sum
            order.restaurants = order_restaurants

        return orders

    def orders_with_price(self):
        orders = self.annotate(order_sum=Sum(F('order_items__price') * F('order_items__quantity')))
        return orders


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('CLOSED', 'Закрыт')
    ]
    ORDER_PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Картой'),
        ('CASH', 'Наличными')
    ]

    id = models.AutoField(verbose_name='№', primary_key=True)
    firstname = models.CharField('имя', max_length=50)
    lastname = models.CharField('фамилия', max_length=100)
    phonenumber = PhoneNumberField('номер телефона')
    address = models.CharField('адрес', max_length=500)
    created = models.DateTimeField('дата создания', default=timezone.now, db_index=True)
    call_date = models.DateTimeField('дата звонка', blank=True, null=True)
    delivery_date = models.DateTimeField('дата доставки', blank=True, null=True)
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='NEW',
                              db_index=True, verbose_name='Статус заказа')
    payment_method = models.CharField(max_length=15, choices=ORDER_PAYMENT_METHOD_CHOICES, blank=True,
                                      verbose_name='Способ оплаты')
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
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', verbose_name='заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items', verbose_name='товар')
    quantity = models.SmallIntegerField('количество', validators=[MinValueValidator(1)])
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f'заказ {self.order.id} - {self.product}: {self.quantity}'

    class Meta():
        verbose_name = 'пункт заказа'
        verbose_name_plural = 'пункты заказа'
