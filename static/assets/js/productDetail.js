
/**
 * Cookies
 *  */


function getCookie(name) {
    var cookieValue = null

    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';')

        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim()

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))

                break
            }
        }
    }

    return cookieValue
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



/*Product Details*/
var productDetails = function() {
    $('.product-image-slider').slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        arrows: false,
        fade: false,
        asNavFor: '.slider-nav-thumbnails',
    });

    $('.slider-nav-thumbnails').slick({
        slidesToShow: 6,
        slidesToScroll: 1,
        asNavFor: '.product-image-slider',
        dots: false,
        focusOnSelect: true,

        prevArrow: '<button type="button" class="slick-prev"><i class="fi-rs-arrow-small-left"></i></button>',
        nextArrow: '<button type="button" class="slick-next"><i class="fi-rs-arrow-small-right"></i></button>'
    });

    // Remove active class from all thumbnail slides
    $('.slider-nav-thumbnails .slick-slide').removeClass('slick-active');

    // Set active class to first thumbnail slides
    $('.slider-nav-thumbnails .slick-slide').eq(0).addClass('slick-active');

    // On before slide change match active thumbnail to current slide
    $('.product-image-slider').on('beforeChange', function(event, slick, currentSlide, nextSlide) {
        var mySlideNumber = nextSlide;
        $('.slider-nav-thumbnails .slick-slide').removeClass('slick-active');
        $('.slider-nav-thumbnails .slick-slide').eq(mySlideNumber).addClass('slick-active');
    });

    $('.product-image-slider').on('beforeChange', function(event, slick, currentSlide, nextSlide) {
        var img = $(slick.$slides[nextSlide]).find("img");
        $('.zoomWindowContainer,.zoomContainer').remove();
        if ($(window).width() > 468) {
            $(img).elevateZoom({
                zoomType: "inner",
                cursor: "crosshair",
                zoomWindowFadeIn: 500,
                zoomWindowFadeOut: 750
            });
        }
    });
    //Elevate Zoom
    if ($(".product-image-slider").length) {
        if ($(window).width() > 468) {
            $('.product-image-slider .slick-active img').elevateZoom({
                zoomType: "inner",
                cursor: "crosshair",
                zoomWindowFadeIn: 500,
                zoomWindowFadeOut: 750
            });
        }
    }
};


