console.log("Product script working")

/**
 * Cookies
 *  */



function getCookie(name) {
    if (!document.cookie) {
        return null; // Return early if no cookies are present
    }

    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();

        if (cookie.substring(0, name.length + 1) === (name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }

    return null; // Return null if the cookie was not found
}

function navigateTo(url) {
    window.location.href = url;  // Navigate to the specified URL
}

/**
 * Cookies
 *  */
////////////////////////////////////////////////////


console.log('productDetail');
const control1Element = document.querySelector("#quantity_control_1");
const control0Element = document.querySelector("#quantity_control_0");
const inStockElement = document.querySelector("#in_stock");
const outOfStockElement = document.querySelector("#out_of_stock");
const fewStockElement = document.querySelector("#few_in_stock");
const toggleElement = document.querySelector("#button_toggle");
const quantityElement = document.querySelector('#quantity_total_2');
const totalAmountElement = document.getElementById("totalamount");
const summaryCartTotal = document.querySelector("#summary_totalamount");
const variantElement = document.querySelector("#vid");
const addTocartElement = document.getElementById("add_to_cart_btn");

var refreshDetail = function() {
    if ( $.fn.elevateZoom ) {
        $('#product-zoom').elevateZoom({
            gallery:'product-zoom-gallery',
            galleryActiveClass: 'active',
            zoomType: "inner",
            cursor: "crosshair",
            zoomWindowFadeIn: 400,
            zoomWindowFadeOut: 400,
            responsive: true
        });

        // On click change thumbs active item
        $('.product-gallery-item').on('click', function (e) {
            $('#product-zoom-gallery').find('a').removeClass('active');
            $(this).addClass('active');

            e.preventDefault();
        });

        var ez = $('#product-zoom').data('elevateZoom');

        // Open popup - product images
        $('#btn-product-gallery').on('click', function (e) {
            if ( $.fn.magnificPopup ) {
                $.magnificPopup.open({
                    items: ez.getGalleryList(),
                    type: 'image',
                    gallery:{
                        enabled:true
                    },
                    fixedContentPos: false,
                    removalDelay: 600,
                    closeBtnInside: false
                }, 0);

                e.preventDefault();
            }
        });
    }
}




//PRODUCT ADD TO CART FROM DETAIL PAGE//
async function addToCart() {
    const cartButton = document.querySelector('.cart-btn');
    cartButton.innerHTML = `<div class='loader'></div>`;
    let variantId = document.getElementById("variant").value || null;
    let productId = document.getElementById("productId").value;
    const token = getCookie('csrftoken');

    try {
        const response = await fetch(`/addtocart/${productId}/`, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            body: JSON.stringify({ variant_id: variantId, product_id: productId }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        console.log(data);

        cartButton.innerHTML = `<div class='loader'></div>`;

        control0Element.classList.add("hidden");
        control1Element.classList.remove("hidden");
        toggleElement.classList.add("hidden");
        document.querySelector(".quantity_total_").value = data.added_quantity;
        document.querySelector("#quantity_total_").value = data.added_quantity;
        document.getElementById("cart_count").innerHTML = data.cart_count;
        cartButton.innerHTML = `Add to Cart`;

        const message = 'Product added to cart!',
        icon = 'success';
        alertG(message, icon)

    } catch (error) {
        cartButton.innerHTML = `Add to Cart`;
        const message = error,
        icon = 'error';
        alertG(message, icon)
    }
}
//PRODUCT ADD TO CART FROM DETAIL PAGE//


//PRODUCT BUY NOW//
async function buyNow() {
    let variantId = document.getElementById("variant").value || null;
    let productId = document.getElementById("productId").value;
    const token = getCookie('csrftoken');

    const response = await fetch(`/buy-now/${productId}/`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": token,
        },
        body: JSON.stringify({ variant_id: variantId, product_id: productId }),
    });

    const data = await response.json();

    if (data.redirect_url) {
        window.location.href = data.redirect_url;
    }
}



async function myFunction() {
    const gallery = document.querySelector("#ajax_gallery");
    const variantId = document.getElementById("mySelect").value;
    const productId = document.getElementById("productId").value;
    const token = getCookie('csrftoken');
    const url = '/variant-fetch/';

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            body: JSON.stringify({ variant_id: variantId, product_id: productId }),
        });

        const data = await response.json();

        if (response.ok) {
            updateGallery(gallery, data.thumbnail);
            updateUrlParam('variantid', data.new.sku);
            updateVariantDetails(data.new);
            // updateCartControl(data.new.control);
            document.querySelector("#variant").value = data.new.id;

            const control0Element = document.querySelector("#quantity_control_0");
            const control1Element = document.querySelector("#quantity_control_1");
            const toggleElement = document.querySelector("#button_toggle");

            if (data.new.control === 1) {
                control0Element.classList.add("hidden");
                control1Element.classList.remove("hidden");
                toggleElement.classList.add("hidden");
            } else {
                control0Element.classList.remove("hidden");
                control1Element.classList.add("hidden");
                toggleElement.classList.add("hidden");
            }

            console.log(data);
        } else {
            console.error('Error:', data);
        }

    } catch (error) {
        console.error('Fetch error:', error);
    }
}

