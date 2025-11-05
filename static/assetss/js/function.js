
console.log("Function js waiiii");
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

$(document).ready(function(){
    
    $("#id_country").change(function (e) {
        e.preventDefault();
        var url = $("#personForm").attr("data-regions-url");
        var countryId = $(this).val();
        console.log(countryId);

        $.ajax({
          url: url,
          data: {
            'country': countryId,
          },
          success: function (data) {
            console.log(data);
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
           document.getElementById('town_name').innerHTML = data.data.town;
           document.getElementById('town_fee').innerHTML = "GH₵" +data.data.fee+ ".00";
          }
        });
  
    });

    $("#id_region").change(function () {
        var url = $("#personForm").attr("data-regions-url");
        var regionId = $(this).val();
        $.ajax({
          url: "/ajax/load-towns/",
          data: {
            'region': regionId
          },
          success: function (data) {
            $("#id_town").html(data);
          }
        });
  
      });
   
});

