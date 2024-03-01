from django.shortcuts import redirect, render, get_object_or_404
from .models import *
from django.contrib import messages
from django_daraja.mpesa.core import MpesaClient
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



# Create your views here.
def index(request):
    
    cart_id = request.session.get("cart_id", None)
    cart = Cart.objects.get(id=cart_id) if cart_id else None
    
    context = {'cart': cart}
    return render(request, 'ecom/index-3.html', context)

def shop(request):
    products = Product.objects.all().order_by("-id")
    categories = Category.objects.all()
    cart_id = request.session.get("cart_id")
    cart, created = Cart.objects.get_or_create(id=cart_id)

    return render(request, 'ecom/category-4cols.html', {
        'products': products,
        'categories': categories,
        'cart': cart, 
    })

def productdetails(request, slug):

    product = get_object_or_404(Product, slug=slug)
    context = {'product': product}

    return render(request, 'ecom/product.html', context)

def productadded(request):
    return render(request, 'ecom/product-added.html')

def add_to_cart(request, pro_id):
    product = get_object_or_404(Product, id=pro_id)
    add_product_to_cart(request, product)
    
    # Set a success message
    success_message = f"{product.name} added to cart successfully."
    messages.success(request, success_message)

    # Redirect the user to a relevant page (e.g., product detail or cart)
    return redirect('shop')


def add_product_to_cart(request, product):
    # Use session-based cart for both authenticated and non-authenticated users
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Cart.objects.get(id=cart_id)
    else:
        cart = Cart.objects.create(total=0)
        request.session['cart_id'] = cart.id    

    # Continue with the rest of the logic to update the cart and display success message

    rate = product.price
    quantity = 1

    cart_product, created = CartProduct.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'rate': rate, 'quantity': quantity, 'subtotal': rate * quantity}
    )

    if not created:
        cart_product.quantity += quantity
        cart_product.subtotal += rate * quantity
        cart_product.save()

    cart.total += rate * quantity
    cart.save()

def managecart(request, cp_id):
    action = request.GET.get('action')
    cp_obj = CartProduct.objects.get(id=cp_id)
    cart_obj = cp_obj.cart
    
    if action == "inc":
        cp_obj.quantity += 1
        cp_obj.subtotal += cp_obj.rate 
        cp_obj.save()
        cart_obj.total += cp_obj.rate  # Increment the cart total
        cart_obj.save()  # Save the changes to the cart

    elif action == "dcr":
        cp_obj.quantity -= 1
        cp_obj.subtotal -= cp_obj.rate
        cp_obj.save()
        cart_obj.total -= cp_obj.rate
        cart_obj.save()
        if cp_obj.quantity == 0:
            cp_obj.delete()

    elif action == "rmv":
        cart_obj.total -= cp_obj.subtotal
        cart_obj.save()
        cp_obj.delete()

    else:
        pass

    return redirect('my-cart')

def emptycart(request):
    cart_id = request.session.get('cart_id', None)
    if cart_id:
        # Use a different variable name, e.g., cart_instance
        cart_instance = get_object_or_404(Cart, id=cart_id)
        cart_instance.cartproduct_set.all().delete()
        cart_instance.total = 0
        cart_instance.save()
        
    return redirect('my-cart')    

def cart(request):

    cart_id = request.session.get("cart_id", None)
    cart = Cart.objects.get(id=cart_id) if cart_id else None
    
    context = {'cart': cart}
    
    return render(request, 'ecom/cart.html', context)
    

def checkout(request):
    cart_id = request.session.get("cart_id", None)
    cart = Cart.objects.get(id=cart_id) if cart_id else None
    
    context = {'cart': cart}

    if request.method == 'POST':
        # Process the form data and create an order
        ordered_by = request.POST.get('ordered_by')
        delivery_address = request.POST.get('delivery_address')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        order_notes = request.POST.get('order_notes')


        # Create an order
        order = Order(
            cart=cart,
            ordered_by=ordered_by,
            delivery_address=delivery_address,
            mobile=mobile,
            email=email,
            order_notes=order_notes,
            subtotal=cart.total,  
            discount=0, 
            total=cart.total,  
            # order_status='PENDING'  
        )
        order.save()

         
        cl = MpesaClient()
        # Use a Safaricom phone number that you have access to, for you to be able to view the prompt.
        phone_number = order.mobile
        amount = order.total
        account_reference = 'reference'
        transaction_desc = 'Description'
        callback_url = 'https://big-plums-tie.loca.lt/getconfirmation'
        response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
         
        print(response.json())
        # Optionally, you can clear the cart after creating the order
        cart.cartproduct_set.all().delete()
        cart.total = 0
        cart.save()

        del request.session['cart_id']

        # Check the response and handle accordingly
        if response.status_code == 200:
            # Payment request successful
            order.order_status = 'PAID'
            order.save()
            return redirect('checkout')
        else:
            # Payment request failed
            order.order_status = 'FAILED'
            order.save()
            return redirect('Order-fail')
        
        
    messages.success(request, "")
        
    return render(request, 'ecom/checkout.html', context)


def mpesa_callback(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))

            # Extract relevant details from the callback
            transaction_status = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            order_id = int(data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])[0].get('Value'))

            # Get the corresponding order from the database
            order = Order.objects.get(id=order_id)

            # Handle transaction status
            if transaction_status == '0':
                # Payment successfuldull-actors-cry.loca.lt
                order.order_status = 'PAID'
                order.save()
            else:
                # Payment failed or canceled
                order.order_status = 'FAILED'
                order.save()

            # Respond to Safaricom with an acknowledgment
            return JsonResponse({'ResultCode': '0', 'ResultDesc': 'Accepted'})

        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Error processing M-Pesa callback: {e}")

            # Respond to Safaricom with an error acknowledgment
            return JsonResponse({'ResultCode': '1', 'ResultDesc': 'Error'})

    else:
        # Respond to non-POST requests with an error acknowledgment
        return JsonResponse({'ResultCode': '1', 'ResultDesc': 'Error'})

def orderconfirm(request):
    return render(request, "ecom/order-confirmation.html")

def orderfailed(request):
    return render(request, "ecom/order-fail.html")
