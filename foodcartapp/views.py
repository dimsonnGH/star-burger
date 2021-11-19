import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Order, OrderItem
import phonenumbers


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

    required_params = 'products,firstname,lastname,phonenumber,address'.split(',')
    invalid_params = [param for param in required_params if not param in request_parameters]
    if invalid_params:
        return Response({'error': f'{", ".join(invalid_params)} keys is not presented'})

    type_checking_list = [
        (list, 'products'),
        (str, 'firstname,lastname,phonenumber,address')
    ]
    for checking_type, str_checking_params in type_checking_list:
        checking_params = str_checking_params.split(',')
        invalid_params = [param for param in checking_params if
                          not isinstance(request_parameters[param], checking_type)]
        if invalid_params:
            return Response({'error': f'{", ".join(invalid_params)} keys is not a {checking_type}'})

    invalid_params = [param for param in required_params if not request_parameters[param]]
    if invalid_params:
        return Response({'error': f'{", ".join(invalid_params)} keys is empty'})

    phonenumber = request_parameters['phonenumber']
    parced_phonenumber = phonenumbers.parse(phonenumber, 'RU')
    if not phonenumbers.is_valid_number(parced_phonenumber):
        return Response({'error': f'{phonenumber} keys is not valid phone number'})

    for item_parameters in request_parameters['products']:
        product_id = item_parameters['product']
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': f'Product with {product_id} id is not exists'})
        item_parameters['product_object'] = product

    order = Order.objects.create(
        firstname=request_parameters['firstname'],
        lastname=request_parameters['lastname'],
        phonenumber=request_parameters['phonenumber'],
        address=request_parameters['address']
    )
    for item_parameters in request_parameters['products']:
        order_item = OrderItem.objects.create(
            order=order,
            product=item_parameters['product_object'],
            quantity=item_parameters['quantity']
        )
    return Response({})
