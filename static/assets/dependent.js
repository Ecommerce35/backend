console.log("Working Perfectly Fine🥂🥂🥂")
$(document).ready(function(){

    $("#id_country").change(function () {
      var url = $("#personForm").attr("data-regions-url");
      var countryId = $(this).val();

      $.ajax({
        url: '{% url "address:ajax_load_regions" %}',
        data: {
          'country': countryId
        },
        success: function (data) {
        console.log(data)
          $("#id_region").html(data);
        }
      });

    });

    $("#id_region").change(function () {
      var url = $("#personForm").attr("data-regions-url");
      var regionId = $(this).val();

      $.ajax({
        url: '{% url "address:ajax_load_towns" %}',
        data: {
          'region': regionId
        },
        success: function (data) {
        console.log(data)
          $("#id_town").html(data);
        }
      });

    });
});