
$(function() {
	$.ajaxSetup({
	  headers : {
	    'Authorization' : 'Digest NTEyZjZjOTA1ZjBhNDYwNjFjNzgwNWViYWE2MmZiNzA='
	  }
	});
	$("#try_api").submit(function(event) {
		submitApiHandler($(this), event);
	});
	$("#function_name").change(function(event) {
		function_name = $(this).find(":selected").val();
		// toggle which items are shown and hidden
		switch(function_name) {
			case "company_domain":
				$("#name_container").hide()
				$("#domain_container").hide()
				$("#company_container").show()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#try_it_webhook_required").show()
				$("#documentation_company_domain").show();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_race").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", false);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", true);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "jobtitle":
				$("#name_container").hide();
				$("#domain_container").hide();
				$("#company_container").hide();
				$("#phone_container").hide();
				$("#zip_container").hide();
				$("#title_container").show();
				$("#submit_button_container").show();
				$("#try_it_webhook_required").hide();
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").show();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_race").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", false);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", true);
			break;
			case "person_age":
				$("#name_container").show()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").show();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_person_race").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", true);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "person_emailaddress":
				$("#name_container").show()
				$("#domain_container").show()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").show()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").show();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_person_race").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", true);
				$("input#domain").attr("required", true);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "person_ethnicity":
				$("#name_container").show()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").show();
				$("#documentation_person_gender").hide();
				$("#documentation_person_race").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", true);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "person_gender":
				$("#name_container").show()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_gender").show();
				$("#documentation_person_race").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", true);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "person_race":
				$("#name_container").show()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_race").show();
				$("#documentation_person_gender").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").hide();
				$("input#name").attr("required", true);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "phone_locations":
				$("#name_container").hide()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").show()
				$("#zip_container").hide()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_race").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_phone_locations").show();
				$("#documentation_zip").hide();
				$("input#name").attr("required", false);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", true);
				$("input#zip").attr("required", false);
				$("input#title").attr("required", false);
			break;
			case "zip":
				$("#name_container").hide()
				$("#domain_container").hide()
				$("#company_container").hide()
				$("#phone_container").hide()
				$("#zip_container").show()
				$("#title_container").hide()
				$("#submit_button_container").show()
				$("#try_it_webhook_required").hide()
				$("#documentation_company_domain").hide();
				$("#documentation_jobtitle").hide();
				$("#documentation_person_age").hide();
				$("#documentation_person_emailaddress").hide();
				$("#documentation_person_ethnicity").hide();
				$("#documentation_person_race").hide();
				$("#documentation_person_gender").hide();
				$("#documentation_phone_locations").hide();
				$("#documentation_zip").show();
				$("input#name").attr("required", false);
				$("input#domain").attr("required", false);
				$("input#company").attr("required", false);
				$("input#phone").attr("required", false);
				$("input#zip").attr("required", true);
				$("input#title").attr("required", false);
			break;
			default:
		}




	});

});



function submitApiHandler(form, event) {
	$("#try_api_submit").prop("disabled", true);
	event.preventDefault();
	function_name = form.find("#function_name").find(":selected").val();

	$("#try_it_form_error").hide()

	url = "https://api.fromdatawithlove.com/v1/"
	params = {}
	switch(function_name) {
		case "company_domain":
			url += "company/domain";
			company_name = form.find("#company").val();
			params = {"name": company_name};
		break;
		case "jobtitle":
			url += "jobtitle/";
			job_title = form.find("#title").val();
			params = {"title": job_title};
		break;
		case "person_age":
			url += "person/age";
			name = form.find("#name").val();
			params = {"name": name};
		break;
		case "person_emailaddress":
			url += "person/emailaddress";
			name = form.find("#name").val();
			domain = form.find("#domain").val();
			params = {"name": name, "domain": domain};
		break;
		case "person_ethnicity":
			url += "person/ethnicity";
			name = form.find("#name").val();
			params = {"name": name};
		break;
		case "person_gender":
			url += "person/gender";
			name = form.find("#name").val();
			params = {"name": name};
		break;
		case "person_race":
			url += "person/race";
			name = form.find("#name").val();
			params = {"name": name};
		break;
		case "phone_locations":
			url += "phone/locations";
			phone = form.find("#phone").val();
			params = {"phone": phone};
		break;
		case "zip":
			url += "location/zipcode/";
			zip = form.find("#zip").val();
			params = {"zip": zip};
		break;
		default:
	}

	$.getJSON(url, params )
	.done(function( json ) {
		pretty_json = JSON.stringify(json, null, 4);
		$("#json_output").html(pretty_json);
		$(".output").show();
		console.log(json)
		//console.log( "JSON Data: " + json );
		$("#try_api_submit").prop("disabled", false);
	})
	.fail(function( jqxhr, textStatus, error ) {
		$(".output").hide();
		var err = textStatus + ", " + error;
		console.log( "Request Failed: " + err );
		$("#try_api_submit").prop("disabled", false);
		$("#try_it_form_error").show()
	});
}