function updateGallery(gallery, thumbnail) {
    gallery.innerHTML = thumbnail;
}


function updateVariantDetails(variant) {
    const selectedVariantName = variant.name;
    document.getElementById("variant").value = variant.id;
    document.getElementById("price").innerHTML = `${variant.price}`;
    document.getElementById("selected_variant").innerHTML = selectedVariantName;
    document.querySelector("#quantity_total_").value = variant.quantity;
}



function updateCartControl(control) {
    const control0Element = document.querySelector("#quantity_control_0");
    const control1Element = document.querySelector("#quantity_control_1");
    const toggleElement = document.querySelector("#button_toggle");

    if (control === 1) {
        control0Element.classList.add("hidden");
        control1Element.classList.remove("hidden");
        toggleElement.classList.add("hidden");
    } else {
        control0Element.classList.remove("hidden");
        control1Element.classList.add("hidden");
        toggleElement.classList.add("hidden");
    }
}


function activeClass() {
    var elements = document.getElementsByClassName("child");
    for (var i = 0; i < elements.length; i++)
    {
        elements[i].onclick = function(){
            
            var el = elements[0];
            while(el)
            {
                if(el.tagName === "A"){
                    el.classList.remove("active");
                }
                el = el.nextSibling;
            }

            this.classList.add("active");
        };
    }
}

async function myFunc(id) {
    const gallery = document.querySelector("#ajax_gallery");
    const productId = document.getElementById("productId").value;
    const token = getCookie('csrftoken');

    try {
        const response = await fetch('/variant-fetch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            body: JSON.stringify({ variant_id: id, product_id: productId }),
        });

        const data = await response.json();

        if (response.ok) {
            updateGallery(gallery, data.thumbnail);
            updateUrlParam('variantid', data.new.sku);
            refreshDetail();
            updateVariantDetails(data.new);
            // updateCartControl(data.new.control);
            activeClass();
            document.querySelector("#variant").value = data.new.id;
            const control0Element = document.querySelector("#quantity_control_0");
            const control1Element = document.querySelector("#quantity_control_1");
            const toggleElement = document.querySelector("#button_toggle");

            if (data.new.control === 1) {
                control0Element.classList.add("hidden");
                control1Element.classList.remove("hidden");
                toggleElement.classList.add("hidden");
            } else {
                control0Element.classList.remove("hidden");
                control1Element.classList.add("hidden");
                toggleElement.classList.add("hidden");
            }

        } else {
            console.error('Error:', data);
        }


    } catch (error) {
        console.error('Error fetching variant data:', error);
    }
}


function updateUrlParam(key, value) {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set(key, value);
    window.history.replaceState(null, null, currentUrl);
}

