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



const LikeOrUnlike = async (id) => {
  const thumbs_up = 'Follow';
  const thumbs_down = 'Unfollow';
  const follows_count = document.querySelector('#followers_all')
  var user = document.getElementById('user').value
  const csrftoken = getCookie("csrftoken");

  const response = await fetch("/follow-unfollow/", {
      method: "POST",
      headers: {
          "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ user_id: user, vendor_id: id }),
  });

  const data = await response.json();
  const like_button_element = document.getElementById(`like_button_${id}`);

  const num_likes = parseInt(follows_count.innerHTML);


  if (data.liked == true) {
      console.log("Followed");
      const follows_count = document.querySelector('#followers_all')
      like_button_element.innerHTML = thumbs_down;
      follows_count.innerHTML = num_likes + 1;
  } else if (data.liked == false) {
      console.log("Unfollowed");
      const follows_count = document.querySelector('#followers_all')
      like_button_element.innerHTML = thumbs_up;
      follows_count.innerHTML = num_likes - 1;
  }
  else {
    Swal.fire({
      title: "Login",
      icon: "info",
      text: data.msg,
      showCloseButton: true,
    })
  }

  // follows_count.innerHTML = data["follows_count"]
};



console.log("Working fine");
const monthNames = ["Jan","Feb","Mar","April","May","June",
"July","Aug","Sept","Oct","Nov","Dec"
];

$("#commentForm").submit(function (e) {
    e.preventDefault();
    let dt = new Date();
    let time = dt.getDay() + " " + monthNames[dt.getUTCMonth] + ", " + dt.getFullYear();
    $.ajax({
        data: $(this).serialize(),
        method: $(this).attr("method"),
        url: $(this).attr("action"),
        dataType: "json",
        success: function(res){
            if (res.bool == true) {
                Swal.fire({
                    title: 'Review sent!',
                    text: "Review sent succesfully, wait for verification",
                    icon: 'success',
                    confirmButtonColor: '#008000',
                })
            }
            if (res.bool == true) {
                $(".hide-comment_form").hide()
                $(".add-review").hide()
                let _html = '<div class="single-comment justify-content-between d-flex mb-30">'
                    _html += '<div class="user justify-content-between d-flex">'                         
                    _html += '<div class="thumb text-center">'
                    _html += '<img src="https://simg.nicepng.com/png/small/73-730154_open-default-profile-picture-png.png" alt="" />'
                    _html += '<a href="#" class="font-heading text-brand">'+ res.context.user +'</a>'
                    _html += '</div>'
                    _html += '<div class="desc">'
                    _html += '<div class="d-flex justify-content-between mb-10">'
                    _html += '<div class="d-flex align-items-center">'
                    _html += '<span class="font-xs text-muted">'+ time +'</span>'
                    _html += '</div>'
                    for (let i = 1; i <= res.context.rating; i++){
                        _html += '<i class="fas fa-star text-warning"></i>'
                        
                    }
                    _html += '</div>'
                    _html += '<p class="mb-10">'+ res.context.review +'</p>'
                    _html += '</div>'
                    _html += '</div>'
                    _html += '</div>'
                    $(".comment-list").prepend(_html)
            }

        }
    })
})

$(document).ready(function(){
    $(".loader").hide();
    $(".filter-checkbox, #price-filter-btn").on("click", function(){
        let filter_object = {}
        let min_price = $("#max_price").attr("min")
        let max_price = $("#max_price").val()

        filter_object.min_price = min_price;
        filter_object.max_price = max_price;

        $(".filter-checkbox").each(function(index){
            let filter_value = $(this).val()
            let filter_key = $(this).data("filter")

            console.log(filter_value, filter_key);
            filter_object[filter_key] = 
            Array.from(document.querySelectorAll('input[data-filter=' + filter_key + ']:checked')).map(function(element){
                return element.value
            })
        })
        console.log(filter_object);
        $.ajax({
            url: '/filter-products',
            data: filter_object,
            dataType: 'json',

            success: function(response){
                $("#filtered-product").html(response.data)
            }
        })
    });


    $("#max_price").on("blur", function(){
        let min_price = $(this).attr("min")
        let max_price = $(this).attr("max")
        let current_price = $(this).val()

        if (current_price < parseInt(min_price)||current_price > parseInt(max_price)){
            console.log("Error occured");

            min_price = Math.round(min_price * 100) / 100
            max_price = Math.round(max_price * 100) / 100
            
           
            alert("Price must be between ₵"+ min_price + ' and ₵' + max_price)
            $(this).val(max_price)
            $('#range').val(max_price)
            $(this).focus()
            return false

        }
    });

    $(document).on("click", ".make-default-address", function(){
        let id = $(this).attr("data-address-id")
        let this_val = $(this)
        $.ajax({
            url: "/make-default-address",
            data: {
                "id":id
            },
            dataType: "json",
            success: function(response){
                console.log("Address Made Default....");
                if (response.boolean == true){

                    $(".check").hide()
                    $(".action_btn").show()

                    $(".check"+id).show()
                    $(".button"+id).hide()

                }
            }
        })
    });

    // Adding to wishlist
    $(document).on("click", ".add-to-wishlist", function(){
        let product_id = $(this).attr("data-product-item")
        let this_val = $(this)
        $.ajax({
            url: "/add-to-wishlist",
            data: {
                "id": product_id
            },
            dataType: "json",
            success: function(response){
                this_val.html("<i class='fas fa-heart text-danger'></i>")
                if (response.bool === true) {
                }
            }
        });
    });


    $(document).on("submit", "#contact-form-ajax", function(e){
        e.preventDefault()
        let full_name = $("#full_name").val()
        let email = $("#email").val()
        let phone = $("#phone").val()
        let subject = $("#subject").val()
        let message = $("#message").val()
        $.ajax({
            url: "/ajax-contact-form",
            data: {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "subject": subject,
                "message": message,
            },
            dataType:"json",
            beforeSend: function(){
                console.log("Sending Data to Server...");
            },
            success: function(res){
                console.log("Sent Data to server!");
                $(".contact_us_p").hide()
                $("#contact-form-ajax").hide()
                $("#message-response").html("Message sent successfully.")
            }
        });
    });

    $(document).on('change', '#post-form', function(e){
        e.preventDefault();
        $.ajax({
            method: $(this).attr("method"),
            type:"POST",
            url:'/ajaxcolor',
            data:{
                productid:$('#productid').val(),
                size:$('#size').val(),
                csrfmiddlewaretoken:$("input[name='csrfmiddlewaretoken']").val(),
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


    $("#id_country").change(function (e) {
        e.preventDefault();
        var url = $("#personForm").attr("data-regions-url");
        var countryId = $(this).val();

        $.ajax({
          url: url,
          data: {
            'country': countryId,
          },
          success: function (data) {
            $("#id_region").html(data);
          }
        });
  
    });
    
    $("#id_town").change(function (e) {
        e.preventDefault();
        var url = $("#location").attr("data-location-url");
        var countryId = $(this).val()||null;

        $.ajax({
          url: url,
          data: {
            'location': countryId,
          },
          success: function (data) {
            console.log(data);
            console.log(data.town);
            console.log(data.data.fee);
            // document.getElementsByClassName("location").html()
           document.querySelector('.town_name').innerHTML = data.data.town;
           document.querySelector('.town_fee').innerHTML = "GH₵" +data.data.fee+ ".00";
          }
        });
  
    });

    $("#id_region").change(function () {
        var url = $("#personForm").attr("data-regions-url");
        var regionId = $(this).val();
        $.ajax({
          url: "/address/ajax/load-towns/",
          data: {
            'region': regionId
          },
          success: function (data) {
            $("#id_town").html(data);
          }
        });
  
      });



    $("#myInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $(".myTable .hello").filter(function() {
          $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });


});

$(document).ready(function(){
    $("#myInput").on("keyup", function() {
      var value = $(this).val().toLowerCase();
      $(".myTable .hello").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
      });
    });
});


$(document).ready(function(){
    $('#my-button-1').waitableButton({
        onClick: function() {
            return fakeAjax('done', 1000);
        },
        doneClass: 'btn btn-success',
        doneText: 'Done',
        disabledOnDone: true
    });

    $('#my-button-2').waitableButton({
        onClick: function() {
            return fakeAjax('fail', 1000);
        },
        failClass: 'btn btn-danger',
        failText: 'Error! Try Again'
    });

    $('#my-button-3').waitableButton({
        onClick: function() {
            return false;
        },
    });

    $('#my-button-2').waitableButton('promise')
    .done(function() {
        console.log('done');
    })
    .fail(function() {
        console.log('fail');
    })
    .always(function() {
        console.log('always');
    });
});


  // END check amount -----------------------------------------------------------------------------
  // START add operating hours --------------------------------------------------------------------
  $('.add-hour').on('click', function (e) {
    e.preventDefault();
    var day = document.getElementById('id_day').value
    var from_hour = document.getElementById('id_from_hour').value
    var to_hour = document.getElementById('id_to_hour').value
    var is_closed = document.getElementById('id_is_closed').checked
    var csrf_token = $('input[name=csrfmiddlewaretoken]').val()
    var url = document.getElementById('add-hour-url').value
    if (is_closed) {
      is_closed = 'True'
      condition = "day != ''"
    }
    else {
      is_closed = 'False'
      condition = "day != '' && from_hour != '' && to_hour != ''"
    }
    if (eval(condition)) {
      $.ajax({
        type: "POST",
        url: url,
        data: {
          'day': day,
          'from_hour': from_hour,
          'to_hour': to_hour,
          'is_closed': is_closed,
          'csrfmiddlewaretoken': csrf_token,
        },
        success: function (response) {
          if (response.status == 'Success') {
            if (response.is_closed == 'Closed') {
              html = '<tr id="hour-' + response.id + '"><td><i class="fas fa-activity"></i></td><td><b>' + response.day + '</b></td><td><b class="text-danger">Closed</b></td><td><a href="" style="color: unset;" class="remove-hour" data-url="/account/vendor/operating-hours/remove/' + response.id + '/"><i class="fas fa-trash text-danger"></i></a></td></tr>';
            }
            else {
              html = '<tr id="hour-' + response.id + '"><td> <i class="fas fa-activity"></i></td><td><b>' + response.day + '</b></td><td>' + response.from_hour + ' - ' + response.to_hour + '</td><td><a href="" style="color: unset;" class="remove-hour" data-url="/account/vendor/operating-hours/remove/' + response.id + '/"><i class="fas fa-trash text-danger"></i></a></td></tr>';
            }
            $('.operating-hours').append(html);
            document.getElementById('operating-hours').reset();
          } 
          else {
            Swal.fire({
              position: 'center',
              icon: 'error',
              title: 'Error',
              text: response.message,
            })
          }
        }
      });
    }
    else {
      Swal.fire({
        position: 'center',
        icon: 'warning',
        title: 'Required',
        text: 'Day and Open/Close fields are required',
      })
    }
  })

  // End add operating hours ----------------------------------------------------------------------
  // START remove operating hours -----------------------------------------------------------------
  $(document).on('click', '.remove-hour', function (e) {
    e.preventDefault();
    url = $(this).attr('data-url');
    $.ajax({
      type: 'GET',
      url: url,
      success: function (response) {
        if (response.status == 'Success') {
          document.getElementById('hour-' + response.id).remove();
        }
      }
    })
  })
  

  // PRODUCT SIZE CHART MODAL
const openEls = document.querySelectorAll("[data-open]");
const closeEls = document.querySelectorAll("[data-close]");
const isVisible = "is-visible";

for (const el of openEls) {
  el.addEventListener("click", function() {
    const modalId = this.dataset.open;
    document.getElementById(modalId).classList.add(isVisible);
  });
}

for (const el of closeEls) {
  el.addEventListener("click", function() {
    this.parentElement.parentElement.parentElement.classList.remove(isVisible);
  });
}

document.addEventListener("click", e => {
  if (e.target == document.querySelector(".modal.is-visible")) {
    document.querySelector(".modal.is-visible").classList.remove(isVisible);
  }
});

document.addEventListener("keyup", e => {
  // if we press the ESC
  if (e.key == "Escape" && document.querySelector(".modal.is-visible")) {
    document.querySelector(".modal.is-visible").classList.remove(isVisible);
  }
});
  // PRODUCT SIZE CHART MODAL