//PRODUCT ADD TO CART FROM DETAIL PAGE//
async function addToCart() {
    let x = document.getElementById("variant").value || null;
    let y = document.getElementById("productId").value;
    var token = getCookie('csrftoken');
    console.log(x);
    console.log(y);

    const response = await fetch(`/addtocart/${y}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": token,
        },
        body: JSON.stringify({ variant_id: x, product_id: y }),
    });

    const data = await response.json();
    console.log(data);

    control0Element.classList.add("hidden");
    control1Element.classList.remove("hidden");
    toggleElement.classList.add("hidden");
    document.querySelector(".quantity_total_").value = data.added_quantity;
    document.querySelector("#quantity_total_").value = data.added_quantity;
    document.getElementById("cart_count").innerHTML = data.cart_count;
    document.getElementById("totalamount").innerHTML = "₵" + data.total + ".00";


}
//PRODUCT ADD TO CART FROM DETAIL PAGE//



//VARIANT SELECTION FROM PRODUCT DETAIL PAGE//
async function myFunction() {
    let gallery = document.querySelector("#ajax_gallery");
    let x = document.getElementById("mySelect").value;
    let y = document.getElementById("productId").value;
    var token = getCookie('csrftoken');
    let urlpat = '/variant-fetch/'

    const response = await fetch(urlpat, {
        method: "POST",
        headers: {
            "X-CSRFToken": token,
        },
        body: JSON.stringify({ variant_id: x, product_id: y }),
    });
 
    const data = await response.json();

    gallery.innerHTML = '';
    gallery.innerHTML = data.thumbnail;

    //Load functions
    productDetails();

    selected = ''

    if (data.new.name == 'M') {
        selected = 'Medium'
    }  else if (data.new.name == 'L')  {
        selected = 'Large'
    }  else if (data.new.name == 'XL') {
        selected = 'Extra Large'
    } else {
        selected = data.new.name
    }

    if (data.new.stock > 10) {
        document.getElementById("default_config").classList.add("hidden")
        inStockElement.classList.remove("hidden")
        outOfStockElement.classList.add("hidden")
        fewStockElement.classList.add("hidden")
    } else if (data.new.stock < 1) {
        document.getElementById("default_config").classList.add("hidden")
        outOfStockElement.classList.remove("hidden")
        inStockElement.classList.add("hidden")
        fewStockElement.classList.add("hidden")
    } else {
        fewStockElement.classList.remove("hidden")
        outOfStockElement.classList.add("hidden")
        inStockElement.classList.add("hidden")
        document.getElementById("default_config").classList.add("hidden")
        document.getElementById("stock_count").innerHTML = data.new.stock + " items in stock";
    }

    console.log(data);
    console.log(data.new);
    console.log(data.thumbnail);
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('variantid', data.new.sku);
    window.history.replaceState(null, null, currentUrl)

    document.getElementById("variant").value = data.new.id;
    document.getElementById("price").innerHTML = "₵" + data.new.price + ".00";
    document.getElementById("selected_variant").innerHTML =  selected;
    document.querySelector("#quantity_total_").value = data.new.quantity;


    if (data.new.control == 1) {
        control0Element.classList.add("hidden")
        control1Element.classList.remove("hidden")
        toggleElement.classList.add("hidden")
    } else {
        toggleElement.classList.add("hidden")
        control0Element.classList.remove("hidden")
        control1Element.classList.add("hidden")
    }

    if (data.new.control == 1) {
        document.querySelector("#quantity_control_1").classList.remove("hidden")
        document.querySelector("#quantity_control_0").classList.add("hidden")
        document.querySelector("#button_toggle").classList.add("hidden")
    } else {
        document.querySelector("#quantity_control_1").classList.add("hidden")
        document.querySelector("#quantity_control_0").classList.remove("hidden")
        document.querySelector("#button_toggle").classList.add("hidden")
    }

        
    document.getElementById("quantity_total_").value = data.new.quantity;

}
// END OF FUNCTION//////////


async function myFunc(id) {
    let gallery = document.querySelector("#ajax_gallery");
    let y = document.getElementById("productId").value;
    var token = getCookie('csrftoken');
    console.log(id, y);

    const response = await fetch('/variant-fetch/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
        },
        body: JSON.stringify({ variant_id: id, product_id: y,}),
    });
    const data = await response.json();

    if (data) {
        var elements = document.getElementsByClassName("child");
        for (var i = 0; i < elements.length; i++)
        {
            elements[i].onclick = function(){
                
                var el = elements[0];
                while(el)
                {
                    if(el.tagName === "DIV"){
                        el.classList.remove("active-swatch");
                    }
                    el = el.nextSibling;
                }

                this.classList.add("active-swatch");
            };
        }
    }

    gallery.innerHTML = '';
    gallery.innerHTML = data.thumbnail;
    productDetails();

    console.log(data);
    console.log(data.new);


    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('variantid', data.new.sku);
    window.history.replaceState(null, null, currentUrl)

    document.getElementById("selected_variant").innerHTML =  data.new.name;
    document.getElementById("price").innerHTML = "₵" + data.new.price + ".00";

    document.getElementById("quantity_total_").value = data.new.quantity;

    if (data.new.stock > 10) {
        document.getElementById("default_config").classList.add("hidden")
        inStockElement.classList.remove("hidden")
        outOfStockElement.classList.add("hidden")
        fewStockElement.classList.add("hidden")
    } else if (data.new.stock < 1) {
        document.getElementById("default_config").classList.add("hidden")
        outOfStockElement.classList.remove("hidden")
        inStockElement.classList.add("hidden")
        fewStockElement.classList.add("hidden")
    } else {
        fewStockElement.classList.remove("hidden")
        outOfStockElement.classList.add("hidden")
        inStockElement.classList.add("hidden")
        document.getElementById("default_config").classList.add("hidden")
        document.getElementById("stock_count").innerHTML = data.new.stock + " items in stock";
    }

    if (data.new.control == 1) {
        control0Element.classList.add("hidden")
        control1Element.classList.remove("hidden")
        toggleElement.classList.add("hidden")
    } else {
        toggleElement.classList.add("hidden")
        control0Element.classList.remove("hidden")
        control1Element.classList.add("hidden")
    }

    document.querySelector("#variant").value = data.new.id;
}


//PRODUCT INCREASE ON DETAIL PAGE//
async function increaseQuantity() {
    let id = document.getElementById("productId").value;
    let varid = document.getElementById("variant").value || null;

    console.log("Product id: ", id);
    console.log("Variant id: ", varid);

    const response = await fetch('/increase/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ variant_id: varid, product_id: id,}),
    });
    const data = await response.json();
    console.log(data); 
    document.getElementById("cart_count").innerHTML = data.cart_count;
    document.getElementById("totalamount").innerHTML = "₵" + data.total + ".00";
    document.querySelector(".quantity_total_").value = data.added_quantity;
    document.querySelector("#quantity_total_").value = data.added_quantity;

}
//PRODUCT INCREASE ON DETAIL PAGE//




//PRODUCT DECREASE ON DETAIL PAGE//
async function decreaseQuantity() {
    let id = document.getElementById("productId").value;
    let varid = document.getElementById("variant").value || null;
    var token = getCookie('csrftoken');

    console.log("Product id: ", id);
    console.log("Variant id: ", varid);

    const response = await fetch('/decrease/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
        },
        body: JSON.stringify({ variant_id: varid, product_id: id,}),
    });
    const data = await response.json();
    console.log(data); 
    document.getElementById("cart_count").innerHTML = data.cart_count;
    document.getElementById("totalamount").innerHTML = "₵" + data.total + ".00";
    document.querySelector(".quantity_total_").value = data.added_quantity;
    document.querySelector("#quantity_total_").value = data.added_quantity;

    if (data.added_quantity == 0) {
        toggleElement.classList.add("hidden")
        control0Element.classList.remove("hidden")
        control1Element.classList.add("hidden")
    }

}
//PRODUCT DECREASE ON DETAIL PAGE//


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
                csrfmiddlewaretoken : token,
            },
            success: function(response) {
                console.log(response);
                document.getElementById("cart_count").innerHTML = response.cart_count;
                document.querySelector(".summary_totalamount").innerHTML = "GH₵" + response.total + ".00";
                document.getElementById("totalamount").innerHTML = "₵" + response.total + ".00";

            }
        });
    });

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
                csrfmiddlewaretoken : token,
            },
            success: function(response) {
                console.log(response);
                document.getElementById("cart_count").innerHTML = response.data.cart_count;
                document.querySelector(".summary_totalamount").innerHTML = "GH₵" + response.data.total + ".00";
                document.getElementById("totalamount").innerHTML = "₵" + response.data.total + ".00";

            }
        });
    })

 
});
//QUANTITY BUTTON ADJUSTMENT

//DELETE CART ITEM FROM CART PAGE//
async function deleteCartItem(id) {
    var token = getCookie('csrftoken');
    const response = await fetch(`/deletecart/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": token,
        },
        body: JSON.stringify({ cart_id : id})
    });

    const data = await response.json();
    console.log(data);
    document.getElementById("cartdiv-" + data.id).outerHTML = "";
    document.getElementById("cart_count").innerHTML = data.cart_count;
    document.querySelector(".summary_totalamount").innerHTML = "GH₵" + data.total + ".00";
    document.getElementById("totalamount").innerHTML = "₵" + data.total + ".00";

    if (data.cart_count < 1) {
        document.getElementById("cart-items").classList.add("hidden");
        document.getElementById("empty-cart").classList.remove("hidden");
    }

}
//DELETE CART ITEM FROM CART PAGE//

$(function () {
    $(".xzoom, .xzoom-gallery").xzoom({
        zoomwidth: 400,
        tint: "#333",
        zoffset: 15,
    })
})

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

