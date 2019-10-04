$(function() {
	$("form#close_account_form").submit(function(event) {
		return confirm("Are you sure?")
	});
});
