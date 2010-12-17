$SCRIPT_ROOT = "/pysoso";


$(function()
{
	$('a#calculate').bind('click', function() {
		$.getJSON($SCRIPT_ROOT + '/_add_numbers', {
			a: $('input[name="a"]').val(),
			b: $('input[name="b"]').val()
		}, function(data) {
			$("#result").text(data.result);
		});
		return false;
	});

	$('a#edit').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$("div.bookmarks .tools").removeClass("visible");
		}
		else
		{
			$(this).addClass("active");
			$("div.bookmarks .tools").addClass("visible");
		}
	});

	$('.bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("slow");
		$.getJSON($(this).attr("href"));
	});

	$('.bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("slow");
	});
});
