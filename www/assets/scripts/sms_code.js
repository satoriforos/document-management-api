$(function() {
	$("#resend_sms").click(function(event) {
		event.preventDefault();
		window.location.reload(true);
	});

	startTimer(seconds_to_expire);
});


function startTimer(duration) {
	display = $('#code_expire_time');
	input = $("#seconds_to_expire")
	var timer = duration, minutes, seconds;
	setInterval(function () {
		minutes = parseInt(timer / 60, 10);
		seconds = parseInt(timer % 60, 10);

		//minutes = minutes < 10 ? "0" + minutes : minutes;
		seconds = seconds < 10 ? "0" + seconds : seconds;

		display.text(minutes);
		input.val(duration);

		if (--timer < 0) {
			timer = duration;
		}
	}, 1000);
}
