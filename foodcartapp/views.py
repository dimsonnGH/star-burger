import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    try:
        request_parameters = json.loads(request.body.decode())
    except ValueError:
        return Response({
            'error': 'Не верный формат данных заказа',
        })

    if not 'products' in request_parameters:
        return Response({'error': 'products key is not presented'})

    if not isinstance(request_parameters['products'], list):
        return Response({'error': 'products key is not a list'})

    if len(request_parameters['products']) == 0:
        return Response({'error': 'products key is empty'})

    order = Order.objects.create(
        firstname=request_parameters['firstname'],
        lastname=request_parameters['lastname'],
        phonenumber=request_parameters['phonenumber'],
        address=request_parameters['address']
    )
    for item_parameters in request_parameters['products']:
        order_item = OrderItem.objects.create(
            order=order,
            product=Product.objects.get(pk=item_parameters['product']),
            quantity=item_parameters['quantity']
        )
    return Response({})