function updateStockStatus(stock) {
    const defaultConfig = document.getElementById("default_config");
    const inStockElement = document.getElementById("in_stock");
    const outOfStockElement = document.getElementById("out_of_stock");
    const fewStockElement = document.getElementById("few_stock");
    const stockCountElement = document.getElementById("stock_count");

    if (stock > 10) {
        defaultConfig.classList.add("hidden");
        inStockElement.classList.remove("hidden");
        outOfStockElement.classList.add("hidden");
        fewStockElement.classList.add("hidden");
    } else if (stock < 1) {
        defaultConfig.classList.add("hidden");
        outOfStockElement.classList.remove("hidden");
        inStockElement.classList.add("hidden");
        fewStockElement.classList.add("hidden");
    } else {
        fewStockElement.classList.remove("hidden");
        outOfStockElement.classList.add("hidden");
        inStockElement.classList.add("hidden");
        defaultConfig.classList.add("hidden");
        stockCountElement.innerHTML = stock + " items in stock";
    }
}


//PRODUCT INCREASE ON DETAIL PAGE//
async function increaseQuantity() {
    const plusButton = document.querySelector('.plus-button');
    plusButton.innerHTML = `<div class='loader'></div>`;
    
    const productId = document.getElementById("productId").value;
    const variantId = document.getElementById("variant").value || null;
    const token = getCookie('csrftoken');

    console.log("Product id:", productId);
    console.log("Variant id:", variantId);

    try {
        const response = await fetch('/increase/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            body: JSON.stringify({ variant_id: variantId, product_id: productId }),
        });

        const data = await response.json();

        if (response.ok) {
            plusButton.innerHTML = `<i class="icon-plus"></i>`;
            updateCartDetails(data);
            const message = 'Product quantity was increased!',
            icon = 'success';
            alertG(message, icon)
        } else {
            const message = 'Could not increase quantity!',
            icon = 'error';
            alertG(message, icon)
            showError(data.message || 'An error occurred while increasing the quantity.');
        }
    } catch (error) {
        const message = 'Could not increase quantity!',
        icon = 'error';
        alertG(message, icon)
        showError('An error occurred while increasing the quantity.');
    }
}

function showError(message) {
    const errorElement = document.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        setTimeout(() => errorElement.classList.add('hidden'), 3000);
    } else {
        alert(message);
    }
}
//PRODUCT INCREASE ON DETAIL PAGE//


//PRODUCT DECREASE ON DETAIL PAGE//
async function decreaseQuantity() {
    const minusButton = document.querySelector('.minus-button');
    minusButton.innerHTML = `<div class='loader'></div>`;
    const productId = document.getElementById("productId").value;
    const variantId = document.getElementById("variant").value || null;
    const token = getCookie('csrftoken');

    try {
        const response = await fetch('/decrease/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            body: JSON.stringify({ variant_id: variantId, product_id: productId }),
        });

        const data = await response.json();

        if (response.ok) {
            minusButton.innerHTML = `<i class="icon-minus"></i>`;
            updateCartDetails(data);
            updateControls(data);
            const message = 'Product quantity was decreased!',
            icon = 'success';
            alertG(message, icon)
        } else {
            const message = 'Could not decrease quantity!',
            icon = 'success';
            alertG(message, icon)
            showError(data.message || 'An error occurred while decreasing the quantity.');
        }
    } catch (error) {
        showError('An error occurred while decreasing the quantity.');
    }
}

function updateControls(data) {
    if (data.added_quantity < 1) {
        toggleElement.classList.add("hidden");
        control0Element.classList.remove("hidden");
        control1Element.classList.add("hidden");
    }
}

function showError(message) {
    const errorElement = document.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        setTimeout(() => errorElement.classList.add('hidden'), 3000);
    } else {
        alert(message);
    }
}
//PRODUCT DECREASE ON DETAIL PAGE//



function updateCartDetails(data) {
    document.getElementById("cart_count").innerHTML = data.cart_count;
    document.querySelector(".quantity_total_").value = data.added_quantity;
    document.querySelector("#quantity_total_").value = data.added_quantity;
}

