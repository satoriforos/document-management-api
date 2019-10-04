var stripe = Stripe('pk_live_zuICqvSiwnCUf6HiI4XF3RMp');
//var stripe = Stripe('pk_test_JDtaS674DQiTI3FCMKAtm2tM');
var card = null;

$(function() {
	attachStripeElements()
	$("input[type=radio][name=billing_id]").change(function(event) {
		payment_block = $("#payment_block");
		if (this.value == "free") {
			payment_block.hide();
			detachStripeHandler()
		} else {
			payment_block.show();
			attachStripeHandler()
		}
	});
	plan_name = get_query_parameter("plan");
	if (plan_name != null) {
		$("input[type=radio][value=" + plan_name + "]").prop('checked', true);
		$("input[type=radio][value=" + plan_name + "]").change();
	}
	selectable_plans = $("input[type=radio][name=billing_id]");
	selectable_plans.each(function(item) {
		selectable_plan = $(selectable_plans[item]);
		if (selectable_plan.prop("checked") == true) {
			selectable_plan.change()
		}
	});
	discount_code = get_query_parameter("discount_code");
	if (discount_code != null) {
		$("#discount_code").val(discount_code);
	}
	
	grecaptcha.ready(function() {
		grecaptcha.execute(
			'6LfvOIUUAAAAAMmg7Ww2zBlxb0S0gbwVPe8Z_xjT',
			{action: 'register'}
		)
		.then(function(token) {
			// Verify the token on the server.
		});
	});
});


function attachStripeHandler() {
	// Handle form submission.
	var form = document.getElementById('stripe_form');
	form.addEventListener('submit', stripeSubmitHandler);
}

function detachStripeHandler() {
	var form = document.getElementById('stripe_form');
	form.removeEventListener('submit', stripeSubmitHandler);
}

function attachStripeElements() {
	var elements = stripe.elements();

	// Custom styling can be passed to options when creating an Element.
	// (Note that this demo uses a wider set of styles than the guide below.)
	var style = {
	  base: {
		color: '#32325d',
		lineHeight: '18px',
		fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
		fontSmoothing: 'antialiased',
		fontSize: '16px',
		'::placeholder': {
		  color: '#aab7c4'
		}
	  },
	  invalid: {
		color: '#fa755a',
		iconColor: '#fa755a'
	  }
	};

	// Create an instance of the card Element.
	card = elements.create('card', {style: style});

	// Add an instance of the card Element into the `card-element` <div>.
	card.mount('#card-element');

	// Handle real-time validation errors from the card Element.
	card.addEventListener('change', function(event) {
	  var displayError = document.getElementById('card-errors');
	  if (event.error) {
		displayError.textContent = event.error.message;
	  } else {
		displayError.textContent = '';
	  }
	});
}


// Submit the form with the token ID.
function stripeTokenHandler(token) {
  // Insert the token ID into the form so it gets submitted to the server
  var form = document.getElementById('stripe_form');
  var hiddenInput = document.createElement('input');
  hiddenInput.setAttribute('type', 'hidden');
  hiddenInput.setAttribute('name', 'stripe_token');
  hiddenInput.setAttribute('value', token.id);
  form.appendChild(hiddenInput);

  // Submit the form
  form.submit();
}

function stripeSubmitHandler(event) {
	event.preventDefault();

	stripe.createToken(card).then(function(result) {
		if (result.error) {
			// Inform the user if there was an error.
			var errorElement = document.getElementById('card-errors');
			errorElement.textContent = result.error.message;
		} else {
			// Send the token to your server.
			stripeTokenHandler(result.token);
		}
	});
}


function get_query_parameter(key) {
	key = key.replace(/[*+?^$.\[\]{}()|\\\/]/g, "\\$&"); // escape RegEx meta chars
	var match = location.search.match(new RegExp("[?&]"+key+"=([^&]+)(&|$)"));
	return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}