//QUANTITY BUTTON ADJUSTMENT
$(document).ready(function(){
    $('.input-counter').each(function() {
        var spinner = jQuery(this),
        input = spinner.find('input[type="text"]'),
        btnUp = spinner.find('.plus-button'),
        btnDown = spinner.find('.minus-button'),
        min = input.attr('min'),
        max = input.attr('max');
        btnUp.on("click", function(e) {
            e.preventDefault();

            var oldValue = parseFloat(input.val());
            if (oldValue >= max) {
                var newVal = oldValue;
            }else {
                var newVal = oldValue + 1;
            }
            spinner.find("input").val(newVal);
            spinner.find("input").trigger("change");
        });

        btnDown.on("click", function(e) {
            e.preventDefault();

            var oldValue = parseFloat(input.val());
            if (oldValue <= min) {
                var newVal = oldValue;
            }else {
                var newVal = oldValue - 1;
            }
            spinner.find("input").val(newVal);
            spinner.find("input").trigger("change");
            
        });

    });

    /**
     * Cart quantity Update 
     */
    $('.updateQuantity').click(function (e){
        e.preventDefault();

        var cart_id = $(this).closest('.allData').find('.cartId').val();
        var product_id = $(this).closest('.allData').find('.productId').val();
        var variant_id = $(this).closest('.allData').find('.variantId').val()||null;
        var quantity = $(this).closest('.allData').find('.quantity_total_').val();
        var token = getCookie('csrftoken');

        console.log(cart_id,product_id,variant_id,quantity,token);

        $.ajax({
            method: 'POST',
            url: '/update',
            data: {
                'cart_id': cart_id,
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity,
                csrfmiddlewaretoken : document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            success: function(response) {
                console.log(response);
                document.getElementById("cart_count").innerHTML = response.cart_count;
                document.querySelector(".summary_totalamount").innerHTML = response.total;
                document.querySelector("#packaging_fee").innerHTML = response.total_packaging_fee;
                document.getElementById("totalamount").innerHTML = response.total;
                const message = 'Product quantity updated successfully',
                icon = 'success';
                alertG(message, icon)

            }
        });
    });

    ///////////// ADD TO CART FROM ANYWHERE //////////////////

    $('.add-to-cart-form').on('submit', function(event) {
        event.preventDefault();  // Prevent the form from submitting the traditional way

        var form = $(this);
        var formData = form.serialize();  // Serialize the form data

        $.ajax({
            url: form.attr('action'),  // The URL to send the request to
            type: 'POST',
            data: formData,
            success: function(response) {
                alert(response.message);
                $('#cart-item-count').text(response.cart_item_count);  // Update the cart item count
            },
            error: function(response) {
                alert('An error occurred. Please try again.');
            }
        });
    });
    ///////////// ADD TO CART FROM ANYWHERE //////////////////


    $('.checking').change(function (e){
        e.preventDefault();

        var cart_id = $(this).closest('.allData').find('.cartId').val();
        var value = $(this).closest('.allData').find('.value');
        var token = getCookie('csrftoken');

        if ($(this).is(':checked')) {
            console.log("Hi there");
            num = 1
        }else{
            num = 0
            console.log("Eyy boys no no");
        }

        console.log(value);
        console.log(cart_id);
        
        $.ajax({
            method: 'POST',
            url: '/check',
            data: {
                'cart': cart_id,
                'value': num,
                csrfmiddlewaretoken : document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            success: function(response) {
                console.log(response);
                document.getElementById("cart_count").innerHTML = response.data.cart_count;
                document.querySelector(".summary_totalamount").innerHTML = response.data.total;
                document.getElementById("totalamount").innerHTML = response.data.total;

            }
        });
    });

    $(document).on('change', '#post-form', function(e){
        console.log("hi");
        var token = getCookie('csrftoken');
        size_id = document.querySelector('#size').value;
        product_id = document.querySelector('#productid').value;
        e.preventDefault();
        $.ajax({
            method: $(this).attr("method"),
            type:"POST",
            url:'/ajaxcolor',
            data:{
                productid: product_id,
                size: size_id,
                csrfmiddlewaretoken: document.querySelector("input[name='csrfmiddlewaretoken']").value,
                action:'post'
            },
            dataType :"json",
            action:"post",
            success: function(response){
                $('#appendHere').html(response.rendered_table);
                $('.appendHere').html(response.rendered_table);
            },
            error: function (data) {
                alert("Got an error Dude " + data);
            }
        });
    });

 
});
//QUANTITY BUTTON ADJUSTMENT

//DELETE CART ITEM FROM CART PAGE//

////////////////////////////////////
async function changeCurrency(currency) {
    try {
        const response = await fetch(`/c/converter/${currency}/`);
        const data = await response.json();
        if (!data.error) {
            console.log(data);
            updatePrices(data.rate, currency);
        } else {
            console.error('Error fetching the conversion rate');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function updatePrices(rate, currencyCode) {
    const currencySymbols = {
        'USD': 'USD',
        'GHS': 'GHS',
        'EUR': 'EUR',
    };
    const symbol = currencySymbols[currencyCode] || '';

    document.querySelectorAll('.product-price').forEach(elem => {
        const newPriceElem = elem.querySelector('.new-price');
        const oldPriceElem = elem.querySelector('.old-price');
        
        const newBasePrice = parseFloat(newPriceElem.getAttribute('data-base-price'));
        const oldBasePrice = parseFloat(oldPriceElem.getAttribute('data-base-price'));

        if (!isNaN(newBasePrice)) {
            newPriceElem.innerText = `${symbol}${(newBasePrice * rate).toFixed(2).toLocaleString()}`;
        } else {
            console.error('Invalid new base price:', newBasePrice);
        }

        if (!isNaN(oldBasePrice)) {
            oldPriceElem.innerText = `Was ${symbol}${(oldBasePrice * rate).toFixed(2).toLocaleString()}`;
        } else {
            console.error('Invalid old base price:', oldBasePrice);
        }
    });
}
////////////////////////////////////


function clearRecentlyViewed() {
    fetch('/p/clear/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector("input[name='csrfmiddlewaretoken']").value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            // Reload the page after successfully clearing the cookies
            document.querySelector('#the_products').classList.add('hidden');
            document.querySelector('#no_products').classList.remove('hidden');
            const message = 'Recently viewed products deleted',
            icon = 'success';
            alertG(message, icon);
            // location.reload();
        } else {
            console.error('Failed to clear recently viewed products');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


//////////////////ALERT FUNCTION///////////////////
function alertG(message, icon) {
    const Toast = Swal.mixin({
        toast: true,
        position: "top-end",
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        }
    });
    Toast.fire({
        icon: icon,
        title: message,
    });
}


/////////////////// DELETE CARTITEM//////////////////////
async function deleteCartItem(id) {
    var token = getCookie('csrftoken');
    const response = await fetch(`/deletecart/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
        },
        body: JSON.stringify({ cart_id : id})
    });

    const data = await response.json();

    if (response.ok) {
        console.log(data);
        document.getElementById("cartdiv-" + data.id).outerHTML = "";
        document.getElementById("cart_count").innerHTML = data.cart_count;
        document.querySelector("#packaging_fee").innerHTML = data.total_packaging_fee;
        document.querySelector(".summary_totalamount").innerHTML = data.total;

        // document.getElementById("totalamount").innerHTML = "₵" + data.total + ".00";
        if (data.cart_count < 1) {
            document.getElementById("cart_items").classList.add("hidden");
            document.querySelector("#summary_card").classList.add("hidden");
            document.querySelector("#empty_cart").classList.remove("hidden");
        }
        const success = 'success';
        alertG(data.message, success)

    } else {
        const success = 'error';
        alertG(response.error, success)
        
    }
}
/////////////////// DELETE CARTITEM//////////////////////


async function deleteAddress(id) {
    var token = getCookie('csrftoken');
    const response = await fetch(`/deleteaddress/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
        },
        body: JSON.stringify({ address_id : id})
    });

    const data = await response.json();
    console.log(data);
    document.getElementById("address-" + data.id).outerHTML = "";
}

//DELETE CART ITEM FROM CART PAGE//

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
////////////////////////////////////////////////////

////////////////////////////////////////////////////
let device = getCookie('device')
if (device == null || device == undefined){
    device = uuidv4()
}

document.cookie ='device=' + device + ";domain=;path=/"
////////////////////////////////////////////////////


const rangeInput = document.querySelectorAll(".range-input input"),
  priceInput = document.querySelectorAll(".price-input input"),
  range = document.querySelector(".slider .progress");
    

// let priceGap = document.getElementById('gapp').value;
let priceGap = 10;

priceInput.forEach((input) => {
  input.addEventListener("input", (e) => {
    let minPrice = parseInt(priceInput[0].value),
      maxPrice = parseInt(priceInput[1].value);

    if (maxPrice - minPrice >= priceGap && maxPrice <= rangeInput[1].max) {
      if (e.target.className === "input-min") {
        rangeInput[0].value = minPrice;
        range.style.left = (minPrice / rangeInput[0].max) * 100 + "%";
      } else {
        rangeInput[1].value = maxPrice;
        range.style.right = 100 - (maxPrice / rangeInput[1].max) * 100 + "%";
      }
    }
  });
});

rangeInput.forEach((input) => {
  input.addEventListener("input", (e) => {
    let minVal = parseInt(rangeInput[0].value),
      maxVal = parseInt(rangeInput[1].value);

    if (maxVal - minVal < priceGap) {
      if (e.target.className === "range-min") {
        rangeInput[0].value = maxVal - priceGap;
      } else {
        rangeInput[1].value = minVal + priceGap;
      }
    } else {
      priceInput[0].value = minVal;
      priceInput[1].value = maxVal;
      range.style.left = (minVal / rangeInput[0].max) * 100 + "%";
      range.style.right = 100 - (maxVal / rangeInput[1].max) * 100 + "%";
    }
  });
});

$(document).ready(function () {
    // Function to get user's current location
    function getLocation(callback) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function (position) {
                callback(position.coords.latitude, position.coords.longitude);
            }, function (error) {
                console.log('Error occurred. Error code: ' + error.code);
                callback(null, null);
            });
        } else {
            console.log("Geolocation is not supported by this browser.");
            callback(null, null);
        }
    }

    // Handle form submission
    $('#vendorSignupForm').submit(function (e) {
        e.preventDefault();
        // Clear previous error messages
        $('#errorMessages').empty();

        // Get form data
        var formData = new FormData(this);

        // Get location and submit form
        getLocation(function (latitude, longitude) {
            if (latitude && longitude) {
                formData.append('latitude', latitude);
                formData.append('longitude', longitude);
            }

            $.ajax({
                url: $(this).attr('action'),
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-CSRFToken': document.querySelector("input[name='csrfmiddlewaretoken']").value,  // Make sure CSRF token is included
                },
                success: function (response) {
                    $('#errorMessages').append('<p>' + response[field][0] + '</p>');
                    console.log(response);

                },
                error: function (response) {
                    // Handle errors
                    var errors = response.responseJSON.errors;
                    for (var field in errors) {
                        if (errors.hasOwnProperty(field)) {
                            $('#errorMessages').append('<p>' + errors[field][0] + '</p>');
                        }
                    }
                }
            });
        });
    });

    // JavaScript to handle Save for Later functionality for multiple products

    $('.save-for-later').on('click', function(event) {
        event.preventDefault();  // Prevent default form submission

        var productId = $(this).data('product-id');  // Get product ID from data attribute
        var variantId = $(this).data('variant-id');  // Get variant ID from data attribute
        var cartId = $(this).data('cart-id');  // Get variant ID from data attribute
        console.log(productId);
        console.log(variantId);
        console.log(cartId);

        // AJAX request to Django view
        $.ajax({
            type: 'POST',
            url: '/cart/save-for-later/',
            data: {
                'product_id': productId,
                'variant_id': variantId,
                'cart_id': cartId,
                'csrfmiddlewaretoken': document.querySelector("input[name='csrfmiddlewaretoken']").value,
            },
            success: function(response) {
                // Remove the specific product from the cart UI
                document.getElementById("cartdiv-" + cartId).outerHTML = "";
                document.getElementById("cart_count").innerHTML = response.cart_count;
                document.querySelector("#packaging_fee").innerHTML = response.total_packaging_fee;
                document.querySelector(".summary_totalamount").innerHTML = response.total;
                if (response.cart_count < 1) {
                    document.getElementById("cart_items").classList.add("hidden");
                    document.querySelector("#summary_card").classList.add("hidden");
                    document.querySelector("#empty_cart").classList.remove("hidden");
                }
                const success = 'success',
                message = 'Product saved for later';
                alertG(message, success)
            },
            error: function(xhr, status, error) {
                console.error('Error saving product for later:', error);
                const message = 'Error saving product for later:' +  error;
                icon = 'error';
                alertG(message, icon)
            }
        });
    });

});

